"""
Smart Product Finder v2.0 - Dashboard
KPIs, ranking clicável, últimas buscas, status do sistema, pedidos recentes.
"""
import streamlit as st
import pandas as pd
from database import db


def render():
    # ── HEADER ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='background:linear-gradient(135deg,#FF6B35,#F7931E);padding:1.5rem 2rem;
                border-radius:12px;margin-bottom:1.5rem;box-shadow:0 4px 15px rgba(255,107,53,0.3)'>
        <h1 style='color:white;margin:0;font-size:1.8rem'>🛒 Smart Product Finder v2.0</h1>
        <p style='color:rgba(255,255,255,0.85);margin:0.3rem 0 0;font-size:0.95rem'>
            Descubra · Analise · Publique · Automatize — Shopee Intelligence + Agentes IA
        </p>
    </div>""", unsafe_allow_html=True)

    stats = db.get_dashboard_stats()

    # ── KPIs LINHA 1 ──────────────────────────────────────────────────────────
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: st.metric("📦 Produtos", stats["total_products"])
    with c2: st.metric("✅ Aprovados", stats["total_approved"])
    with c3: st.metric("🏆 Melhor Score", f"{stats['best_score']:.0f}")
    with c4: st.metric("🔍 Buscas", stats["total_searches"])
    with c5: st.metric("🛍️ Publicados", stats["total_publications"])
    with c6: st.metric("🔗 Lojas", stats["total_stores"])

    # ── KPIs LINHA 2 - PEDIDOS ────────────────────────────────────────────────
    orders = stats["orders"]
    if orders["total"] > 0:
        oc1,oc2,oc3,oc4 = st.columns(4)
        with oc1: st.metric("🛒 Pedidos", orders["total"])
        with oc2: st.metric("💰 Receita", f"R$ {orders['revenue']:.2f}")
        with oc3: st.metric("📈 Lucro", f"R$ {orders['profit']:.2f}")
        with oc4: st.metric("⏳ Novos", orders["pending"])

    st.divider()

    # ── RANKING + ÚLTIMAS BUSCAS ──────────────────────────────────────────────
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.subheader("🏆 Top Produtos por Score")
        top = stats.get("top_products", [])
        if top:
            for p in top:
                score = p.get("score", 0) or 0
                decision = p.get("ai_decision", "revisar") or "revisar"
                dec_icon = {"aprovado":"✅","revisar":"⚠️","rejeitado":"❌"}.get(decision,"⚠️")
                score_color = "#27AE60" if score>=75 else "#F39C12" if score>=50 else "#E74C3C"
                name = p.get("name","")[:55]
                pid = p.get("id","")
                
                col_info, col_score, col_btn = st.columns([5,2,2])
                with col_info:
                    st.markdown(f"""
                    <div style='padding:0.4rem 0'>
                        <div style='font-size:0.85rem;font-weight:600;color:#333'>{dec_icon} {name}</div>
                        <div style='font-size:0.75rem;color:#888'>R$ {p.get('price',0):.2f} · ⭐{p.get('rating',0)}</div>
                    </div>""", unsafe_allow_html=True)
                with col_score:
                    st.markdown(f"""
                    <div style='text-align:center;background:{score_color}20;border:1px solid {score_color};
                                border-radius:8px;padding:0.3rem;margin-top:0.3rem'>
                        <span style='font-weight:700;color:{score_color};font-size:1.1rem'>{score:.0f}</span>
                        <span style='font-size:0.65rem;color:#888'>/100</span>
                    </div>""", unsafe_allow_html=True)
                with col_btn:
                    if st.button("🔍 Ver", key=f"dash_view_{pid}", use_container_width=True):
                        st.session_state["goto_product"] = pid
                        st.session_state["nav"] = "📊 Resultados"
                        st.rerun()
        else:
            st.info("🔍 Realize uma busca para ver o ranking aqui.")

    with col_r:
        st.subheader("🕐 Últimas Buscas")
        recent = db.get_recent_searches(limit=6)
        if recent:
            for s in recent:
                created = str(s.get("created_at",""))[:16].replace("T"," ")
                kw = s.get("keyword","—")
                found = s.get("total_found",0); appr = s.get("total_approved",0)
                col_s1, col_s2 = st.columns([4,1])
                with col_s1:
                    st.markdown(f"""
                    <div style='background:#f8f9fa;border-left:3px solid #FF6B35;
                                padding:0.5rem 0.8rem;border-radius:0 8px 8px 0;margin-bottom:0.4rem'>
                        <div style='font-weight:600;color:#333;font-size:0.85rem'>🔍 {kw}</div>
                        <div style='color:#888;font-size:0.72rem'>{created} · {found} produtos · {appr} aprovados</div>
                    </div>""", unsafe_allow_html=True)
                with col_s2:
                    if st.button("↻", key=f"repeat_{s.get('id')}", help="Repetir busca"):
                        st.session_state["repeat_search"] = s
                        st.session_state["nav"] = "🔍 Nova Busca"
                        st.rerun()
        else:
            st.info("Nenhuma busca realizada. Comece pela aba **Nova Busca**.")

    st.divider()

    # ── STATUS DO SISTEMA ─────────────────────────────────────────────────────
    st.subheader("⚙️ Status do Sistema")
    from modules.ai_analyzer import get_ai_status
    from modules.scraper import get_scraper_status
    from agents.agents import get_agents_status

    ai_st = get_ai_status()
    sc_st = get_scraper_status()
    agents_st = get_agents_status()

    s1,s2,s3,s4 = st.columns(4)
    def status_card(col, icon, label, msg, active):
        color = "#27AE60" if active else "#F39C12"
        col.markdown(f"""
        <div style='background:{color}15;border:1px solid {color}40;padding:0.8rem;
                    border-radius:8px;text-align:center'>
            <div style='font-size:1.4rem'>{icon}</div>
            <div style='font-weight:600;color:{color};font-size:0.85rem'>{label}</div>
            <div style='font-size:0.72rem;color:#666;margin-top:0.2rem'>{msg}</div>
        </div>""", unsafe_allow_html=True)

    with s1: status_card(s1,"🤖","IA Anthropic",
                         "Ativa" if ai_st["active"] else "Modo Simulado", ai_st["active"])
    with s2: status_card(s2,"🕷️","Scraper",
                         "Real (AliExpress)" if sc_st["active"] else "Demo", sc_st["active"])
    with s3:
        stores = db.get_store_integrations(active_only=True)
        status_card(s3,"🔗","Lojas",
                    f"{len(stores)} conectada(s)" if stores else "Nenhuma", len(stores)>0)
    with s4:
        status_card(s4,"🗄️","Banco SQLite",
                    f"{stats['total_products']} registros", True)

    # ── LOG DE AGENTES RECENTE ────────────────────────────────────────────────
    logs = db.get_agent_logs(limit=8)
    if logs:
        st.divider()
        st.subheader("🤖 Atividade Recente dos Agentes")
        agent_icons = {"cadu":"🔵","ariel":"🎨","luna":"✍️","enzo":"📈","sistema":"⚙️"}
        for log in logs:
            agent = log.get("agent","sistema")
            icon = agent_icons.get(agent,"⚙️")
            status_color = "#27AE60" if log.get("status")=="ok" else "#E74C3C"
            time_str = str(log.get("created_at",""))[:16].replace("T"," ")
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:0.5rem;padding:0.3rem 0;
                        border-bottom:1px solid #f0f0f0;font-size:0.82rem'>
                <span>{icon}</span>
                <span style='color:#666;min-width:80px'><b>{agent.upper()}</b></span>
                <span style='flex:1;color:#333'>{log.get("action","")}</span>
                <span style='color:#888;font-size:0.72rem'>{time_str}</span>
                <span style='color:{status_color}'>●</span>
            </div>""", unsafe_allow_html=True)

    # ── INÍCIO RÁPIDO ─────────────────────────────────────────────────────────
    if stats["total_products"] == 0:
        st.divider()
        st.info("""
        ### 🚀 Início Rápido
        1. **🔍 Nova Busca** → busque produtos no AliExpress (modo demo ativo)
        2. **📊 Resultados** → analise scores e decisões dos agentes
        3. **✅ Aprovados** → agentes geram conteúdo e publicam automaticamente
        4. **🔗 Lojas** → conecte Shopee, Dropi, WooCommerce ou Nuvemshop
        5. **📦 Pedidos** → acompanhe vendas e envie ao Dropi para fulfillment
        """)
