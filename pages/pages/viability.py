"""
Smart Product Finder — pages/viability.py
Aba de Análise de Viabilidade Enterprise.

Cole o link do AliExpress → calcula lucro real após TODAS as taxas:
  • Comissão Shopee por categoria
  • Taxa de pagamento Shopee
  • IOF importação
  • Imposto MEI (DAS SIMEI equivalente)
  • Frete interno (estimado por peso)
  • Custo de Shopee Ads
  • Embalagem

Inclui:
  • Simulação de sensibilidade de preço (gráfico)
  • Projeção mensal de lucro
  • Recomendações automáticas
  • Break-even price
  • Modo de comparação (até 3 produtos)
"""

import streamlit as st
import asyncio
from datetime import datetime

from modules.markup_engine import (
    ProductInput, calculate_viability, simulate_price_sensitivity,
    get_shopee_categories, get_ads_strategies,
)
from modules.aliexpress_fetcher import run_async_fetch, AliProductData


# ─────────────────────────────────────────────────────────────────────────────
# CACHE — evita refetch desnecessário
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch_product(url: str) -> dict:
    """Busca produto com cache de 1h."""
    product = run_async_fetch(url)
    # Converte dataclass para dict para serialização do cache
    return {
        "url": product.url,
        "title": product.title,
        "price_usd": product.price_usd,
        "rating": product.rating,
        "review_count": product.review_count,
        "orders_count": product.orders_count,
        "ships_from": product.ships_from,
        "estimated_weight_kg": product.estimated_weight_kg,
        "image_url": product.image_url,
        "store_name": product.store_name,
        "has_choice_badge": product.has_choice_badge,
        "category_hint": product.category_hint,
        "success": product.success,
        "error": product.error,
        "extraction_method": product.extraction_method,
    }


# ─────────────────────────────────────────────────────────────────────────────
# RENDER PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def render():
    st.header("📐 Análise de Viabilidade")
    st.markdown(
        "Cole o link do AliExpress e descubra se o produto sobra **lucro real** "
        "após comissão Shopee, IOF, frete, MEI e Ads."
    )

    # Tabs principais
    tab_single, tab_compare, tab_guide = st.tabs([
        "🔍 Analisar Produto",
        "⚖️ Comparar Produtos",
        "📚 Como Funciona",
    ])

    with tab_single:
        _render_single_analysis()

    with tab_compare:
        _render_comparison()

    with tab_guide:
        _render_guide()


# ─────────────────────────────────────────────────────────────────────────────
# ABA: ANÁLISE ÚNICA
# ─────────────────────────────────────────────────────────────────────────────

def _render_single_analysis():

    # ── INPUT: URL ────────────────────────────────────────────────────────────
    st.subheader("1️⃣ URL do Produto")
    col_url, col_btn = st.columns([5, 1])
    with col_url:
        product_url = st.text_input(
            "Link do AliExpress",
            placeholder="https://www.aliexpress.com/item/1234567890.html",
            label_visibility="collapsed",
        )
    with col_btn:
        fetch_btn = st.button("🔍 Buscar", type="primary", use_container_width=True)

    # Estado do produto buscado
    if "fetched_product" not in st.session_state:
        st.session_state["fetched_product"] = None

    if fetch_btn and product_url:
        with st.spinner("Buscando dados do produto..."):
            st.session_state["fetched_product"] = cached_fetch_product(product_url)

    product_data = st.session_state.get("fetched_product")

    # Exibe dados do produto buscado
    if product_data:
        _render_product_preview(product_data)

    st.divider()

    # ── INPUT: PARÂMETROS DE CÁLCULO ──────────────────────────────────────────
    st.subheader("2️⃣ Parâmetros de Cálculo")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**💵 Produto**")
        price_usd = st.number_input(
            "Preço no AliExpress (USD)",
            min_value=0.01, max_value=9999.0, step=0.5,
            value=float(product_data["price_usd"]) if product_data and product_data.get("price_usd") else 10.0,
            help="Preço que você paga ao fornecedor, em dólares",
        )
        usd_brl = st.number_input(
            "Cotação USD → BRL",
            min_value=1.0, max_value=20.0, step=0.05, value=5.70,
            help="Use a cotação do dia. Padrão: 5.70",
        )
        ships_from_brazil = st.checkbox(
            "Produto enviado do Brasil",
            value=product_data.get("ships_from", "China") == "BR" if product_data else False,
            help="Se marcado, não haverá IOF (6,38%) no custo",
        )

    with col2:
        st.markdown("**🏷️ Preço de Venda**")
        # Sugere preço automático (3.5x do custo em BRL)
        cost_brl = price_usd * usd_brl
        suggested_price = round(cost_brl * 3.5, 2)
        sale_price = st.number_input(
            "Preço de venda na Shopee (R$)",
            min_value=1.0, max_value=99999.0, step=1.0,
            value=suggested_price,
            help="Quanto você quer cobrar do comprador na Shopee",
        )
        category = st.selectbox(
            "Categoria Shopee",
            options=get_shopee_categories(),
            index=get_shopee_categories().index("Organização")
                  if "Organização" in get_shopee_categories() else 0,
            help="Afeta % da comissão Shopee (16% a 20%)",
        )
        weight_kg = st.number_input(
            "Peso estimado (kg)",
            min_value=0.01, max_value=50.0, step=0.05, value=0.30,
            help="Usado para estimar o frete de envio ao comprador",
        )

    with col3:
        st.markdown("**📢 Custos Operacionais**")
        ads_options = get_ads_strategies()
        ads_strategy = st.selectbox(
            "Estratégia Shopee Ads",
            options=list(ads_options.keys()),
            format_func=lambda k: ads_options[k],
            index=2,  # moderado
            help="CPA estimado como % do preço de venda",
        )
        freight_override = st.number_input(
            "Frete de envio real (R$) — 0 para estimar",
            min_value=0.0, max_value=200.0, step=1.0, value=0.0,
            help="Se souber o frete exato, informe aqui. Senão deixe 0.",
        )
        monthly_units = st.number_input(
            "Unidades estimadas/mês",
            min_value=1, max_value=10000, step=5, value=30,
            help="Para projeção de lucro mensal",
        )

    # Custos extras opcionais
    with st.expander("➕ Custos Adicionais (opcional)", expanded=False):
        ec1, ec2 = st.columns(2)
        with ec1:
            packaging = st.number_input(
                "Custo de embalagem (R$)", min_value=0.0, max_value=50.0, step=0.5, value=1.50
            )
        with ec2:
            extra_costs = st.number_input(
                "Outros custos fixos por unidade (R$)", min_value=0.0, max_value=500.0, step=1.0, value=0.0
            )

    # ── CALCULAR ──────────────────────────────────────────────────────────────
    calc_btn = st.button("⚡ Calcular Viabilidade Completa", type="primary", use_container_width=True)

    if calc_btn or st.session_state.get("auto_calc"):
        st.session_state["auto_calc"] = False

        inp = ProductInput(
            aliexpress_price_usd=price_usd,
            usd_brl_rate=usd_brl,
            desired_sale_price_brl=sale_price,
            category=category,
            product_weight_kg=weight_kg,
            ships_from_brazil=ships_from_brazil,
            freight_cost_override=freight_override if freight_override > 0 else None,
            ads_strategy=ads_strategy,
            packaging_cost=packaging,
            extra_costs=extra_costs,
            monthly_units_estimate=int(monthly_units),
        )

        bd = calculate_viability(inp)
        st.session_state["last_viability"] = {"inp": inp, "bd": bd}

    # ── RESULTADO ─────────────────────────────────────────────────────────────
    if "last_viability" in st.session_state:
        bd = st.session_state["last_viability"]["bd"]
        inp = st.session_state["last_viability"]["inp"]

        st.divider()
        _render_result(bd, inp)


def _render_product_preview(p: dict):
    """Mostra card resumido do produto buscado."""
    is_demo = p.get("extraction_method") == "demo_fallback"
    label = "⚠️ Dados estimados (demo)" if is_demo else f"✅ Dados extraídos via {p.get('extraction_method')}"

    with st.container():
        st.markdown(f"""
        <div style='background:var(--color-background-secondary);border:1px solid var(--color-border-tertiary);
                    border-radius:8px;padding:0.8rem 1rem;margin:0.5rem 0'>
            <div style='font-weight:500;color:var(--color-text-primary);font-size:0.9rem'>
                {p.get("title","Sem título") or "Sem título"}
            </div>
            <div style='color:var(--color-text-secondary);font-size:0.8rem;margin-top:0.3rem'>
                💵 US$ {p.get("price_usd",0):.2f} &nbsp;·&nbsp;
                ⭐ {p.get("rating",0):.1f} &nbsp;·&nbsp;
                📦 {p.get("orders_count",0):,} pedidos &nbsp;·&nbsp;
                🌍 Envia de: {p.get("ships_from","?")} &nbsp;·&nbsp;
                <span style='color:var(--color-text-tertiary)'>{label}</span>
            </div>
        </div>""", unsafe_allow_html=True)

    if p.get("error"):
        st.info(f"ℹ️ {p['error']} Ajuste o preço manualmente abaixo.")


def _render_result(bd, inp):
    """Renderiza o resultado completo da análise de viabilidade."""

    # ── VEREDITO PRINCIPAL ────────────────────────────────────────────────────
    score = bd.viability_score
    color = "#27AE60" if score >= 75 else "#2980B9" if score >= 55 else "#F39C12" if score >= 35 else "#E74C3C"

    st.markdown(f"""
    <div style='background:{color}15;border:2px solid {color};border-radius:12px;
                padding:1.2rem 1.5rem;margin-bottom:1rem'>
        <div style='display:flex;justify-content:space-between;align-items:center'>
            <div>
                <div style='font-size:1.3rem;font-weight:500;color:{color}'>{bd.viability_label}</div>
                <div style='color:var(--color-text-secondary);font-size:0.85rem;margin-top:0.2rem'>
                    Score de viabilidade baseado em margem, markup e lucro absoluto
                </div>
            </div>
            <div style='text-align:center;min-width:80px'>
                <div style='font-size:2.5rem;font-weight:700;color:{color};line-height:1'>{score}</div>
                <div style='font-size:0.7rem;color:var(--color-text-tertiary)'>/100</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        delta_color = "normal" if bd.net_profit > 0 else "inverse"
        st.metric("💰 Lucro / Unidade", f"R$ {bd.net_profit:.2f}",
                  delta=f"{bd.net_margin_pct:.1f}% margem", delta_color=delta_color)
    with k2:
        st.metric("📊 Margem Líquida", f"{bd.net_margin_pct:.1f}%",
                  delta="alvo ≥ 20%", delta_color="off")
    with k3:
        markup = bd.sale_price / bd.product_cost_brl if bd.product_cost_brl > 0 else 0
        st.metric("📈 Markup", f"{markup:.1f}x",
                  delta="alvo ≥ 3x", delta_color="off")
    with k4:
        st.metric("📅 Lucro Mensal", f"R$ {bd.monthly_net_profit:.0f}",
                  delta=f"{inp.monthly_units_estimate} un/mês", delta_color="off")
    with k5:
        st.metric("⚖️ Break-even", f"R$ {bd.break_even_price:.2f}",
                  delta=f"atual R$ {bd.sale_price:.2f}", delta_color="off")

    st.divider()

    # ── BREAKDOWN DETALHADO ───────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("📋 Breakdown de Custos")

        _cost_row("Produto AliExpress", bd.product_cost_brl, bd.sale_price,
                  f"US$ {inp.aliexpress_price_usd:.2f} × {inp.usd_brl_rate:.2f}"
                  + (f" + IOF R$ {bd.iof_cost:.2f}" if not inp.ships_from_brazil else " (sem IOF)"))

        if bd.outbound_freight > 0:
            _cost_row("Frete (envio ao comprador)", bd.outbound_freight, bd.sale_price,
                      f"Estimado para {inp.product_weight_kg}kg")

        _cost_row(
            f"Comissão Shopee ({bd.shopee_commission_pct*100:.0f}%)",
            bd.shopee_commission, bd.sale_price,
            f"Categoria: {inp.category}"
        )

        _cost_row("Taxa pagamento Shopee (2%)", bd.shopee_payment_fee, bd.sale_price)

        _cost_row(
            f"Imposto MEI (~{bd.mei_rate_used*100:.1f}% equiv.)",
            bd.mei_das_equivalent, bd.sale_price,
            "DAS SIMEI 2024: R$ 71,60/mês"
        )

        _cost_row(
            f"Shopee Ads ({bd.ads_pct*100:.0f}%)",
            bd.ads_cost, bd.sale_price,
            f"Estratégia: {inp.ads_strategy}"
        )

        if bd.packaging > 0:
            _cost_row("Embalagem", bd.packaging, bd.sale_price)

        if bd.extra_costs > 0:
            _cost_row("Custos extras", bd.extra_costs, bd.sale_price)

        # Total
        st.markdown(f"""
        <div style='background:var(--color-background-secondary);border-radius:8px;
                    padding:0.6rem 1rem;margin:0.5rem 0;display:flex;justify-content:space-between'>
            <span style='font-weight:500'>Total de Custos</span>
            <span style='font-weight:700;color:var(--color-text-danger)'>R$ {bd.total_cost:.2f}
            &nbsp;<span style='font-size:0.8rem;color:var(--color-text-tertiary)'>
            ({bd.total_cost/bd.sale_price*100:.1f}% do preço)</span></span>
        </div>""", unsafe_allow_html=True)

        # Lucro
        profit_color = "#27AE60" if bd.net_profit > 0 else "#E74C3C"
        st.markdown(f"""
        <div style='background:{profit_color}15;border:1px solid {profit_color};border-radius:8px;
                    padding:0.6rem 1rem;margin:0.3rem 0;display:flex;justify-content:space-between'>
            <span style='font-weight:500'>Lucro Líquido / Unidade</span>
            <span style='font-weight:700;color:{profit_color}'>R$ {bd.net_profit:.2f}
            &nbsp;<span style='font-size:0.8rem'>({bd.net_margin_pct:.1f}%)</span></span>
        </div>""", unsafe_allow_html=True)

    with col_right:
        st.subheader("📈 Projeção Mensal")
        monthly = inp.monthly_units_estimate
        st.markdown(f"""
        <div style='background:var(--color-background-secondary);border-radius:8px;padding:1rem;margin-bottom:0.8rem'>
            <div style='display:grid;grid-template-columns:1fr 1fr;gap:0.5rem'>
                <div>
                    <div style='font-size:0.72rem;color:var(--color-text-tertiary)'>Unidades</div>
                    <div style='font-size:1.1rem;font-weight:500'>{monthly}</div>
                </div>
                <div>
                    <div style='font-size:0.72rem;color:var(--color-text-tertiary)'>Receita</div>
                    <div style='font-size:1.1rem;font-weight:500'>R$ {bd.monthly_revenue:.0f}</div>
                </div>
                <div>
                    <div style='font-size:0.72rem;color:var(--color-text-tertiary)'>Custo Total</div>
                    <div style='font-size:1.1rem;font-weight:500'>R$ {bd.total_cost * monthly:.0f}</div>
                </div>
                <div>
                    <div style='font-size:0.72rem;color:{"#27AE60" if bd.monthly_net_profit > 0 else "#E74C3C"}'>Lucro Líquido</div>
                    <div style='font-size:1.3rem;font-weight:700;color:{"#27AE60" if bd.monthly_net_profit > 0 else "#E74C3C"}'>
                        R$ {bd.monthly_net_profit:.0f}
                    </div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Cenários mensais
        st.markdown("**Cenários de Volume:**")
        for units in [10, 30, 50, 100, 200]:
            monthly_profit = bd.net_profit * units
            bar_pct = min(abs(monthly_profit) / 500, 1.0)
            bar_color = "#27AE60" if monthly_profit > 0 else "#E74C3C"
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:0.5rem;margin:0.3rem 0'>
                <div style='min-width:55px;font-size:0.8rem;color:var(--color-text-secondary)'>{units} un/mês</div>
                <div style='flex:1;height:12px;background:var(--color-background-secondary);border-radius:6px;overflow:hidden'>
                    <div style='width:{bar_pct*100:.0f}%;height:100%;background:{bar_color};border-radius:6px'></div>
                </div>
                <div style='min-width:70px;font-size:0.8rem;font-weight:500;color:{bar_color};text-align:right'>
                    R$ {monthly_profit:.0f}
                </div>
            </div>""", unsafe_allow_html=True)

    # ── SENSIBILIDADE DE PREÇO ────────────────────────────────────────────────
    st.divider()
    st.subheader("📊 Sensibilidade ao Preço de Venda")
    st.caption("Veja como a margem muda conforme o preço — encontre o ponto ótimo.")

    sensitivity = simulate_price_sensitivity(inp)

    try:
        import pandas as pd
        df_sens = pd.DataFrame(sensitivity)

        # Tabela visual
        cols = st.columns(len(sensitivity))
        for i, (col, row) in enumerate(zip(cols, sensitivity)):
            is_current = abs(row["price"] - inp.desired_sale_price_brl) < 0.5
            border = "2px solid #FF6B35" if is_current else "1px solid var(--color-border-tertiary)"
            bg = "#FF6B3510" if is_current else "var(--color-background-secondary)"
            margin_color = "#27AE60" if row["net_margin_pct"] >= 20 else "#F39C12" if row["net_margin_pct"] >= 10 else "#E74C3C"
            with col:
                st.markdown(f"""
                <div style='border:{border};background:{bg};border-radius:8px;
                            padding:0.5rem;text-align:center'>
                    <div style='font-size:0.75rem;color:var(--color-text-tertiary)'>R$</div>
                    <div style='font-size:0.95rem;font-weight:500'>{row["price"]:.2f}</div>
                    <div style='font-size:0.8rem;color:{margin_color};font-weight:500'>
                        {row["net_margin_pct"]:.1f}%
                    </div>
                    <div style='font-size:0.7rem;color:var(--color-text-secondary)'>
                        R$ {row["net_profit"]:.2f}
                    </div>
                </div>""", unsafe_allow_html=True)
    except ImportError:
        st.warning("pandas não instalado — tabela de sensibilidade indisponível")

    # ── WARNINGS E RECOMENDAÇÕES ──────────────────────────────────────────────
    if bd.warnings or bd.recommendations:
        st.divider()
        col_w, col_r = st.columns(2)
        with col_w:
            if bd.warnings:
                st.subheader("⚠️ Alertas")
                for w in bd.warnings:
                    st.warning(w)
        with col_r:
            if bd.recommendations:
                st.subheader("💡 Recomendações")
                for r in bd.recommendations:
                    st.info(r)

    # ── AÇÃO: SALVAR NO BANCO ─────────────────────────────────────────────────
    st.divider()
    col_save, col_export, _ = st.columns([2, 2, 3])
    with col_save:
        if st.button("💾 Salvar Análise", use_container_width=True):
            _save_viability_analysis(inp, bd)
            st.success("✅ Análise salva! Acesse em Resultados.")
    with col_export:
        export_data = _build_export(inp, bd)
        st.download_button(
            "⬇️ Exportar CSV",
            data=export_data,
            file_name=f"viabilidade_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )


def _cost_row(label: str, cost: float, sale: float, note: str = ""):
    """Renderiza uma linha de custo no breakdown."""
    pct = (cost / sale * 100) if sale > 0 else 0
    note_html = f"<span style='color:var(--color-text-tertiary);font-size:0.72rem'> — {note}</span>" if note else ""
    st.markdown(f"""
    <div style='display:flex;justify-content:space-between;align-items:baseline;
                padding:0.25rem 0;border-bottom:1px solid var(--color-border-tertiary)'>
        <span style='color:var(--color-text-secondary);font-size:0.85rem'>{label}{note_html}</span>
        <span style='font-size:0.85rem;color:var(--color-text-danger)'>
            − R$ {cost:.2f}
            <span style='font-size:0.72rem;color:var(--color-text-tertiary)'>&nbsp;({pct:.1f}%)</span>
        </span>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ABA: COMPARAÇÃO DE PRODUTOS
# ─────────────────────────────────────────────────────────────────────────────

def _render_comparison():
    st.subheader("⚖️ Comparar até 3 Produtos")
    st.caption("Analise múltiplos produtos lado a lado para escolher o mais rentável.")

    n_products = st.radio("Quantos produtos comparar?", [2, 3], horizontal=True)
    st.divider()

    inputs = []
    cols = st.columns(int(n_products))
    categories = get_shopee_categories()
    ads_opts = get_ads_strategies()

    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**Produto {i+1}**")
            price = st.number_input(f"Preço AliExpress USD #{i+1}", 0.01, 9999.0, 10.0 + i*5, key=f"cmp_price_{i}")
            sale  = st.number_input(f"Preço venda R$ #{i+1}", 1.0, 99999.0, round((10.0+i*5)*5.7*3.2,2), key=f"cmp_sale_{i}")
            cat   = st.selectbox(f"Categoria #{i+1}", categories, key=f"cmp_cat_{i}")
            ads   = st.selectbox(f"Ads #{i+1}", list(ads_opts.keys()),
                                  format_func=lambda k: ads_opts[k], index=2, key=f"cmp_ads_{i}")
            inputs.append(ProductInput(
                aliexpress_price_usd=price, usd_brl_rate=5.70,
                desired_sale_price_brl=sale, category=cat,
                ads_strategy=ads, monthly_units_estimate=30,
            ))

    if st.button("⚡ Comparar", type="primary", use_container_width=True):
        results = [calculate_viability(inp) for inp in inputs]
        st.divider()

        # Cabeçalho
        header_cols = st.columns(n_products)
        for i, (col, bd) in enumerate(zip(header_cols, results)):
            score = bd.viability_score
            color = "#27AE60" if score >= 75 else "#2980B9" if score >= 55 else "#F39C12" if score >= 35 else "#E74C3C"
            with col:
                st.markdown(f"""
                <div style='text-align:center;background:{color}15;border:1px solid {color};
                            border-radius:8px;padding:0.8rem'>
                    <div style='font-size:2rem;font-weight:700;color:{color}'>{score}</div>
                    <div style='font-size:0.8rem;color:var(--color-text-secondary)'>Score</div>
                    <div style='font-size:0.75rem;color:{color};margin-top:0.3rem'>{bd.viability_label.split("—")[0]}</div>
                </div>""", unsafe_allow_html=True)

        st.divider()

        # Métricas comparativas
        metrics = [
            ("Margem Líquida", lambda bd: f"{bd.net_margin_pct:.1f}%", lambda bd: bd.net_margin_pct),
            ("Lucro / Unidade", lambda bd: f"R$ {bd.net_profit:.2f}", lambda bd: bd.net_profit),
            ("Lucro Mensal (30 un)", lambda bd: f"R$ {bd.monthly_net_profit:.0f}", lambda bd: bd.monthly_net_profit),
            ("Break-even", lambda bd: f"R$ {bd.break_even_price:.2f}", lambda bd: -bd.break_even_price),
            ("Markup", lambda bd: f"{bd.sale_price/bd.product_cost_brl:.1f}x" if bd.product_cost_brl>0 else "—",
             lambda bd: bd.sale_price/bd.product_cost_brl if bd.product_cost_brl>0 else 0),
        ]

        for label, fmt, sort_key in metrics:
            vals = [sort_key(bd) for bd in results]
            best_idx = vals.index(max(vals))
            row_cols = st.columns([2] + [1]*n_products)
            with row_cols[0]:
                st.markdown(f"<div style='padding:0.3rem 0;font-size:0.85rem;color:var(--color-text-secondary)'>{label}</div>", unsafe_allow_html=True)
            for j, (col, bd) in enumerate(zip(row_cols[1:], results)):
                is_best = (j == best_idx)
                style = "font-weight:700;color:#27AE60;" if is_best else "color:var(--color-text-primary);"
                with col:
                    st.markdown(f"<div style='padding:0.3rem 0;text-align:center;{style}font-size:0.85rem'>{'🥇 ' if is_best else ''}{fmt(bd)}</div>", unsafe_allow_html=True)

        # Recomendação final
        final_scores = [bd.viability_score for bd in results]
        best = final_scores.index(max(final_scores)) + 1
        st.success(f"🏆 **Produto {best}** tem o melhor score de viabilidade ({max(final_scores)}/100)")


# ─────────────────────────────────────────────────────────────────────────────
# ABA: GUIA
# ─────────────────────────────────────────────────────────────────────────────

def _render_guide():
    st.subheader("📚 Como a Calculadora Funciona")

    with st.expander("🔢 Fórmula de Custo Total", expanded=True):
        st.markdown("""
        ```
        Custo Total = Produto (c/ IOF) + Frete Saída + Embalagem
                    + Comissão Shopee  + Taxa Pagamento Shopee
                    + Imposto MEI      + Shopee Ads
        
        Lucro Líquido = Preço de Venda − Custo Total
        Margem Líquida = (Lucro / Preço Venda) × 100
        ```
        """)

    with st.expander("🛍️ Taxas Shopee (2024)"):
        import pandas as pd
        from modules.markup_engine import SHOPEE_COMMISSION_BY_CATEGORY
        cats = {k: f"{v*100:.0f}%" for k, v in SHOPEE_COMMISSION_BY_CATEGORY.items() if k != "default"}
        df = pd.DataFrame(list(cats.items()), columns=["Categoria", "Comissão"])
        st.dataframe(df, use_container_width=True, hide_index=True, height=280)
        st.markdown("**+ 2% taxa de pagamento** em todos os pedidos.")

    with st.expander("🏛️ Imposto MEI (SIMEI 2024)"):
        st.markdown("""
        - DAS Comércio 2024: **R$ 71,60/mês** (INSS + ICMS)
        - Para cálculo por unidade: dividimos pelo faturamento médio mensal estimado
        - Faturamento usado no cálculo: R$ 3.000/mês → **~2,4% por venda**
        - Ajuste em "Custos Adicionais" se seu faturamento for muito diferente
        """)

    with st.expander("💵 IOF em Compras Internacionais"):
        st.markdown("""
        - Compras no AliExpress com cartão brasileiro = **6,38% de IOF**
        - Já incluído automaticamente no cálculo do custo do produto
        - Se o produto vier de estoque no Brasil (marque a opção), **IOF = zero**
        """)

    with st.expander("📢 Shopee Ads — CPA Estimado"):
        for k, v in get_ads_strategies().items():
            from modules.markup_engine import ADS_TIER
            pct = ADS_TIER.get(k, 0)
            st.markdown(f"- **{v}**: {pct*100:.0f}% do preço de venda por conversão estimada")

    with st.expander("🎯 Score de Viabilidade — Como é calculado"):
        st.markdown("""
        | Critério | Peso | Máximo |
        |---|---|---|
        | Margem líquida ≥ 30% | 50 pts | 50 |
        | Markup ≥ 4x | 25 pts | 25 |
        | Lucro absoluto ≥ R$ 20 | 25 pts | 25 |

        **Escala de classificação:**
        - 🟢 75-100: Excelente
        - 🔵 55-74: Bom
        - 🟡 35-54: Regular
        - 🟠 15-34: Fraco
        - 🔴 0-14: Inviável
        """)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _save_viability_analysis(inp: ProductInput, bd):
    """Salva análise de viabilidade no banco como produto para análise posterior."""
    try:
        import uuid
        from database import db as _db
        from modules.scoring import format_score_breakdown

        pid = f"via_{uuid.uuid4().hex[:8]}"
        product = {
            "id": pid,
            "name": f"Análise via calculadora — R$ {inp.desired_sale_price_brl:.2f}",
            "link": "",
            "price": inp.aliexpress_price_usd * inp.usd_brl_rate,
            "rating": 0,
            "sales": 0,
            "delivery_days": 0,
            "ships_from_brazil": inp.ships_from_brazil,
            "choice_badge": False,
            "image_url": "",
            "category": inp.category,
            "collected_at": datetime.now().isoformat(),
        }
        sid = _db.save_search({
            "keyword": "Calculadora viabilidade",
            "category": inp.category, "min_price": 0, "max_price": 0,
            "min_rating": 0, "min_sales": 0, "ships_from_brazil": False,
            "choice_badge": False, "min_margin": 20, "freight_cost": inp.product_cost_brl,
            "target_price": inp.desired_sale_price_brl,
            "competition": "média", "notes": "Salvo da calculadora de viabilidade",
        })
        _db.save_product(product, sid)
        _db.save_analysis({
            "product_id": pid,
            "score": float(bd.viability_score),
            "score_breakdown": "{}",
            "ai_potential": "alto" if bd.is_viable else "baixo",
            "ai_target_audience": "",
            "ai_strengths": f"Margem {bd.net_margin_pct:.1f}% | Lucro R$ {bd.net_profit:.2f}/un",
            "ai_weaknesses": " | ".join(bd.warnings) if bd.warnings else "",
            "ai_risk": "baixo" if bd.is_viable else "alto",
            "ai_price_suggestion": inp.desired_sale_price_brl,
            "ai_shopee_title": "",
            "ai_description": f"Análise de viabilidade: {bd.viability_label}",
            "ai_creative_ideas": "",
            "ai_hashtags": "",
            "ai_decision": "aprovado" if bd.is_viable else "rejeitado",
        })
    except Exception as e:
        st.warning(f"Não foi possível salvar no banco: {e}")


def _build_export(inp: ProductInput, bd) -> bytes:
    """Gera CSV com todos os dados da análise para download."""
    lines = [
        "Campo,Valor",
        f"Preço AliExpress USD,{inp.aliexpress_price_usd:.2f}",
        f"Cotação USD BRL,{inp.usd_brl_rate:.2f}",
        f"Custo produto BRL,{bd.product_cost_brl:.2f}",
        f"IOF,{bd.iof_cost:.2f}",
        f"Frete saída,{bd.outbound_freight:.2f}",
        f"Embalagem,{bd.packaging:.2f}",
        f"Comissão Shopee,{bd.shopee_commission:.2f}",
        f"Taxa pagamento Shopee,{bd.shopee_payment_fee:.2f}",
        f"Imposto MEI,{bd.mei_das_equivalent:.2f}",
        f"Shopee Ads,{bd.ads_cost:.2f}",
        f"Custos extras,{bd.extra_costs:.2f}",
        f"TOTAL CUSTOS,{bd.total_cost:.2f}",
        f"Preço de venda,{bd.sale_price:.2f}",
        f"Lucro líquido,{bd.net_profit:.2f}",
        f"Margem líquida %,{bd.net_margin_pct:.1f}",
        f"Score viabilidade,{bd.viability_score}",
        f"Veredito,{bd.viability_label}",
        f"Break-even,{bd.break_even_price:.2f}",
        f"Preço mínimo viável (20%),{bd.minimum_viable_price:.2f}",
        f"Projeção mensal ({inp.monthly_units_estimate} un),{bd.monthly_net_profit:.2f}",
    ]
    return ("\ufeff" + "\n".join(lines)).encode("utf-8")
