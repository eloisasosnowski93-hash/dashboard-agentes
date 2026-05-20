"""Smart Product Finder v2.0 - Resultados com ativação de agentes ao aprovar"""
import streamlit as st
from database import db
from modules import scoring, exporter


def render():
    st.header("📊 Resultados da Análise")

    with st.expander("🔧 Filtros", expanded=True):
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: f_score = st.number_input("Score Mínimo", 0, 100, 0)
        with c2: f_price = st.number_input("Custo Máx (R$)", 0.0, value=0.0, step=5.0, help="0=sem limite")
        with c3: f_rating = st.number_input("Avaliação Mín", 0.0, 5.0, 0.0, 0.1)
        with c4:
            cats = db.get_categories()
            f_cat = st.selectbox("Categoria", cats)
        with c5:
            f_status = st.selectbox("Status", ["todos","aprovado","rejeitado"],
                                    format_func=lambda x:{"todos":"🔵 Todos","aprovado":"✅ Aprovados","rejeitado":"❌ Rejeitados"}.get(x,x))

    filters = {}
    if f_score > 0: filters["min_score"] = f_score
    if f_price > 0: filters["max_price"] = f_price
    if f_rating > 0: filters["min_rating"] = f_rating
    if f_cat != "Todas": filters["category"] = f_cat
    if f_status != "todos": filters["status"] = f_status

    products = db.get_all_products(filters)
    if not products:
        st.info("🔍 Nenhum produto encontrado. Realize uma busca primeiro ou ajuste os filtros.")
        return

    scores = [p["score"] for p in products if p.get("score")]
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Total", len(products))
    with c2: st.metric("Score médio", f"{sum(scores)/len(scores):.1f}" if scores else "—")
    with c3: st.metric("Aprovados", sum(1 for p in products if p.get("is_approved")))
    with c4: st.metric("Score máx", f"{max(scores):.1f}" if scores else "—")

    st.divider()
    st.subheader("📥 Exportar")
    kw = st.session_state.get("last_search_keyword","produtos")
    ec1,ec2,ec3,_ = st.columns([1,1,1,2])
    with ec1:
        st.download_button("⬇️ CSV", exporter.export_to_csv(products),
                           exporter.get_export_filename("csv",kw), "text/csv", use_container_width=True)
    with ec2:
        st.download_button("⬇️ Excel", exporter.export_to_excel(products),
                           exporter.get_export_filename("excel",kw),
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with ec3:
        st.download_button("⬇️ JSON", exporter.export_to_json(products),
                           exporter.get_export_filename("json",kw), "application/json", use_container_width=True)

    st.divider()
    st.subheader(f"🛒 Produtos ({len(products)})")

    for product in products:
        _render_card(product)


def _render_card(product: dict):
    score = product.get("score", 0) or 0
    decision = product.get("ai_decision","revisar") or "revisar"
    name = product.get("name","Produto")[:80]
    price = product.get("price",0)
    rating = product.get("rating",0)
    sales = product.get("sales",0)
    is_approved = product.get("is_approved",0)
    agent_status = product.get("agent_status","")
    pid = product.get("id","")

    score_label, score_color = scoring.get_score_label(score)
    dec_icon = {"aprovado":"✅","revisar":"⚠️","rejeitado":"❌"}.get(decision,"⚠️")
    header = f"{dec_icon} [{score:.0f}] {name} · R$ {price:.2f} · ⭐{rating}"
    if is_approved and agent_status == "gerado":
        header = "🤖 " + header

    with st.expander(header, expanded=False):
        cl, cr = st.columns([2,1])

        with cl:
            st.markdown(f"**Produto:** {product.get('name','')}")
            ic1,ic2,ic3,ic4 = st.columns(4)
            with ic1: st.markdown(f"**💰 Custo:** R$ {price:.2f}")
            with ic2:
                sug = product.get("ai_price_suggestion",0)
                st.markdown(f"**🏷️ Sugerido:** R$ {sug:.2f}" if sug else "**🏷️ Sugerido:** —")
            with ic3: st.markdown(f"**⭐ Avaliação:** {rating}/5")
            with ic4: st.markdown(f"**📦 Vendas:** {sales:,}")
            ic5,ic6,ic7 = st.columns(3)
            with ic5: st.markdown(f"**🇧🇷 Brasil:** {'Sim' if product.get('ships_from_brazil') else 'Não'}")
            with ic6: st.markdown(f"**Choice:** {'✅' if product.get('choice_badge') else '❌'}")
            with ic7: st.markdown(f"**📂 Cat:** {product.get('category','—')}")

            # Link para o produto no AliExpress
            if product.get("link"):
                st.markdown(f"🔗 [**Ver no AliExpress ↗**]({product['link']})")

            # Título Shopee (agente ou IA)
            title = product.get("agent_title") or product.get("ai_shopee_title","")
            if title:
                st.markdown("**🏪 Título Shopee:**")
                st.code(title, language=None)

        with cr:
            # Score visual
            st.markdown(f"""
            <div style='text-align:center;background:{score_color}20;border:2px solid {score_color};
                        border-radius:12px;padding:0.8rem;margin-bottom:0.8rem'>
                <div style='font-size:2.2rem;font-weight:800;color:{score_color};line-height:1'>{score:.0f}</div>
                <div style='font-size:0.7rem;color:#666'>/100 pts</div>
                <div style='font-size:0.8rem;font-weight:600;color:{score_color};margin-top:0.3rem'>{score_label}</div>
            </div>""", unsafe_allow_html=True)

            # Decisão IA
            dc = {"aprovado":"#27AE60","revisar":"#F39C12","rejeitado":"#E74C3C"}.get(decision,"#666")
            st.markdown(f"""
            <div style='text-align:center;background:{dc}15;border:1px solid {dc};
                        border-radius:8px;padding:0.5rem;margin-bottom:0.8rem'>
                <span style='color:{dc};font-weight:600;font-size:0.82rem'>{dec_icon} {decision.upper()}</span>
            </div>""", unsafe_allow_html=True)

            # Botões de ação
            if not is_approved:
                if st.button("✅ Aprovar + Agentes", key=f"apr_{pid}",
                             use_container_width=True, type="primary"):
                    _approve_with_agents(product)
            else:
                if agent_status == "gerado":
                    st.success("🤖 Conteúdo gerado")
                elif agent_status == "pendente":
                    if st.button("🤖 Ativar Agentes", key=f"agents_{pid}", use_container_width=True):
                        _run_agents(product)
                else:
                    st.success("✅ Aprovado")

                if st.button("❌ Remover", key=f"rej_{pid}", use_container_width=True):
                    db.reject_product(pid, "Removido pelo usuário")
                    st.warning("Removido"); st.rerun()

        # Tabs de análise detalhada
        if any(product.get(k) for k in ["ai_strengths","ai_description","agent_description"]):
            st.divider()
            tab1,tab2,tab3,tab4 = st.tabs(["💪 Análise IA","📝 Copy (Luna)","🎨 Criativos (Ariel)","📊 Score"])

            with tab1:
                ca,cb = st.columns(2)
                with ca:
                    strengths = product.get("ai_strengths","")
                    if strengths:
                        st.markdown("**✅ Pontos Fortes:**")
                        for pt in strengths.split(", "):
                            if pt.strip(): st.markdown(f"- {pt.strip()}")
                    audience = product.get("ai_target_audience","")
                    if audience: st.markdown(f"**👥 Público:** {audience}")
                with cb:
                    weaknesses = product.get("ai_weaknesses","")
                    if weaknesses:
                        st.markdown("**⚠️ Pontos de Atenção:**")
                        for pt in weaknesses.split(", "):
                            if pt.strip(): st.markdown(f"- {pt.strip()}")
                    risk = product.get("ai_risk","")
                    if risk: st.markdown(f"**🎯 Risco:** {risk}")

            with tab2:
                # Prioriza descrição da Luna (agente), depois IA
                desc = product.get("agent_description") or product.get("ai_description","")
                if desc:
                    st.markdown("**📋 Descrição para Shopee:**")
                    st.text_area("", value=desc, height=220, key=f"desc_{pid}")
                hashtags = product.get("agent_hashtags") or product.get("ai_hashtags","")
                if hashtags: st.markdown(f"**#️⃣** {hashtags}")

            with tab3:
                creative = product.get("ai_creative_ideas","")
                if creative:
                    st.markdown("**🎨 Ideias de Criativo:**")
                    for idea in creative.split(", "):
                        if idea.strip(): st.markdown(f"- {idea.strip()}")

            with tab4:
                breakdown_json = product.get("score_breakdown","")
                if breakdown_json:
                    from modules.scoring import parse_score_breakdown
                    bd = parse_score_breakdown(breakdown_json)
                    if bd:
                        names = {"price_margin":"Margem","rating":"Avaliação","sales_volume":"Vendas",
                                 "shipping":"Envio","choice_badge":"Choice","competition":"Concorrência",
                                 "visual_potential":"Visual","saturation_risk":"Saturação"}
                        for key, data in bd.items():
                            cs = data.get("score",0); cm = data.get("max",10)
                            pct = cs/cm if cm > 0 else 0
                            cn,cb2,cp = st.columns([2,4,1])
                            with cn: st.markdown(f"<small>{names.get(key,key)}</small>", unsafe_allow_html=True)
                            with cb2: st.progress(pct, text=data.get("detail",""))
                            with cp: st.markdown(f"<small>**{cs}/{cm}**</small>", unsafe_allow_html=True)


def _approve_with_agents(product: dict):
    """Aprova o produto e imediatamente aciona todos os agentes."""
    pid = product.get("id","")
    with st.spinner("✅ Aprovando e acionando agentes..."):
        db.approve_product(pid, notes="Aprovado com agentes")
        _run_agents(product)


def _run_agents(product: dict):
    """Executa pipeline completo de agentes para um produto."""
    pid = product.get("id","")
    api_key = os.getenv("ANTHROPIC_API_KEY", "") if False else None

    with st.spinner("🤖 Agentes trabalhando..."):
        import os as _os
        api_key = _os.getenv("ANTHROPIC_API_KEY","") or None
        from agents.agents import run_all_agents
        result = run_all_agents(product, api_key)
        if result.get("success"):
            st.success("🤖 Agentes concluíram! Cadu, Luna, Ariel e Enzo geraram o conteúdo.")
            st.rerun()
        else:
            st.error(f"❌ Erro nos agentes: {result.get('error','')}")
