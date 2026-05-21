"""
Smart Product Finder — modules/markup_engine.py
Calculadora de viabilidade enterprise para MEI dropshipping Shopee/AliExpress.

Modela TODAS as taxas reais:
  • Comissão Shopee por categoria (16-20%)
  • Taxa de pagamento Shopee (variável por método)
  • Imposto MEI (SIMEI — 5% INSS + taxas fixas convertidas para %)
  • Frete (estimado por peso/destino ou informado)
  • Custo de anúncio Shopee Ads (CPA estimado)
  • Custo do produto AliExpress (com IOF implícito ~6.38%)
  • Embalagem extra (se aplicável)

Todos os cálculos são determinísticos e auditáveis —
cada detalhe é retornado no breakdown para exibição.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
import math

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES REAIS (MEI 2024 + Shopee Brasil)
# ─────────────────────────────────────────────────────────────────────────────

# Comissão Shopee por categoria (% sobre preço de venda)
# Fonte: Shopee Central do Vendedor 2024
SHOPEE_COMMISSION_BY_CATEGORY = {
    "Eletrônicos":          0.20,
    "Celulares e Tablets":  0.20,
    "Informática":          0.20,
    "Eletrodomésticos":     0.18,
    "Casa e Decoração":     0.18,
    "Ferramentas":          0.18,
    "Esporte e Lazer":      0.18,
    "Saúde e Beleza":       0.18,
    "Moda Feminina":        0.16,
    "Moda Masculina":       0.16,
    "Calçados":             0.16,
    "Bebês e Crianças":     0.16,
    "Brinquedos":           0.16,
    "Pets":                 0.16,
    "Alimentos":            0.16,
    "Livros":               0.16,
    "Organização":          0.18,
    "Papelaria":            0.16,
    "Acessórios":           0.18,
    "Outros":               0.18,
    "default":              0.18,
}

# Taxa de serviço de pagamento Shopee (% sobre preço + frete cobrado do comprador)
SHOPEE_PAYMENT_FEE = 0.02        # 2% fixo

# IOF implícito em compras internacionais (AliExpress via cartão)
IOF_INTERNATIONAL = 0.0638       # 6,38%

# DAS MEI 2024 — simplificação para % equivalente
# Comércio: R$ 67,00/mês fixo. Assumimos faturamento médio de R$ 2.500/mês → ~2,7%
# Serviços: R$ 71,00/mês fixo. Convertemos para % sobre faturamento.
MEI_DAS_MONTHLY_COMMERCE = 71.60  # R$ — valor 2024 com INSS
MEI_ASSUMED_MONTHLY_REVENUE = 3000.0  # R$ — faturamento base para % equivalente
MEI_EFFECTIVE_RATE = MEI_DAS_MONTHLY_COMMERCE / MEI_ASSUMED_MONTHLY_REVENUE

# Custo padrão de embalagem (saco/caixa + fita + etiqueta)
DEFAULT_PACKAGING_COST = 1.50    # R$

# Frete interno padrão (produto saindo do Brasil p/ comprador)
# Shopee Flex ou Correios. Estimativa por faixa de peso.
SHIPPING_COST_TIERS = {
    0.3: 12.0,   # até 300g → R$ 12
    0.5: 14.0,   # até 500g → R$ 14
    1.0: 18.0,   # até 1kg  → R$ 18
    2.0: 24.0,   # até 2kg  → R$ 24
    5.0: 35.0,   # até 5kg  → R$ 35
    999: 50.0,   # acima    → R$ 50
}

# Tiers de ads como % do preço de venda (CPA estimado por competitividade)
ADS_TIER = {
    "sem_ads":  0.00,
    "básico":   0.05,   # 5%  — lances baixos, produto validado
    "moderado": 0.10,   # 10% — lances médios, concorrência média
    "agressivo":0.15,   # 15% — lances altos, lançamento/nicho disputado
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ProductInput:
    """Dados brutos de entrada do produto a ser avaliado."""
    aliexpress_price_usd: float         # Preço no AliExpress em USD
    usd_brl_rate: float                 # Cotação USD→BRL
    desired_sale_price_brl: float       # Preço que pretende cobrar na Shopee
    category: str = "Outros"
    product_weight_kg: float = 0.3      # Peso estimado em kg
    ships_from_brazil: bool = False     # Se estoque já está no BR
    freight_cost_override: Optional[float] = None  # Frete real se souber
    ads_strategy: str = "moderado"      # sem_ads / básico / moderado / agressivo
    packaging_cost: float = DEFAULT_PACKAGING_COST
    extra_costs: float = 0.0            # Qualquer custo adicional (custom)
    monthly_units_estimate: int = 30    # Para projeção mensal


@dataclass
class CostBreakdown:
    """Custo detalhado, auditável linha a linha."""
    # — Custo do produto —
    product_cost_usd: float = 0.0
    iof_cost: float = 0.0
    product_cost_brl: float = 0.0       # produto + IOF

    # — Logística —
    inbound_freight: float = 0.0        # Frete AliExpress → você (estimado ou zero se BR)
    outbound_freight: float = 0.0       # Frete você → comprador
    packaging: float = 0.0

    # — Taxas Shopee —
    shopee_commission: float = 0.0
    shopee_commission_pct: float = 0.0
    shopee_payment_fee: float = 0.0

    # — Impostos —
    mei_das_equivalent: float = 0.0
    mei_rate_used: float = 0.0

    # — Marketing —
    ads_cost: float = 0.0
    ads_pct: float = 0.0

    # — Extras —
    extra_costs: float = 0.0

    # — Totais —
    total_cost: float = 0.0
    sale_price: float = 0.0
    gross_profit: float = 0.0
    gross_margin_pct: float = 0.0
    net_profit: float = 0.0
    net_margin_pct: float = 0.0

    # — Projeções mensais —
    monthly_units: int = 0
    monthly_revenue: float = 0.0
    monthly_net_profit: float = 0.0

    # — Viabilidade —
    is_viable: bool = False
    viability_score: int = 0            # 0-100
    viability_label: str = ""
    warnings: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)

    # — Break-even —
    break_even_price: float = 0.0       # Preço mínimo para não ter prejuízo
    minimum_viable_price: float = 0.0   # Preço para margem líquida de 20%


# ─────────────────────────────────────────────────────────────────────────────
# ENGINE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def calculate_viability(inp: ProductInput) -> CostBreakdown:
    """
    Calcula viabilidade completa de um produto para dropshipping Shopee/MEI.
    Retorna CostBreakdown totalmente preenchido e auditável.
    """
    bd = CostBreakdown()
    warnings = []
    recommendations = []

    sale = inp.desired_sale_price_brl
    bd.sale_price = sale
    bd.monthly_units = inp.monthly_units_estimate

    # ── 1. CUSTO DO PRODUTO ───────────────────────────────────────────────────
    bd.product_cost_usd = inp.aliexpress_price_usd
    product_brl_raw = inp.aliexpress_price_usd * inp.usd_brl_rate

    if inp.ships_from_brazil:
        # Produto nacional — sem IOF
        bd.iof_cost = 0.0
        bd.product_cost_brl = product_brl_raw
    else:
        bd.iof_cost = product_brl_raw * IOF_INTERNATIONAL
        bd.product_cost_brl = product_brl_raw + bd.iof_cost

    if bd.product_cost_brl >= sale:
        warnings.append("🚨 Custo do produto já supera o preço de venda — produto inviável.")

    # ── 2. FRETE DE ENTRADA (AliExpress → você) ───────────────────────────────
    if inp.ships_from_brazil:
        bd.inbound_freight = 0.0  # Já está no BR
    else:
        # AliExpress frequentemente oferece frete grátis p/ BR
        # Usamos estimativa conservadora de R$ 0 (free shipping) ou R$ 20 se
        # o usuário não informou. Produto acima de R$ 50 no Ali geralmente tem frete.
        if bd.product_cost_brl > 50:
            bd.inbound_freight = 0.0  # frete grátis incluso
        else:
            bd.inbound_freight = 0.0  # padrão grátis — pode ser sobreescrito

    # ── 3. FRETE DE SAÍDA (você → comprador) ──────────────────────────────────
    if inp.freight_cost_override is not None:
        bd.outbound_freight = inp.freight_cost_override
    else:
        bd.outbound_freight = _estimate_outbound_freight(inp.product_weight_kg)

    # ── 4. EMBALAGEM ──────────────────────────────────────────────────────────
    bd.packaging = inp.packaging_cost

    # ── 5. COMISSÃO SHOPEE ────────────────────────────────────────────────────
    commission_rate = SHOPEE_COMMISSION_BY_CATEGORY.get(
        inp.category,
        SHOPEE_COMMISSION_BY_CATEGORY["default"]
    )
    bd.shopee_commission_pct = commission_rate
    bd.shopee_commission = sale * commission_rate

    if commission_rate >= 0.20:
        warnings.append(f"⚠️ Categoria '{inp.category}' tem comissão alta ({commission_rate*100:.0f}%). "
                         "Considere reclassificar o produto se possível.")

    # ── 6. TAXA DE PAGAMENTO SHOPEE ───────────────────────────────────────────
    bd.shopee_payment_fee = sale * SHOPEE_PAYMENT_FEE

    # ── 7. IMPOSTO MEI ────────────────────────────────────────────────────────
    bd.mei_rate_used = MEI_EFFECTIVE_RATE
    bd.mei_das_equivalent = sale * MEI_EFFECTIVE_RATE

    # ── 8. CUSTO DE ADS ───────────────────────────────────────────────────────
    ads_rate = ADS_TIER.get(inp.ads_strategy, 0.10)
    bd.ads_pct = ads_rate
    bd.ads_cost = sale * ads_rate

    if ads_rate == 0:
        recommendations.append("💡 Sem ads: funcionará melhor para produtos com alta busca orgânica. "
                                 "Produtos novos geralmente precisam de pelo menos 5% em ads.")

    # ── 9. CUSTOS EXTRAS ──────────────────────────────────────────────────────
    bd.extra_costs = inp.extra_costs

    # ── 10. TOTAL ─────────────────────────────────────────────────────────────
    bd.total_cost = (
        bd.product_cost_brl
        + bd.inbound_freight
        + bd.outbound_freight
        + bd.packaging
        + bd.shopee_commission
        + bd.shopee_payment_fee
        + bd.mei_das_equivalent
        + bd.ads_cost
        + bd.extra_costs
    )

    # ── 11. LUCROS E MARGENS ──────────────────────────────────────────────────
    bd.gross_profit = sale - bd.product_cost_brl - bd.outbound_freight - bd.inbound_freight
    bd.gross_margin_pct = (bd.gross_profit / sale) * 100 if sale > 0 else 0

    bd.net_profit = sale - bd.total_cost
    bd.net_margin_pct = (bd.net_profit / sale) * 100 if sale > 0 else 0

    # ── 12. PROJEÇÕES MENSAIS ─────────────────────────────────────────────────
    bd.monthly_revenue = sale * inp.monthly_units_estimate
    bd.monthly_net_profit = bd.net_profit * inp.monthly_units_estimate

    # ── 13. BREAK-EVEN ────────────────────────────────────────────────────────
    # Break-even: preço onde lucro líquido = 0
    # Custo fixo / (1 - % taxas variáveis sobre preço)
    variable_rate_on_sale = (
        commission_rate + SHOPEE_PAYMENT_FEE + MEI_EFFECTIVE_RATE + ads_rate
    )
    fixed_costs = (
        bd.product_cost_brl
        + bd.inbound_freight
        + bd.outbound_freight
        + bd.packaging
        + bd.extra_costs
    )
    if variable_rate_on_sale < 1:
        bd.break_even_price = fixed_costs / (1 - variable_rate_on_sale)
    else:
        bd.break_even_price = fixed_costs * 2  # impossível — aviso

    # Preço mínimo viável (20% margem líquida)
    TARGET_NET_MARGIN = 0.20
    if (1 - variable_rate_on_sale - TARGET_NET_MARGIN) > 0:
        bd.minimum_viable_price = fixed_costs / (1 - variable_rate_on_sale - TARGET_NET_MARGIN)
    else:
        bd.minimum_viable_price = bd.break_even_price * 1.5

    # ── 14. SCORE DE VIABILIDADE ──────────────────────────────────────────────
    score = 0

    # Margem líquida (peso 50)
    if bd.net_margin_pct >= 30:   score += 50
    elif bd.net_margin_pct >= 20: score += 40
    elif bd.net_margin_pct >= 10: score += 25
    elif bd.net_margin_pct >= 5:  score += 10
    elif bd.net_margin_pct > 0:   score += 5

    # Markup (preço venda / custo produto, peso 25)
    markup = sale / bd.product_cost_brl if bd.product_cost_brl > 0 else 0
    if markup >= 4:    score += 25
    elif markup >= 3:  score += 20
    elif markup >= 2:  score += 12
    elif markup >= 1.5:score += 5

    # Lucro absoluto por unidade (peso 25)
    if bd.net_profit >= 20:   score += 25
    elif bd.net_profit >= 10: score += 18
    elif bd.net_profit >= 5:  score += 10
    elif bd.net_profit >= 1:  score += 3

    bd.viability_score = min(score, 100)

    if bd.viability_score >= 75:
        bd.is_viable = True
        bd.viability_label = "🟢 EXCELENTE — Produto muito viável"
    elif bd.viability_score >= 55:
        bd.is_viable = True
        bd.viability_label = "🔵 BOM — Produto viável"
    elif bd.viability_score >= 35:
        bd.is_viable = False
        bd.viability_label = "🟡 REGULAR — Margem apertada"
    elif bd.viability_score >= 15:
        bd.is_viable = False
        bd.viability_label = "🟠 FRACO — Alto risco de prejuízo"
    else:
        bd.is_viable = False
        bd.viability_label = "🔴 INVIÁVEL — Não publicar"

    # ── 15. RECOMENDAÇÕES AUTOMÁTICAS ─────────────────────────────────────────
    if bd.net_profit < 0:
        recommendations.append(
            f"❌ Prejuízo de R$ {abs(bd.net_profit):.2f} por unidade. "
            f"Preço mínimo para break-even: R$ {bd.break_even_price:.2f}"
        )

    if bd.net_margin_pct < 20 and bd.net_profit > 0:
        recommendations.append(
            f"💡 Para atingir 20% de margem líquida, suba o preço para "
            f"R$ {bd.minimum_viable_price:.2f} (+R$ {bd.minimum_viable_price - sale:.2f})"
        )

    if markup < 2.5:
        recommendations.append(
            "⚠️ Markup abaixo de 2.5x — risco alto. "
            "Pequenas variações de frete ou comissão vão zerar o lucro."
        )

    if not inp.ships_from_brazil and bd.net_margin_pct > 0:
        recommendations.append(
            "💡 Se encontrar esse produto com estoque no Brasil, "
            f"o IOF economizado seria R$ {bd.iof_cost:.2f}/unidade."
        )

    if inp.ads_strategy == "sem_ads" and bd.net_margin_pct >= 20:
        recommendations.append(
            "💡 Margem confortável — considere alocar 5-8% em Shopee Ads "
            "para acelerar o volume sem comprometer a rentabilidade."
        )

    if bd.monthly_net_profit > 0:
        months_to_1k = math.ceil(1000 / bd.monthly_net_profit) if bd.monthly_net_profit > 0 else 999
        if months_to_1k <= 3:
            recommendations.append(
                f"🚀 Com {inp.monthly_units_estimate} unidades/mês, "
                f"você atinge R$ 1.000 de lucro em {months_to_1k} mês(es)."
            )

    bd.warnings = warnings
    bd.recommendations = recommendations

    return bd


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _estimate_outbound_freight(weight_kg: float) -> float:
    """Estima frete de saída baseado no peso do produto."""
    for max_weight, cost in sorted(SHIPPING_COST_TIERS.items()):
        if weight_kg <= max_weight:
            return cost
    return 50.0


def get_shopee_categories() -> list:
    """Retorna lista de categorias Shopee para o selectbox."""
    return sorted([k for k in SHOPEE_COMMISSION_BY_CATEGORY.keys() if k != "default"])


def get_ads_strategies() -> dict:
    """Retorna opções de estratégia de ads para o selectbox."""
    return {
        "sem_ads":   "Sem Ads (orgânico)",
        "básico":    "Básico — 5% do preço (produto já validado)",
        "moderado":  "Moderado — 10% do preço (lançamento normal)",
        "agressivo": "Agressivo — 15% do preço (nicho disputado)",
    }


def simulate_price_sensitivity(inp: ProductInput, n: int = 7) -> list:
    """
    Simula o efeito de diferentes preços de venda sobre a margem.
    Retorna lista de dicts para plotar gráfico.
    """
    results = []
    base = inp.desired_sale_price_brl
    # testa de -30% a +40% do preço base
    multipliers = [0.70, 0.80, 0.90, 1.00, 1.15, 1.30, 1.40]
    for m in multipliers:
        test_inp = ProductInput(
            aliexpress_price_usd=inp.aliexpress_price_usd,
            usd_brl_rate=inp.usd_brl_rate,
            desired_sale_price_brl=round(base * m, 2),
            category=inp.category,
            product_weight_kg=inp.product_weight_kg,
            ships_from_brazil=inp.ships_from_brazil,
            freight_cost_override=inp.freight_cost_override,
            ads_strategy=inp.ads_strategy,
            packaging_cost=inp.packaging_cost,
            extra_costs=inp.extra_costs,
            monthly_units_estimate=inp.monthly_units_estimate,
        )
        bd = calculate_viability(test_inp)
        results.append({
            "price": round(base * m, 2),
            "net_profit": round(bd.net_profit, 2),
            "net_margin_pct": round(bd.net_margin_pct, 1),
            "score": bd.viability_score,
            "label": bd.viability_label.split("—")[0].strip(),
        })
    return results
