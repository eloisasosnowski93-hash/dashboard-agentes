"""
Smart Product Finder - Página: Resultados
Exibe todos os produtos analisados com filtros, detalhes e ações.
Ariel (Visual Merchandiser) e Luna (Copywriter) consultam aqui para executar.
"""

import streamlit as st
import pandas as pd

from database import db
from modules import scoring, exporter


def render():
    """Renderiza a página de resultados com filtros e tabela de produtos."""

    st.header("📊 Resultados da Análise")

    # ── FILTROS LATERAIS ─────────────────────────────────────────────────────
    with st.expander("🔧 Filtros de Exibição", expanded=True):
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            filter_min_score = st.number_input(
                "Score Mínimo", min_value=0, max_value=100, value=0
            )
        with col2:
            filter_max_price = st.number_input(
                "Custo Máximo (R$)", min_value=0.0, value=0.0, step=5.0,
                help="0 = sem limite"
            )
        with col3:
            filter_min_rating = st.number_input(
                "Avaliação Mínima", min_value=0.0, max_value=5.0, value=0.0, step=0.1
            )
        with col4:
            categories = db.get_categories()
            filter_category = st.selectbox("Categoria", options=categories)

        with col5:
            filter_status = st.selectbox(
                "Status",
                options=["todos", "aprovado", "rejeitado"],
                format_func=lambda x: {"todos": "🔵 Todos", "aprovado": "✅ Aprovados", "rejeitado": "❌ Rejeitados"}.get(x, x)
            )

    # Monta dicionário de filtros
    filters = {}
    if filter_min_score > 0:
        filters["min_score"] = filter_min_score
    if filter_max_price > 0:
        filters["max_price"] = filter_max_price
    if filter_min_rating > 0:
        filters["min_rating"] = filter_min_rating
    if filter_category != "Todas":
        filters["category"] = filter_category
    if filter_status != "todos":
        filters["status"] = filter_status

    # ── CARREGA PRODUTOS ──────────────────────────────────────────────────────
    products = db.get_all_products(filters)

    if not products:
        st.info("🔍 Nenhum produto encontrado com esses filtros. Realize uma busca primeiro ou ajuste os filtros.")
        return

    # ── ESTATÍSTICAS RÁPIDAS ──────────────────────────────────────────────────
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    scores = [p["score"] for p in products if p.get("score")]

    with col_s1:
        st.metric("Total encontrado", len(products))
    with col_s2:
        st.metric("Score médio", f"{sum(scores)/len(scores):.1f}" if scores else "—")
    with col_s3:
        st.metric("Aprovados", sum(1 for p in products if p.get("is_approved")))
    with col_s4:
        st.metric("Score máximo", f"{max(scores):.1f}" if scores else "—")

    st.divider()

    # ── EXPORTAÇÃO ────────────────────────────────────────────────────────────
    st.subheader("📥 Exportar Resultados")
    col_e1, col_e2, col_e3, _ = st.columns([1, 1, 1, 2])

    keyword = st.session_state.get("last_search_keyword", "produtos")

    with col_e1:
        csv_data = exporter.export_to_csv(products)
        st.download_button(
            "⬇️ CSV",
            data=csv_data,
            file_name=exporter.get_export_filename("csv", keyword),
            mime="text/csv",
            use_container_width=True
        )

    with col_e2:
        excel_data = exporter.export_to_excel(products)
        st.download_button(
            "⬇️ Excel",
            data=excel_data,
            file_name=exporter.get_export_filename("excel", keyword),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col_e3:
        json_data = exporter.export_to_json(products)
        st.download_button(
            "⬇️ JSON",
            data=json_data,
            file_name=exporter.get_export_filename("json", keyword),
            mime="application/json",
            use_container_width=True
        )

    st.divider()

    # ── TABELA DE PRODUTOS ────────────────────────────────────────────────────
    st.subheader(f"🛒 Produtos ({len(products)} encontrados)")

    # Renderiza cards individuais
    for product in products:
        _render_product_card(product)


def _render_product_card(product: dict):
    """Renderiza o card expandível de um produto com todas as informações."""

    score = product.get("score", 0) or 0
    decision = product.get("ai_decision", "revisar") or "revisar"
    name = product.get("name", "Produto sem nome")[:80]
    price = product.get("price", 0)
    rating = product.get("rating", 0)
    sales = product.get("sales", 0)
    is_approved = product.get("is_approved", 0)

    score_label, score_color = scoring.get_score_label(score)

    # Ícone de status
    decision_icons = {
        "aprovado": "✅",
        "revisar": "⚠️",
        "rejeitado": "❌"
    }
    decision_icon = decision_icons.get(decision, "⚠️")

    # Header do card (título do expander)
    header = f"{decision_icon} [{score:.0f}] {name} · R$ {price:.2f} · ⭐{rating}"

    with st.expander(header, expanded=False):
        col_left, col_right = st.columns([2, 1])

        with col_left:
            # ── INFORMAÇÕES GERAIS ─────────────────────────────────────────
            st.markdown(f"**Produto:** {product.get('name', '')}")

            info_cols = st.columns(4)
            with info_cols[0]:
                st.markdown(f"**💰 Custo:** R$ {price:.2f}")
            with info_cols[1]:
                suggested = product.get("ai_price_suggestion", 0)
                st.markdown(f"**🏷️ Sugerido:** R$ {suggested:.2f}" if suggested else "**🏷️ Sugerido:** —")
            with info_cols[2]:
                st.markdown(f"**⭐ Avaliação:** {rating}/5")
            with info_cols[3]:
                st.markdown(f"**📦 Vendas:** {sales:,}")

            extra_cols = st.columns(3)
            with extra_cols[0]:
                br = "🇧🇷 Sim" if product.get("ships_from_brazil") else "🌏 Não"
                st.markdown(f"**Envio Brasil:** {br}")
            with extra_cols[1]:
                choice = "✅ Sim" if product.get("choice_badge") else "❌ Não"
                st.markdown(f"**Selo Choice:** {choice}")
            with extra_cols[2]:
                st.markdown(f"**📂 Categoria:** {product.get('category', '—')}")

            # ── TÍTULO SHOPEE ──────────────────────────────────────────────
            if product.get("ai_shopee_title"):
                st.markdown("**🏪 Título Shopee Sugerido:**")
                st.code(product["ai_shopee_title"], language=None)

            # ── LINK ───────────────────────────────────────────────────────
            if product.get("link"):
                st.markdown(f"🔗 [Ver no AliExpress]({product['link']})")

        with col_right:
            # ── SCORE VISUAL ───────────────────────────────────────────────
            st.markdown(f"""
            <div style='text-align: center; background: {score_color}20;
                        border: 2px solid {score_color}; border-radius: 12px;
                        padding: 1rem; margin-bottom: 1rem;'>
                <div style='font-size: 2.5rem; font-weight: 800; color: {score_color};
                            line-height: 1'>{score:.0f}</div>
                <div style='font-size: 0.75rem; color: #666; margin-top: 0.3rem'>/ 100 pts</div>
                <div style='font-size: 0.85rem; font-weight: 600; color: {score_color};
                            margin-top: 0.5rem'>{score_label}</div>
            </div>
            """, unsafe_allow_html=True)

            # ── DECISÃO IA ─────────────────────────────────────────────────
            decision_colors = {
                "aprovado": "#27AE60",
                "revisar": "#F39C12",
                "rejeitado": "#E74C3C"
            }
            d_color = decision_colors.get(decision, "#666")
            st.markdown(f"""
            <div style='text-align: center; background: {d_color}15;
                        border: 1px solid {d_color}; border-radius: 8px;
                        padding: 0.6rem; margin-bottom: 1rem;'>
                <div style='font-size: 0.85rem; color: {d_color}; font-weight: 600;'>
                    {decision_icon} Decisão IA: {decision.upper()}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── BOTÕES DE AÇÃO ─────────────────────────────────────────────
            product_id = product.get("id", "")

            if not is_approved:
                if st.button("✅ Aprovar", key=f"approve_{product_id}", use_container_width=True, type="primary"):
                    if db.approve_product(product_id):
                        st.success("Produto aprovado!")
                        st.rerun()
            else:
                st.success("✅ Aprovado")
                if st.button("❌ Remover Aprovação", key=f"reject_{product_id}", use_container_width=True):
                    if db.reject_product(product_id, "Removido pelo usuário"):
                        st.warning("Aprovação removida")
                        st.rerun()

        # ── ANÁLISE IA DETALHADA (aba expandida) ───────────────────────────
        if any(product.get(k) for k in ["ai_strengths", "ai_weaknesses", "ai_description"]):
            st.divider()
            tab1, tab2, tab3 = st.tabs(["💪 Análise", "📝 Copy", "🎨 Criativos"])

            with tab1:
                col_a, col_b = st.columns(2)
                with col_a:
                    strengths = product.get("ai_strengths", "")
                    if strengths:
                        st.markdown("**✅ Pontos Fortes:**")
                        for point in strengths.split(", "):
                            if point.strip():
                                st.markdown(f"- {point.strip()}")

                    audience = product.get("ai_target_audience", "")
                    if audience:
                        st.markdown(f"**👥 Público-alvo:** {audience}")

                with col_b:
                    weaknesses = product.get("ai_weaknesses", "")
                    if weaknesses:
                        st.markdown("**⚠️ Pontos de Atenção:**")
                        for point in weaknesses.split(", "):
                            if point.strip():
                                st.markdown(f"- {point.strip()}")

                    risk = product.get("ai_risk", "")
                    if risk:
                        st.markdown(f"**🎯 Risco:** {risk}")

            with tab2:
                description = product.get("ai_description", "")
                if description:
                    st.markdown("**📋 Descrição para Shopee (Luna — Copywriter):**")
                    st.text_area("", value=description, height=200, key=f"desc_{product_id}")
                    st.button("📋 Copiar", key=f"copy_desc_{product_id}")

                hashtags = product.get("ai_hashtags", "")
                if hashtags:
                    st.markdown(f"**#️⃣ Hashtags:** {hashtags}")

            with tab3:
                creative_ideas = product.get("ai_creative_ideas", "")
                if creative_ideas:
                    st.markdown("**🎨 Ideias de Criativo (Ariel — Visual Merchandiser):**")
                    for idea in creative_ideas.split(", "):
                        if idea.strip():
                            st.markdown(f"- {idea.strip()}")

        # ── BREAKDOWN DO SCORE ──────────────────────────────────────────────
        breakdown_json = product.get("score_breakdown", "")
        if breakdown_json:
            with st.expander("🔬 Detalhamento do Score", expanded=False):
                from modules.scoring import parse_score_breakdown
                breakdown = parse_score_breakdown(breakdown_json)

                if breakdown:
                    criteria_names = {
                        "price_margin": "Margem de Preço",
                        "rating": "Avaliação",
                        "sales_volume": "Volume de Vendas",
                        "shipping": "Envio",
                        "choice_badge": "Selo Choice",
                        "competition": "Concorrência",
                        "visual_potential": "Potencial Visual",
                        "saturation_risk": "Risco de Saturação",
                    }

                    for key, data in breakdown.items():
                        c_score = data.get("score", 0)
                        c_max = data.get("max", 10)
                        c_detail = data.get("detail", "")
                        pct = c_score / c_max if c_max > 0 else 0
                        label = criteria_names.get(key, key)

                        col_name, col_bar, col_pts = st.columns([2, 4, 1])
                        with col_name:
                            st.markdown(f"<small>{label}</small>", unsafe_allow_html=True)
                        with col_bar:
                            st.progress(pct, text=c_detail)
                        with col_pts:
                            st.markdown(f"<small>**{c_score}/{c_max}**</small>", unsafe_allow_html=True)
