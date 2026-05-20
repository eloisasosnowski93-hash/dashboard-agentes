"""
Smart Product Finder - Módulo de Scoring
Algoritmo de pontuação comercial de 0 a 100 para produtos de dropshipping.

Cadu (Analista de Mercado & SEO) definiu os critérios de score
com base em padrões de "Demanda Reprimida" no marketplace Shopee.
"""

import json
from typing import Tuple


# Pesos de cada critério (soma = 100)
SCORE_WEIGHTS = {
    "price_margin":     25,  # Margem estimada sobre o preço de venda
    "rating":           20,  # Avaliação do produto
    "sales_volume":     20,  # Quantidade de vendas (prova social)
    "shipping":         10,  # Envia do Brasil (entrega rápida = vantagem)
    "choice_badge":      8,  # Selo Choice AliExpress (confiabilidade)
    "competition":      10,  # Concorrência percebida (menos = melhor)
    "visual_potential":  4,  # Estimativa de potencial visual
    "saturation_risk":   3,  # Risco de saturação de mercado
}


def calculate_score(product: dict, search_params: dict) -> Tuple[float, dict]:
    """
    Calcula o score comercial de 0 a 100 para um produto.
    
    Args:
        product: Dados do produto coletado
        search_params: Parâmetros da busca (preços, margem desejada, concorrência)
    
    Returns:
        (score_total, score_breakdown) onde score_breakdown explica cada critério
    """
    breakdown = {}
    total_score = 0.0

    # ── 1. MARGEM DE PREÇO (25 pontos) ──────────────────────────────────────
    price_score, price_detail = _score_price_margin(product, search_params)
    breakdown["price_margin"] = {"score": price_score, "max": 25, "detail": price_detail}
    total_score += price_score

    # ── 2. AVALIAÇÃO (20 pontos) ─────────────────────────────────────────────
    rating_score, rating_detail = _score_rating(product.get("rating", 0))
    breakdown["rating"] = {"score": rating_score, "max": 20, "detail": rating_detail}
    total_score += rating_score

    # ── 3. VOLUME DE VENDAS (20 pontos) ──────────────────────────────────────
    sales_score, sales_detail = _score_sales(product.get("sales", 0))
    breakdown["sales_volume"] = {"score": sales_score, "max": 20, "detail": sales_detail}
    total_score += sales_score

    # ── 4. ENVIO DO BRASIL (10 pontos) ───────────────────────────────────────
    shipping_score, shipping_detail = _score_shipping(
        product.get("ships_from_brazil", False),
        product.get("delivery_days", 30)
    )
    breakdown["shipping"] = {"score": shipping_score, "max": 10, "detail": shipping_detail}
    total_score += shipping_score

    # ── 5. SELO CHOICE (8 pontos) ─────────────────────────────────────────────
    choice_score = 8 if product.get("choice_badge") else 0
    breakdown["choice_badge"] = {
        "score": choice_score,
        "max": 8,
        "detail": "Possui Selo Choice ✓" if choice_score else "Sem Selo Choice"
    }
    total_score += choice_score

    # ── 6. CONCORRÊNCIA (10 pontos) ──────────────────────────────────────────
    competition_score, competition_detail = _score_competition(
        search_params.get("competition", "média")
    )
    breakdown["competition"] = {"score": competition_score, "max": 10, "detail": competition_detail}
    total_score += competition_score

    # ── 7. POTENCIAL VISUAL (4 pontos) ───────────────────────────────────────
    visual_score, visual_detail = _score_visual_potential(product)
    breakdown["visual_potential"] = {"score": visual_score, "max": 4, "detail": visual_detail}
    total_score += visual_score

    # ── 8. RISCO DE SATURAÇÃO (3 pontos) ─────────────────────────────────────
    saturation_score, saturation_detail = _score_saturation_risk(product)
    breakdown["saturation_risk"] = {"score": saturation_score, "max": 3, "detail": saturation_detail}
    total_score += saturation_score

    final_score = round(min(total_score, 100), 1)
    return final_score, breakdown


def _score_price_margin(product: dict, search_params: dict) -> Tuple[float, str]:
    """
    Calcula pontuação baseada na margem estimada.
    Fórmula: margem = ((preço_venda - preço_custo - frete) / preço_venda) * 100
    """
    cost = product.get("price", 0)
    freight = search_params.get("freight_cost", 15)
    target_price = search_params.get("target_price", 0)
    min_margin = search_params.get("min_margin", 30)

    if target_price <= 0 or cost <= 0:
        # Sem dados suficientes: usa heurística baseada no custo
        if cost < 15:
            return 20, f"Produto de baixo custo (R$ {cost:.2f}) — bom potencial de margem"
        elif cost < 30:
            return 15, f"Custo moderado (R$ {cost:.2f})"
        else:
            return 8, f"Custo elevado (R$ {cost:.2f}) — margem pode ser apertada"

    margin = ((target_price - cost - freight) / target_price) * 100

    if margin >= 60:
        score = 25
        label = f"Margem excelente: {margin:.1f}%"
    elif margin >= 45:
        score = 20
        label = f"Margem boa: {margin:.1f}%"
    elif margin >= 30:
        score = 14
        label = f"Margem aceitável: {margin:.1f}%"
    elif margin >= 15:
        score = 7
        label = f"Margem baixa: {margin:.1f}%"
    else:
        score = 2
        label = f"Margem insuficiente: {margin:.1f}%"

    return score, label


def _score_rating(rating: float) -> Tuple[float, str]:
    """Pontua baseado na avaliação do produto (0-5 estrelas)."""
    if rating >= 4.8:
        return 20, f"Avaliação excepcional: {rating}⭐"
    elif rating >= 4.5:
        return 16, f"Avaliação muito boa: {rating}⭐"
    elif rating >= 4.0:
        return 12, f"Avaliação boa: {rating}⭐"
    elif rating >= 3.5:
        return 7, f"Avaliação regular: {rating}⭐"
    elif rating > 0:
        return 3, f"Avaliação baixa: {rating}⭐"
    else:
        return 0, "Sem avaliações"


def _score_sales(sales: int) -> Tuple[float, str]:
    """
    Pontua por volume de vendas.
    Muitas vendas = produto validado pelo mercado.
    """
    if sales >= 20000:
        return 20, f"Volume altíssimo: {sales:,} vendas — produto validado"
    elif sales >= 10000:
        return 17, f"Volume muito alto: {sales:,} vendas"
    elif sales >= 5000:
        return 14, f"Volume alto: {sales:,} vendas"
    elif sales >= 1000:
        return 10, f"Volume moderado: {sales:,} vendas"
    elif sales >= 100:
        return 6, f"Volume baixo: {sales:,} vendas"
    elif sales > 0:
        return 3, f"Poucas vendas: {sales} — produto novo ou nicho"
    else:
        return 0, "Sem dados de vendas"


def _score_shipping(ships_from_brazil: bool, delivery_days: int) -> Tuple[float, str]:
    """
    Produtos enviados do Brasil têm vantagem enorme na Shopee.
    Entrega rápida = menos cancelamentos = mais conversões.
    """
    if ships_from_brazil:
        if delivery_days <= 7:
            return 10, f"🇧🇷 Envio do Brasil: entrega em {delivery_days} dias — vantagem competitiva máxima"
        else:
            return 8, f"🇧🇷 Envio do Brasil: {delivery_days} dias"
    else:
        if delivery_days <= 15:
            return 4, f"Envio internacional rápido: {delivery_days} dias"
        elif delivery_days <= 25:
            return 2, f"Envio internacional médio: {delivery_days} dias"
        else:
            return 0, f"Envio internacional lento: {delivery_days} dias — risco de cancelamento"


def _score_competition(competition: str) -> Tuple[float, str]:
    """Menos concorrência = maior chance de destaque."""
    mapping = {
        "baixa": (10, "Concorrência baixa — excelente janela de oportunidade"),
        "média": (5, "Concorrência média — necessário diferencial"),
        "alta": (1, "Concorrência alta — difícil destaque sem investimento"),
    }
    return mapping.get(competition.lower(), (5, "Concorrência não informada"))


def _score_visual_potential(product: dict) -> Tuple[float, str]:
    """
    Estima potencial visual baseado em indicadores indiretos.
    Ariel (Visual Merchandiser) considera: categoria, nome, imagem disponível.
    """
    name = product.get("name", "").lower()
    category = product.get("category", "").lower()
    has_image = bool(product.get("image_url"))

    # Categorias com alto apelo visual
    visual_categories = ["casa", "decoração", "moda", "beleza", "esporte", "kids"]
    visual_keywords = ["led", "cor", "colorido", "design", "aesthetic", "premium", "kit"]

    score = 0
    if has_image:
        score += 2
    if any(kw in category for kw in visual_categories):
        score += 1
    if any(kw in name for kw in visual_keywords):
        score += 1

    labels = {0: "Potencial visual baixo", 1: "Potencial visual moderado",
              2: "Bom potencial visual", 3: "Alto potencial visual", 4: "Excepcional apelo visual"}
    return min(score, 4), labels.get(score, "Potencial visual moderado")


def _score_saturation_risk(product: dict) -> Tuple[float, str]:
    """
    Avalia risco de saturação baseado no volume de vendas vs. categoria.
    Muitas vendas + categoria genérica = produto saturado.
    """
    sales = product.get("sales", 0)
    category = product.get("category", "").lower()
    generic_categories = ["eletrônicos", "capas", "carregadores", "fones"]

    is_generic = any(g in category for g in generic_categories)

    if sales > 50000 and is_generic:
        return 0, "Alto risco de saturação — mercado lotado"
    elif sales > 20000:
        return 1, "Risco moderado de saturação"
    else:
        return 3, "Baixo risco de saturação — espaço para novos players"


def get_score_label(score: float) -> Tuple[str, str]:
    """
    Retorna rótulo e cor baseados no score.
    Útil para a interface Streamlit.
    """
    if score >= 80:
        return "🟢 EXCELENTE", "#27AE60"
    elif score >= 65:
        return "🔵 BOM", "#2980B9"
    elif score >= 50:
        return "🟡 REGULAR", "#F39C12"
    elif score >= 35:
        return "🟠 FRACO", "#E67E22"
    else:
        return "🔴 RUIM", "#E74C3C"


def format_score_breakdown(breakdown: dict) -> str:
    """
    Formata o breakdown do score para exibição amigável.
    Serializa para JSON para armazenar no banco.
    """
    return json.dumps(breakdown, ensure_ascii=False)


def parse_score_breakdown(breakdown_json: str) -> dict:
    """Deserializa o breakdown do banco de volta para dicionário."""
    if not breakdown_json:
        return {}
    try:
        return json.loads(breakdown_json)
    except (json.JSONDecodeError, TypeError):
        return {}
