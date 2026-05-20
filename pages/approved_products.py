"""
Smart Product Finder - Página: Produtos Aprovados
Lista de produtos aprovados para publicação na Shopee.
Ariel e Luna trabalham diretamente com estes produtos para criar anúncios.
"""

import streamlit as st
import pandas as pd
from database import db
from modules import exporter


def render():
    """Renderiza a página de produtos aprovados com pipeline de publicação."""

    st.header("✅ Produtos Aprovados para Publicação")
    st.markdown("Produtos que passaram pelos critérios de score e análise IA. Prontos para ir à Shopee.")

    approved = db.get_approved_products()

    if not approved:
        st.info("""
        ### 📭 Nenhum produto aprovado ainda
        
        Para aprovar produtos:
        1. Realize uma busca em **🔍 Nova Busca**
        2. Os produtos com score alto são auto-aprovados
        3. Você pode aprovar manualmente em **📊 Resultados**
        """)
        return

    # ── MÉTRICAS ──────────────────────────────────────────────────────────────
    scores = [p.get("score", 0) for p in approved if p.get("score")]
    prices = [p.get("price", 0) for p in approved if p.get("price")]
    suggestions = [p.get("ai_price_suggestion", 0) for p in approved if p.get("ai_price_suggestion")]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📦 Total Aprovados", len(approved))
    with col2:
        st.metric("🏆 Score Médio", f"{sum(scores)/len(scores):.1f}" if scores else "—")
    with col3:
        avg_cost = sum(prices) / len(prices) if prices else 0
        st.metric("💰 Custo Médio", f"R$ {avg_cost:.2f}")
    with col4:
        avg_sell = sum(suggestions) / len(suggestions) if suggestions else 0
        st.metric("🏷️ Preço Médio Sugerido", f"R$ {avg_sell:.2f}")

    st.divider()

    # ── EXPORTAÇÃO APROVADOS ───────────────────────────────────────────────────
    col_e1, col_e2, col_e3, _ = st.columns([1, 1, 1, 2])

    with col_e1:
        csv_data = exporter.export_to_csv(approved)
        st.download_button(
            "⬇️ CSV",
            data=csv_data,
            file_name=exporter.get_export_filename("csv", "aprovados"),
            mime="text/csv",
            use_container_width=True
        )

    with col_e2:
        excel_data = exporter.export_to_excel(approved)
        st.download_button(
            "⬇️ Excel",
            data=excel_data,
            file_name=exporter.get_export_filename("excel", "aprovados"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col_e3:
        json_data = exporter.export_to_json(approved)
        st.download_button(
            "⬇️ JSON",
            data=json_data,
            file_name=exporter.get_export_filename("json", "aprovados"),
            mime="application/json",
            use_container_width=True
        )

    st.divider()

    # ── PIPELINE DE PUBLICAÇÃO ─────────────────────────────────────────────────
    st.subheader("🚀 Pipeline de Publicação")

    # Agrupa por status
    status_groups = {}
    for p in approved:
        status = p.get("status", "aprovado")
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(p)

    status_labels = {
        "aprovado": "📋 Fila de Publicação",
        "publicado": "✅ Publicado na Shopee",
        "pausado": "⏸️ Pausado"
    }

    for status, products in status_groups.items():
        st.markdown(f"**{status_labels.get(status, status)}** ({len(products)} produtos)")

        df = _products_to_df(products)
        st.dataframe(df, use_container_width=True, hide_index=True, height=min(len(products) * 38 + 40, 300))

        st.divider()

    # ── CARDS DETALHADOS ───────────────────────────────────────────────────────
    st.subheader("🃏 Cartões de Produto")

    for product in approved:
        _render_approved_card(product)


def _products_to_df(products: list) -> pd.DataFrame:
    """Converte lista de produtos para DataFrame formatado."""
    rows = []
    for p in products:
        cost = p.get("price", 0)
        suggested = p.get("ai_price_suggestion", 0)
        margin = round(((suggested - cost) / suggested * 100), 1) if suggested else 0

        rows.append({
            "Produto": p.get("name", "")[:55],
            "Score": f"{p.get('score', 0) or 0:.0f}",
            "Custo": f"R$ {cost:.2f}",
            "Venda": f"R$ {suggested:.2f}" if suggested else "—",
            "Margem": f"{margin}%" if margin else "—",
            "Aprovado em": str(p.get("approved_at", ""))[:16],
        })
    return pd.DataFrame(rows)


def _render_approved_card(product: dict):
    """Renderiza card detalhado de produto aprovado com copy pronto."""
    name = product.get("name", "Produto")
    score = product.get("score", 0) or 0
    price = product.get("price", 0)
    suggested = product.get("ai_price_suggestion", 0)
    shopee_title = product.get("ai_shopee_title", "Título não gerado")
    approved_at = str(product.get("approved_at", ""))[:16]

    with st.expander(f"✅ {name[:70]} · Score: {score:.0f}/100", expanded=False):
        col1, col2 = st.columns([3, 1])

        with col1:
            # Título Shopee
            st.markdown("**🏪 Título para Shopee:**")
            st.code(shopee_title, language=None)

            # Financeiro
            if suggested:
                margin = round(((suggested - price) / suggested * 100), 1)
                st.markdown(f"""
                💰 **Custo:** R$ {price:.2f} → **Venda:** R$ {suggested:.2f} → **Margem:** {margin:.1f}%
                """)

            # Link
            if product.get("link"):
                st.markdown(f"🔗 [Fornecedor no AliExpress]({product['link']})")

        with col2:
            st.metric("Score", f"{score:.0f}/100")
            st.markdown(f"<small style='color:#666'>Aprovado: {approved_at}</small>", unsafe_allow_html=True)

            # Ação de remover aprovação
            if st.button("🗑️ Remover", key=f"rem_{product.get('id', '')}"):
                if db.reject_product(product.get("id", ""), "Removido pelo usuário"):
                    st.warning("Removido da lista")
                    st.rerun()
