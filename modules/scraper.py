"""
Smart Product Finder - Módulo de Coleta (Scraper)
Coleta produtos do AliExpress com suporte a modo demo.

MODO DEMO: Ativo por padrão quando SCRAPER_MODE=demo ou sem configuração.
MODO REAL: Ativo quando SCRAPER_MODE=real e playwright instalado.
"""

import os
import json
import uuid
import random
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Callable


# Caminho dos dados de demo
DEMO_FILE = Path(__file__).parent.parent / "data" / "demo_products.json"

# Modo de operação do scraper
SCRAPER_MODE = os.getenv("SCRAPER_MODE", "demo")


def collect_products(
    keyword: str,
    category: str = "",
    min_price: float = 0,
    max_price: float = 999,
    min_rating: float = 0,
    min_sales: int = 0,
    ships_from_brazil: Optional[bool] = None,
    choice_badge: Optional[bool] = None,
    max_results: int = 20,
    progress_callback: Optional[Callable] = None
) -> List[dict]:
    """
    Ponto de entrada principal para coleta de produtos.
    
    Decide automaticamente entre modo demo e scraping real
    baseado na variável de ambiente SCRAPER_MODE.
    
    Args:
        keyword: Palavra-chave de busca
        category: Categoria do produto
        min_price/max_price: Faixa de preço
        min_rating: Avaliação mínima
        min_sales: Vendas mínimas
        ships_from_brazil: Filtro de origem
        choice_badge: Filtro de selo
        max_results: Máximo de produtos a retornar
        progress_callback: Função chamada com % progresso (0-100)
    
    Returns:
        Lista de dicionários com dados dos produtos
    """
    if SCRAPER_MODE == "real":
        return _collect_real(
            keyword, category, min_price, max_price,
            min_rating, min_sales, ships_from_brazil,
            choice_badge, max_results, progress_callback
        )
    else:
        return _collect_demo(
            keyword, category, min_price, max_price,
            min_rating, min_sales, ships_from_brazil,
            choice_badge, max_results, progress_callback
        )


def _collect_demo(
    keyword: str,
    category: str,
    min_price: float,
    max_price: float,
    min_rating: float,
    min_sales: int,
    ships_from_brazil: Optional[bool],
    choice_badge: Optional[bool],
    max_results: int,
    progress_callback: Optional[Callable]
) -> List[dict]:
    """
    Modo demo: carrega produtos do arquivo JSON e simula busca realista.
    Filtra produtos baseado nos parâmetros fornecidos.
    Simula latência de rede para UX realista.
    """
    if not DEMO_FILE.exists():
        return []

    with open(DEMO_FILE, "r", encoding="utf-8") as f:
        all_products = json.load(f)

    # Simula progresso de coleta
    if progress_callback:
        for i in range(0, 60, 10):
            progress_callback(i)
            time.sleep(0.1)

    # Filtra produtos baseado nos critérios
    filtered = []
    for p in all_products:
        if p.get("price", 0) < min_price:
            continue
        if max_price > 0 and p.get("price", 0) > max_price:
            continue
        if p.get("rating", 0) < min_rating:
            continue
        if p.get("sales", 0) < min_sales:
            continue
        if ships_from_brazil is True and not p.get("ships_from_brazil"):
            continue
        if choice_badge is True and not p.get("choice_badge"):
            continue
        filtered.append(p)

    # Simula variação: produtos extras baseados na keyword
    extra_products = _generate_extra_products(keyword, category, max(0, max_results - len(filtered)))
    combined = (filtered + extra_products)[:max_results]

    # Simula conclusão da coleta
    if progress_callback:
        for i in range(60, 101, 10):
            progress_callback(i)
            time.sleep(0.05)

    return combined


def _generate_extra_products(keyword: str, category: str, count: int) -> List[dict]:
    """
    Gera produtos adicionais simulados baseados na keyword.
    Cria variações realistas para enriquecer a demonstração.
    """
    if count <= 0:
        return []

    categories = ["Casa e Decoração", "Eletrônicos", "Moda", "Esporte", "Saúde e Beleza",
                  "Organização", "Papelaria", "Pets", "Acessórios", "Informática"]

    extras = []
    for i in range(count):
        price = round(random.uniform(5, 80), 2)
        sales = random.randint(50, 35000)
        rating = round(random.uniform(3.8, 5.0), 1)

        extras.append({
            "id": f"sim_{uuid.uuid4().hex[:8]}",
            "name": f"{keyword.title()} {_random_adjective()} {_random_suffix()}",
            "link": f"https://www.aliexpress.com/item/sim{i:04d}",
            "price": price,
            "rating": rating,
            "sales": sales,
            "delivery_days": random.randint(8, 25),
            "ships_from_brazil": random.random() > 0.7,
            "choice_badge": random.random() > 0.5,
            "image_url": f"https://via.placeholder.com/300x300/{_random_color()}/FFFFFF?text={keyword[:8].replace(' ', '+')}",
            "category": category or random.choice(categories),
            "collected_at": datetime.now().isoformat()
        })

    return extras


def _random_adjective() -> str:
    adjectives = ["Premium", "Ultra", "Pro", "Smart", "Slim", "Mini", "Turbo", "Plus", "Max", "Elite"]
    return random.choice(adjectives)


def _random_suffix() -> str:
    suffixes = ["2024", "v2", "Kit", "Set", "Pack", "Original", "Importado", "Top"]
    return random.choice(suffixes)


def _random_color() -> str:
    colors = ["FF6B35", "2ECC71", "3498DB", "9B59B6", "E74C3C", "F39C12", "1ABC9C", "E67E22"]
    return random.choice(colors)


def _collect_real(
    keyword: str,
    category: str,
    min_price: float,
    max_price: float,
    min_rating: float,
    min_sales: int,
    ships_from_brazil: Optional[bool],
    choice_badge: Optional[bool],
    max_results: int,
    progress_callback: Optional[Callable]
) -> List[dict]:
    """
    Modo REAL: Usa Playwright para scraping do AliExpress.
    
    ATENÇÃO: Esta implementação é estrutural e serve como base.
    O AliExpress usa anti-bot agressivo. Para produção, considere:
    - Usar proxies rotativos
    - Adicionar delays aleatórios entre requests
    - Usar perfis de navegador pré-aquecidos
    - Considerar a API oficial do AliExpress (AliExpress Open Platform)
    
    Para habilitar: export SCRAPER_MODE=real
    """
    try:
        from playwright.sync_api import sync_playwright

        products = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()

            # Constrói URL de busca AliExpress
            search_url = _build_aliexpress_url(keyword, min_price, max_price)

            if progress_callback:
                progress_callback(10)

            page.goto(search_url, timeout=30000)
            page.wait_for_timeout(3000)

            if progress_callback:
                progress_callback(30)

            # Extrai produtos da página
            raw_items = page.evaluate(_get_extraction_script())

            if progress_callback:
                progress_callback(70)

            for i, item in enumerate(raw_items[:max_results]):
                try:
                    product = _parse_aliexpress_item(item, keyword, category)
                    if product and _passes_filters(product, min_rating, min_sales, ships_from_brazil, choice_badge):
                        products.append(product)
                except Exception:
                    continue

            browser.close()

            if progress_callback:
                progress_callback(100)

        return products

    except ImportError:
        # Playwright não instalado — fallback para demo
        print("⚠️ Playwright não instalado. Usando modo demo. Execute: pip install playwright && playwright install chromium")
        return _collect_demo(
            keyword, category, min_price, max_price,
            min_rating, min_sales, ships_from_brazil,
            choice_badge, max_results, progress_callback
        )
    except Exception as e:
        print(f"❌ Erro no scraping real: {e}. Usando modo demo.")
        return _collect_demo(
            keyword, category, min_price, max_price,
            min_rating, min_sales, ships_from_brazil,
            choice_badge, max_results, progress_callback
        )


def _build_aliexpress_url(keyword: str, min_price: float, max_price: float) -> str:
    """Constrói a URL de busca do AliExpress com parâmetros."""
    import urllib.parse
    base = "https://www.aliexpress.com/wholesale"
    params = {
        "SearchText": keyword,
        "sortType": "total_tranpro_desc",  # Ordenar por mais vendidos
    }
    if min_price > 0:
        params["minPrice"] = int(min_price)
    if max_price > 0:
        params["maxPrice"] = int(max_price)

    return f"{base}?{urllib.parse.urlencode(params)}"


def _get_extraction_script() -> str:
    """Script JavaScript para extrair dados dos produtos da página AliExpress."""
    return """
    () => {
        const items = [];
        const productCards = document.querySelectorAll('[class*="manhattan--container"]');
        
        productCards.forEach(card => {
            try {
                const title = card.querySelector('[class*="multi--titleText"]')?.textContent?.trim();
                const priceEl = card.querySelector('[class*="multi--price-sale"]');
                const price = parseFloat(priceEl?.textContent?.replace(/[^0-9.]/g, '') || '0');
                const link = card.querySelector('a')?.href;
                const image = card.querySelector('img')?.src;
                const starsEl = card.querySelector('[class*="multi--evaluation"]');
                const salesEl = card.querySelector('[class*="multi--trade"]');
                
                if (title && link) {
                    items.push({ title, price, link, image,
                        stars: starsEl?.textContent?.trim() || '',
                        sales: salesEl?.textContent?.trim() || ''
                    });
                }
            } catch(e) {}
        });
        
        return items;
    }
    """


def _parse_aliexpress_item(item: dict, keyword: str, category: str) -> Optional[dict]:
    """Converte item bruto do JavaScript para estrutura padrão."""
    try:
        sales_text = item.get("sales", "0").replace(",", "").replace("+", "")
        sales_num = int("".join(filter(str.isdigit, sales_text)) or "0")

        rating_text = item.get("stars", "0")
        try:
            rating = float(rating_text[:3])
        except (ValueError, IndexError):
            rating = 0.0

        return {
            "id": f"ali_{uuid.uuid4().hex[:12]}",
            "name": item.get("title", "Produto sem nome")[:200],
            "link": item.get("link", ""),
            "price": float(item.get("price", 0)),
            "rating": rating,
            "sales": sales_num,
            "delivery_days": 15,
            "ships_from_brazil": False,
            "choice_badge": False,
            "image_url": item.get("image", ""),
            "category": category or "Geral",
            "collected_at": datetime.now().isoformat()
        }
    except Exception:
        return None


def _passes_filters(product: dict, min_rating: float, min_sales: int,
                    ships_from_brazil: Optional[bool], choice_badge: Optional[bool]) -> bool:
    """Verifica se o produto passa pelos filtros do usuário."""
    if product.get("rating", 0) < min_rating:
        return False
    if product.get("sales", 0) < min_sales:
        return False
    if ships_from_brazil is True and not product.get("ships_from_brazil"):
        return False
    if choice_badge is True and not product.get("choice_badge"):
        return False
    return True


def get_scraper_status() -> dict:
    """Retorna status atual do scraper."""
    return {
        "mode": SCRAPER_MODE,
        "active": SCRAPER_MODE == "real",
        "message": (
            "🔴 Modo Real ativo — scraping AliExpress" if SCRAPER_MODE == "real"
            else "🟡 Modo Demo — dados simulados realistas"
        )
    }
