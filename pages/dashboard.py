"""
Smart Product Finder - Página: Dashboard
Visão geral com KPIs, ranking e últimas buscas.
"""

import streamlit as st
import pandas as pd
from database import db


def render():
    """Renderiza o dashboard principal com métricas e ranking."""

    # ── HEADER ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
                padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem;
                box-shadow: 0 4px 15px rgba(255,107,53,0.3)'>
        <h1 style='color: white; margin: 0; font-size: 2rem;'>🛒 Smart Product Finder</h1>
        <p style='color: rgba(255,255,255,0.85); margin: 0.5rem 0 0 0; font-size: 1rem;'>
            Descubra produtos com Demanda Reprimida para Shopee · Powered by IA
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── MÉTRICAS PRINCIPAIS ──────────────────────────────────────────────────
    stats = db.get_dashboard_stats()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="📦 Produtos Coletados",
            value=stats["total_products"],
            help="Total de produtos analisados no banco de dados"
        )

    with col2:
        st.metric(
            label="✅ Aprovados",
            value=stats["total_approved"],
            delta=f"+{stats['total_approved']}" if stats["total_approved"] > 0 else None,
            delta_color="normal",
            help="Produtos aprovados para publicação"
        )

    with col3:
        st.metric(
            label="❌ Rejeitados",
            value=stats["total_rejected"],
            help="Produtos que não passaram nos critérios"
        )

    with col4:
        st.metric(
            label="🏆 Melhor Score",
            value=f"{stats['best_score']:.0f}/100",
            help="Maior pontuação comercial encontrada"
        )

    with col5:
        st.metric(
            label="🔍 Buscas",
            value=stats["total_searches"],
            help="Total de pesquisas realizadas"
        )

    st.divider()

    # ── LAYOUT PRINCIPAL: RANKING + ÚLTIMAS BUSCAS ─────────────────────────
    col_left, col_right = st.columns([3, 2])

    # ── RANKING DOS MELHORES PRODUTOS ──────────────────────────────────────
    with col_left:
        st.subheader("🏆 Ranking — Top Produtos por Score")

        if stats["top_products"]:
            df_top = pd.DataFrame(stats["top_products"])

            # Renomeia colunas para exibição
            df_display = df_top.rename(columns={
                "name": "Produto",
                "price": "Custo (R$)",
                "rating": "Avaliação",
                "score": "Score",
                "ai_decision": "Decisão IA"
            })

            # Formata valores
            df_display["Custo (R$)"] = df_display["Custo (R$)"].apply(lambda x: f"R$ {x:.2f}")
            df_display["Avaliação"] = df_display["Avaliação"].apply(lambda x: f"{'⭐' * int(x)} {x}")
            df_display["Score"] = df_display["Score"].apply(
                lambda x: f"{'🟢' if x >= 75 else '🟡' if x >= 50 else '🔴'} {x:.0f}"
            )
            df_display["Decisão IA"] = df_display["Decisão IA"].apply(
                lambda x: f"✅ {x}" if x == "aprovado" else f"⚠️ {x}" if x == "revisar" else f"❌ {x}"
            )

            st.dataframe(
                df_display[["Produto", "Score", "Custo (R$)", "Avaliação", "Decisão IA"]],
                use_container_width=True,
                hide_index=True,
                height=220
            )
        else:
            _empty_state(
                "🔍 Nenhum produto analisado ainda",
                "Vá para **Nova Busca** e colete seus primeiros produtos!"
            )

    # ── ÚLTIMAS BUSCAS ──────────────────────────────────────────────────────
    with col_right:
        st.subheader("🕐 Últimas Buscas")

        recent = db.get_recent_searches(limit=6)

        if recent:
            for search in recent:
                with st.container():
                    created = search.get("created_at", "")[:16].replace("T", " ")
                    found = search.get("total_found", 0)
                    approved = search.get("total_approved", 0)

                    st.markdown(f"""
                    <div style='background: #f8f9fa; border-left: 3px solid #FF6B35;
                                padding: 0.6rem 0.8rem; border-radius: 0 8px 8px 0;
                                margin-bottom: 0.5rem;'>
                        <div style='font-weight: 600; color: #333; font-size: 0.9rem;'>
                            🔍 {search.get('keyword', '—')}
                        </div>
                        <div style='color: #666; font-size: 0.75rem; margin-top: 0.2rem;'>
                            {created} · {found} encontrados · {approved} aprovados
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            _empty_state("Nenhuma busca realizada", "Comece pela aba **Nova Busca**")

    st.divider()

    # ── STATUS DO SISTEMA ───────────────────────────────────────────────────
    st.subheader("⚙️ Status do Sistema")

    col_s1, col_s2, col_s3 = st.columns(3)

    from modules.ai_analyzer import get_ai_status
    from modules.scraper import get_scraper_status

    ai_status = get_ai_status()
    scraper_status = get_scraper_status()

    with col_s1:
        status_color = "#27AE60" if ai_status["active"] else "#F39C12"
        st.markdown(f"""
        <div style='background: {status_color}20; border: 1px solid {status_color}40;
                    padding: 1rem; border-radius: 8px; text-align: center;'>
            <div style='font-size: 1.5rem'>🤖</div>
            <div style='font-weight: 600; color: {status_color}'>IA Analyzer</div>
            <div style='font-size: 0.8rem; color: #666; margin-top: 0.3rem'>
                {ai_status["message"].split("—")[0]}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_s2:
        sc_color = "#27AE60" if scraper_status["active"] else "#F39C12"
        st.markdown(f"""
        <div style='background: {sc_color}20; border: 1px solid {sc_color}40;
                    padding: 1rem; border-radius: 8px; text-align: center;'>
            <div style='font-size: 1.5rem'>🕷️</div>
            <div style='font-weight: 600; color: {sc_color}'>Scraper</div>
            <div style='font-size: 0.8rem; color: #666; margin-top: 0.3rem'>
                {scraper_status["message"].split("—")[0]}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_s3:
        st.markdown(f"""
        <div style='background: #2ECC7120; border: 1px solid #2ECC7140;
                    padding: 1rem; border-radius: 8px; text-align: center;'>
            <div style='font-size: 1.5rem'>🗄️</div>
            <div style='font-weight: 600; color: #27AE60'>Banco SQLite</div>
            <div style='font-size: 0.8rem; color: #666; margin-top: 0.3rem'>
                ✅ Operacional · {stats["total_products"]} registros
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── DICA DE INÍCIO RÁPIDO ───────────────────────────────────────────────
    if stats["total_products"] == 0:
        st.info("""
        ### 🚀 Início Rápido
        1. Clique em **🔍 Nova Busca** no menu lateral
        2. Preencha a palavra-chave do produto
        3. Configure os filtros e clique em **Iniciar Busca**
        4. Analise os resultados na aba **📊 Resultados**
        5. Aprove os melhores em **✅ Aprovados**
        """)


def _empty_state(title: str, message: str):
    """Renderiza estado vazio estilizado."""
    st.markdown(f"""
    <div style='text-align: center; padding: 2rem; color: #aaa;
                background: #f8f9fa; border-radius: 8px; border: 1px dashed #ddd;'>
        <div style='font-size: 1.1rem; font-weight: 600; color: #666'>{title}</div>
        <div style='font-size: 0.85rem; margin-top: 0.5rem'>{message}</div>
    </div>
    """, unsafe_allow_html=True)
