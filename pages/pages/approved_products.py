"""Smart Product Finder v2.0 - Produtos Aprovados com conteúdo dos agentes e publicação"""
import streamlit as st
import pandas as pd
from database import db
from modules import exporter


def render():
    st.header("✅ Produtos Aprovados")
    st.markdown("Conteúdo gerado pelos agentes · Pronto para publicar nas suas lojas")

    approved = db.get_approved_products()
    stores = db.get_store_integrations(active_only=True)

    if not approved:
        st.info("""
        ### 📭 Nenhum produto aprovado ainda
        1. Faça uma busca em **🔍 Nova Busca**
        2. Aprove produtos em **📊 Resultados** (botão "Aprovar + Agentes")
        3. Os agentes Cadu, Luna, Ariel e Enzo geram o conteúdo automaticamente
        """)
        return

    # ── MÉTRICAS ──────────────────────────────────────────────────────────────
    scores = [p.get("score",0) for p in approved if p.get("score")]
    prices = [p.get("price",0) for p in approved if p.get("price")]
    agent_prices = [p.get("agent_price",0) for p in approved if p.get("agent_price")]

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.metric("📦 Total", len(approved))
    with c2: st.metric("🏆 Score Médio", f"{sum(scores)/len(scores):.1f}" if scores else "—")
    with c3: st.metric("💰 Custo Médio", f"R$ {sum(prices)/len(prices):.2f}" if prices else "—")
    with c4: st.metric("🏷️ Venda Média", f"R$ {sum(agent_prices)/len(agent_prices):.2f}" if agent_prices else "—")
    with c5:
        gerados = sum(1 for p in approved if p.get("agent_status") == "gerado")
        st.metric("🤖 Conteúdo Gerado", gerados)

    st.divider()

    # ── AVISO SEM LOJAS ───────────────────────────────────────────────────────
    if not stores:
        st.warning("⚠️ Nenhuma loja conectada. Vá em **🔗 Lojas** para conectar Shopee, Dropi, WooCommerce ou Nuvemshop.")

    # ── EXPORTAÇÃO ────────────────────────────────────────────────────────────
    ec1,ec2,ec3,_ = st.columns([1,1,1,2])
    with ec1:
        st.download_button("⬇️ CSV", exporter.export_to_csv(approved),
                           exporter.get_export_filename("csv","aprovados"), "text/csv", use_container_width=True)
    with ec2:
        st.download_button("⬇️ Excel", exporter.export_to_excel(approved),
                           exporter.get_export_filename("excel","aprovados"),
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with ec3:
        st.download_button("⬇️ JSON", exporter.export_to_json(approved),
                           exporter.get_export_filename("json","aprovados"), "application/json", use_container_width=True)

    st.divider()

    # ── CARDS DE PRODUTOS APROVADOS ───────────────────────────────────────────
    st.subheader("🃏 Produtos Aprovados")
    for p in approved:
        _render_approved_card(p, stores)


def _render_approved_card(product: dict, stores: list):
    name = product.get("name","")
    score = product.get("score",0) or 0
    price = product.get("price",0)
    agent_status = product.get("agent_status","pendente") or "pendente"
    pid = product.get("id","")

    # Ícone de status do agente
    agent_icon = {"gerado":"🤖","publicado":"✅","pendente":"⏳","erro":"❌"}.get(agent_status,"⏳")
    approved_at = str(product.get("approved_at",""))[:16]

    with st.expander(f"{agent_icon} {name[:65]} · Score: {score:.0f}/100 · {agent_status.upper()}", expanded=False):

        # ── CONTEÚDO DOS AGENTES ───────────────────────────────────────────
        if agent_status == "gerado":
            tab_cadu, tab_luna, tab_ariel, tab_enzo, tab_pub = st.tabs(
                ["🔵 Cadu (SEO)", "✍️ Luna (Copy)", "🎨 Ariel (Visual)", "📈 Enzo (Ads)", "🚀 Publicar"])

            with tab_cadu:
                st.markdown("**🏪 Título SEO para Shopee:**")
                title = product.get("agent_title","")
                st.code(title or product.get("ai_shopee_title",""), language=None)
                keywords = product.get("agent_keywords","")
                if keywords:
                    st.markdown("**🔑 Palavras-chave para Ads:**")
                    for kw in keywords.split(", "):
                        if kw.strip(): st.markdown(f"- `{kw.strip()}`")

            with tab_luna:
                desc = product.get("agent_description","")
                if desc:
                    st.markdown("**📋 Descrição de Conversão:**")
                    st.text_area("", value=desc, height=250, key=f"luna_desc_{pid}")
                hashtags = product.get("agent_hashtags","")
                if hashtags: st.markdown(f"**#️⃣ Hashtags:** {hashtags}")

            with tab_ariel:
                brief = product.get("agent_creative_brief","")
                if brief:
                    st.markdown("**🎨 Brief do Criativo:**")
                    st.text_area("", value=brief, height=300, key=f"ariel_brief_{pid}")

            with tab_enzo:
                agent_price = product.get("agent_price",0) or 0
                cost = product.get("price",0) or 0
                ad_budget = product.get("agent_ad_budget",0) or 0
                if agent_price > 0:
                    margin = round(((agent_price - cost - 15) / agent_price) * 100, 1)
                    ec1,ec2,ec3 = st.columns(3)
                    with ec1: st.metric("💰 Custo", f"R$ {cost:.2f}")
                    with ec2: st.metric("🏷️ Preço Enzo", f"R$ {agent_price:.2f}")
                    with ec3: st.metric("📊 Margem", f"{margin:.1f}%")
                    if ad_budget > 0:
                        st.metric("📢 Budget Diário de Ads", f"R$ {ad_budget:.2f}")

            with tab_pub:
                _render_publish_tab(product, stores)

        elif agent_status == "pendente":
            st.info("⏳ Conteúdo ainda não gerado pelos agentes.")
            ca,cb = st.columns(2)
            with ca:
                if st.button("🤖 Gerar Conteúdo Agora", key=f"gen_{pid}", type="primary", use_container_width=True):
                    _run_agents_for(product)
            with cb:
                # Mostra informações básicas enquanto aguarda
                sug = product.get("ai_price_suggestion",0)
                if sug: st.markdown(f"💰 Custo: R${price:.2f} → 🏷️ Sugerido: R${sug:.2f}")
                if product.get("link"): st.markdown(f"🔗 [Ver no AliExpress]({product['link']})")

        elif agent_status == "publicado":
            st.success("✅ Produto publicado nas lojas!")
            pubs = db.get_publications(pid)
            if pubs:
                for pub in pubs:
                    url = pub.get("platform_listing_url","")
                    store_name = pub.get("store_name","")
                    if url: st.markdown(f"🛍️ [{store_name}]({url})")
        else:
            st.error(f"❌ Erro ao gerar conteúdo. Tente novamente.")
            if st.button("🔄 Tentar Novamente", key=f"retry_{pid}"):
                _run_agents_for(product)

        # Info básica + ações
        st.divider()
        ic1,ic2,ic3 = st.columns(3)
        with ic1: st.markdown(f"**📅 Aprovado:** {approved_at}")
        with ic2:
            if product.get("link"): st.markdown(f"**🔗 [Fornecedor AliExpress]({product['link']})**")
        with ic3:
            if st.button("🗑️ Remover Aprovação", key=f"rem_ap_{pid}"):
                db.reject_product(pid, "Removido da lista de aprovados")
                st.warning("Removido"); st.rerun()


def _render_publish_tab(product: dict, stores: list):
    """Tab de publicação do produto nas lojas conectadas."""
    pid = product.get("id","")
    st.markdown("**🚀 Publicar nas Lojas Conectadas:**")

    if not stores:
        st.warning("Nenhuma loja conectada. Configure em **🔗 Lojas**.")
        return

    pubs = db.get_publications(pid)
    published_store_ids = {p.get("store_id") for p in pubs if p.get("status") == "publicado"}

    for store in stores:
        store_id = store.get("id")
        platform = store.get("platform","")
        store_name = store.get("name","")
        platform_icons = {"shopee":"🛍️","dropi":"📦","woocommerce":"🛒","nuvemshop":"☁️","mercadolivre":"🟡"}
        icon = platform_icons.get(platform,"🔗")

        already_pub = store_id in published_store_ids
        pub_for_store = next((p for p in pubs if p.get("store_id")==store_id), None)

        sc1,sc2,sc3 = st.columns([3,2,2])
        with sc1:
            status_text = "✅ Publicado" if already_pub else "⏳ Não publicado"
            st.markdown(f"{icon} **{store_name}** ({platform}) — {status_text}")
            if pub_for_store and pub_for_store.get("platform_listing_url"):
                url = pub_for_store.get("platform_listing_url","")
                st.markdown(f"  → [Ver anúncio ↗]({url})")
        with sc2:
            if not already_pub:
                if st.button(f"📤 Publicar", key=f"pub_{pid}_{store_id}",
                             use_container_width=True, type="primary"):
                    _publish_to_store(product, store)
            else:
                if st.button(f"🔄 Re-publicar", key=f"repub_{pid}_{store_id}", use_container_width=True):
                    _publish_to_store(product, store)
        with sc3:
            if platform == "dropi" and already_pub:
                if st.button("📦 Enviar Pedidos→Dropi", key=f"dropi_{pid}_{store_id}", use_container_width=True):
                    st.info("Pedidos pendentes serão enviados ao Dropi automaticamente.")


def _publish_to_store(product: dict, store: dict):
    """Aciona a publicação em uma loja específica."""
    with st.spinner(f"📤 Publicando em {store.get('name')}..."):
        from integrations.integrations import publish_product
        approved_content = {
            "agent_title": product.get("agent_title",""),
            "agent_description": product.get("agent_description",""),
            "agent_price": product.get("agent_price",0),
            "ap_id": product.get("ap_id")
        }
        result = publish_product(product, approved_content, store)
        if result.get("success"):
            url = result.get("listing_url","")
            st.success(f"✅ Publicado! [Ver anúncio ↗]({url})" if url else "✅ Publicado!")
            st.rerun()
        else:
            st.error(f"❌ Erro: {result.get('error','desconhecido')}")


def _run_agents_for(product: dict):
    """Aciona os agentes para um produto específico."""
    import os as _os
    with st.spinner("🤖 Agentes trabalhando... Cadu → Luna → Ariel → Enzo"):
        api_key = _os.getenv("ANTHROPIC_API_KEY","") or None
        from agents.agents import run_all_agents
        result = run_all_agents(product, api_key)
        if result.get("success"):
            st.success("🤖 Conteúdo gerado por todos os agentes!"); st.rerun()
        else:
            st.error(f"❌ Erro: {result.get('error','')}")
