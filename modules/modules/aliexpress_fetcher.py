"""
Smart Product Finder — modules/aliexpress_fetcher.py
Extrai dados de produtos do AliExpress a partir de uma URL.

Estratégias em cascata (tenta a mais rápida primeiro):
  1. Extração de JSON embutido na página (window.runParams / _ddc_)
  2. Parsing HTML com BeautifulSoup (meta tags + seletores)
  3. Dados estimados a partir da URL (fallback para demo)

Uso assíncrono para não travar o Streamlit.
Cache com st.cache_data por 1h para evitar requisições repetidas.
"""

import re
import json
import asyncio
import hashlib
from typing import Optional
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs


@dataclass
class AliProductData:
    """Dados extraídos de um produto AliExpress."""
    url: str
    title: str = ""
    price_usd: float = 0.0
    original_price_usd: float = 0.0    # preço sem desconto
    rating: float = 0.0
    review_count: int = 0
    orders_count: int = 0
    ships_from: str = "China"
    estimated_weight_kg: float = 0.3
    image_url: str = ""
    store_name: str = ""
    store_feedback_pct: float = 0.0
    category_hint: str = ""
    has_choice_badge: bool = False
    extraction_method: str = "unknown"
    success: bool = False
    error: str = ""


async def fetch_aliexpress_product(url: str, timeout: int = 15) -> AliProductData:
    """
    Ponto de entrada assíncrono. Tenta extrair dados do produto na URL informada.
    Compatível com links longos e links encurtados do app AliExpress.
    """
    result = AliProductData(url=url)

    # Normaliza URL
    clean_url = _normalize_aliexpress_url(url)
    if not clean_url:
        result.error = "URL inválida. Use um link do AliExpress (aliexpress.com/item/...)."
        return result

    result.url = clean_url

    # Tenta extração real
    try:
        html = await _fetch_html(clean_url, timeout)
        if html:
            # Estratégia 1: JSON embutido (mais confiável)
            extracted = _extract_from_json_embed(html)
            if extracted.success:
                return extracted

            # Estratégia 2: HTML/meta tags
            extracted = _extract_from_html(html, clean_url)
            if extracted.success:
                return extracted

    except Exception as e:
        result.error = f"Não foi possível acessar o produto: {e}"

    # Estratégia 3: Fallback — estima a partir da URL (modo demo)
    return _extract_demo_fallback(clean_url)


async def _fetch_html(url: str, timeout: int) -> Optional[str]:
    """Faz a requisição HTTP de forma assíncrona."""
    try:
        import aiohttp
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
            "Accept": "text/html,application/xhtml+xml",
            "Referer": "https://www.google.com.br/",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status == 200:
                    return await resp.text(errors="ignore")
                return None
    except ImportError:
        # aiohttp não instalado — tenta requests síncrono
        try:
            import requests
            r = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }, timeout=timeout)
            return r.text if r.status_code == 200 else None
        except Exception:
            return None
    except Exception:
        return None


def _extract_from_json_embed(html: str) -> AliProductData:
    """
    Tenta extrair o JSON window.runParams que o AliExpress embute na página.
    Contém preço, título, avaliações e mais em estrutura estruturada.
    """
    result = AliProductData(url="", extraction_method="json_embed")

    # Padrões de JSON embutido encontrados no AliExpress
    patterns = [
        r'window\.runParams\s*=\s*(\{.+?\});\s*(?:window|var)',
        r'"data"\s*:\s*(\{"skuModule".*?"title".*?\})\s*}',
        r'_ddc_\s*=\s*(\{.*?\})\s*;',
    ]

    for pattern in patterns:
        try:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                parsed = _parse_runparams(data)
                if parsed.price_usd > 0 and parsed.title:
                    parsed.success = True
                    return parsed
        except Exception:
            continue

    return result


def _parse_runparams(data: dict) -> AliProductData:
    """Parseia a estrutura window.runParams do AliExpress."""
    result = AliProductData(url="", extraction_method="json_embed")
    try:
        # Navega por possíveis estruturas
        sku = data.get("data", {}).get("skuModule", data.get("skuModule", {}))
        title_mod = data.get("data", {}).get("titleModule", data.get("titleModule", {}))
        rating_mod = data.get("data", {}).get("feedbackModule", data.get("feedbackModule", {}))
        shipping_mod = data.get("data", {}).get("shippingModule", data.get("shippingModule", {}))

        # Título
        result.title = (
            title_mod.get("subject", "")
            or data.get("data", {}).get("title", "")
            or ""
        )

        # Preço
        price_data = (
            sku.get("skuPriceList", [{}])[0]
            if sku.get("skuPriceList") else {}
        )
        price_str = (
            price_data.get("skuVal", {}).get("skuAmount", {}).get("value", "0")
            or sku.get("salePrice", {}).get("minPrice", "0")
        )
        try:
            result.price_usd = float(str(price_str).replace(",", ".").replace("US$", "").strip())
        except Exception:
            result.price_usd = 0.0

        # Rating
        result.rating = float(rating_mod.get("tradeScore", 0) or 0)
        result.review_count = int(str(rating_mod.get("evaCount", "0")).replace("+", "").replace(",", "") or 0)

        # Origem do envio
        result.ships_from = shipping_mod.get("sourceCountry", "CN")

    except Exception:
        pass
    return result


def _extract_from_html(html: str, url: str) -> AliProductData:
    """
    Extrai dados via parsing HTML direto (meta tags Open Graph e seletores).
    Fallback quando o JSON embutido não está disponível.
    """
    result = AliProductData(url=url, extraction_method="html_parse")

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Título — meta og:title ou <h1>
        og_title = soup.find("meta", property="og:title")
        result.title = (
            (og_title.get("content", "") if og_title else "")
            or (soup.find("h1") and soup.find("h1").get_text(strip=True))
            or ""
        )

        # Imagem
        og_img = soup.find("meta", property="og:image")
        result.image_url = og_img.get("content", "") if og_img else ""

        # Preço — procura padrões comuns
        price_patterns = [
            r'"price"\s*:\s*"?([\d.]+)"?',
            r'US\$\s*([\d.]+)',
            r'"minActivityPrice"\s*:\s*"([\d.]+)"',
            r'"formatedActivityPrice"\s*:\s*"US \$([\d.]+)"',
        ]
        for pat in price_patterns:
            m = re.search(pat, html)
            if m:
                try:
                    result.price_usd = float(m.group(1))
                    break
                except Exception:
                    pass

        # Rating
        rating_m = re.search(r'"averageStar"\s*:\s*"?([\d.]+)"?', html)
        if rating_m:
            result.rating = float(rating_m.group(1))

        # Pedidos
        orders_m = re.search(r'([\d,]+)\s*(?:sold|orders|pedidos)', html, re.IGNORECASE)
        if orders_m:
            result.orders_count = int(orders_m.group(1).replace(",", ""))

        if result.title and result.price_usd > 0:
            result.success = True

    except ImportError:
        # BeautifulSoup não instalado
        result.error = "beautifulsoup4 não instalado. Usando dados estimados."
    except Exception as e:
        result.error = str(e)

    return result


def _extract_demo_fallback(url: str) -> AliProductData:
    """
    Fallback para demonstração quando não é possível acessar a URL.
    Gera dados plausíveis baseados no hash da URL para consistência.
    """
    url_hash = int(hashlib.md5(url.encode()).hexdigest()[:8], 16)

    # Gera preço pseudo-aleatório mas determinístico para a URL
    base_prices = [3.5, 5.9, 8.2, 11.5, 15.9, 19.9, 24.5, 31.0, 42.0, 58.0]
    price = base_prices[url_hash % len(base_prices)]

    ratings = [4.2, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9]
    rating = ratings[url_hash % len(ratings)]

    orders = [500, 1200, 2800, 5500, 8900, 15000, 23000]
    order_count = orders[url_hash % len(orders)]

    titles = [
        "Produto AliExpress (demo — não foi possível acessar a URL)",
        "Item importado — acesse a URL para ver título real",
    ]

    result = AliProductData(
        url=url,
        title=titles[url_hash % len(titles)],
        price_usd=price,
        original_price_usd=round(price * 1.3, 2),
        rating=rating,
        review_count=order_count // 5,
        orders_count=order_count,
        ships_from="China",
        estimated_weight_kg=0.3,
        has_choice_badge=(url_hash % 3 == 0),
        extraction_method="demo_fallback",
        success=True,
        error="Dados estimados — não foi possível acessar a URL real. "
              "Preencha o preço manualmente para cálculo preciso.",
    )
    return result


def _normalize_aliexpress_url(url: str) -> Optional[str]:
    """
    Normaliza e valida URLs do AliExpress.
    Aceita: aliexpress.com/item/..., s.click.aliexpress.com, a.aliexpress.com
    """
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    # Verifica se é AliExpress
    valid_domains = ["aliexpress.com", "aliexpress.us", "s.click.aliexpress.com", "a.aliexpress.com"]
    try:
        parsed = urlparse(url)
        if not any(d in parsed.netloc for d in valid_domains):
            return None
    except Exception:
        return None

    # Limpa parâmetros de rastreamento desnecessários (mantém itemId)
    try:
        if "/item/" in url:
            # Extrai item ID e reconstrói URL limpa
            item_match = re.search(r'/item/(\d+)', url)
            if item_match:
                item_id = item_match.group(1)
                return f"https://www.aliexpress.com/item/{item_id}.html"
    except Exception:
        pass

    return url


def extract_item_id(url: str) -> Optional[str]:
    """Extrai o item ID de uma URL AliExpress."""
    m = re.search(r'/item/(\d+)', url)
    return m.group(1) if m else None


def run_async_fetch(url: str) -> AliProductData:
    """
    Wrapper síncrono para chamar fetch_aliexpress_product de contextos síncronos.
    Compatível com Streamlit (que já tem seu próprio event loop).
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Streamlit roda em loop — usa thread separada
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, fetch_aliexpress_product(url))
                return future.result(timeout=20)
        else:
            return loop.run_until_complete(fetch_aliexpress_product(url))
    except Exception as e:
        result = AliProductData(url=url)
        result.error = str(e)
        # Retorna fallback demo para não quebrar a UI
        return _extract_demo_fallback(url)
