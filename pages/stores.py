"""Smart Product Finder v2.0 - Gerenciamento de Lojas e Integrações"""
import streamlit as st
import json
from database import db
from integrations.integrations import get_all_platforms, test_connection, sync_orders


def render():
    st.header("🔗 Lojas & Integrações")
    st.markdown("Conecte suas lojas para publicar produtos e sincronizar pedidos automaticamente.")

    tab_minha, tab_add, tab_plat = st.tabs(["🏪 Minhas Lojas", "➕ Adicionar Loja", "📋 Plataformas"])

    with tab_minha:
        _render_my_stores()

    with tab_add:
        _render_add_store()

    with tab_plat:
        _render_platforms()


def _render_my_stores():
    stores = db.get_store_integrations()
    if not stores:
        st.info("Nenhuma loja conectada ainda. Use a aba **➕ Adicionar Loja** para começar.")
        return

    for store in stores:
        _render_store_card(store)


def _render_store_card(store: dict):
    platform = store.get("platform","")
    store_name = store.get("name","")
    is_active = store.get("is_active", True)
    last_sync = str(store.get("last_sync",""))[:16] or "Nunca"
    store_id = store.get("id")

    icons = {"shopee":"🛍️","dropi":"📦","woocommerce":"🛒","nuvemshop":"☁️","mercadolivre":"🟡","yampi":"🚀"}
    colors = {"shopee":"#EE4D2D","dropi":"#7C3AED","woocommerce":"#96588A","nuvemshop":"#00B1EA","mercadolivre":"#FFE600","yampi":"#F97316"}
    icon = icons.get(platform,"🔗"); color = colors.get(platform,"#666")

    status_label = "🟢 Ativa" if is_active else "🔴 Inativa"

    with st.container():
        st.markdown(f"""
        <div style='border:1px solid {color}40;border-left:4px solid {color};border-radius:8px;
                    padding:1rem;margin-bottom:0.8rem;background:{color}05'>
            <div style='display:flex;align-items:center;gap:0.5rem'>
                <span style='font-size:1.5rem'>{icon}</span>
                <div>
                    <div style='font-size:1rem;font-weight:700;color:#333'>{store_name}</div>
                    <div style='font-size:0.8rem;color:#666'>{platform.title()} · {status_label} · Última sync: {last_sync}</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        bc1,bc2,bc3,bc4,bc5 = st.columns(5)
        with bc1:
            if st.button("🔌 Testar", key=f"test_{store_id}", use_container_width=True):
                with st.spinner("Testando conexão..."):
                    result = test_connection(store)
                    if result["success"]: st.success(result["message"])
                    else: st.error(result["message"])
        with bc2:
            if st.button("🔄 Sync Pedidos", key=f"sync_{store_id}", use_container_width=True):
                with st.spinner("Sincronizando..."):
                    orders = sync_orders(store)
                    st.success(f"✅ {len(orders)} novo(s) pedido(s) sincronizado(s)")
        with bc3:
            toggle_label = "⏹️ Desativar" if is_active else "▶️ Ativar"
            if st.button(toggle_label, key=f"toggle_{store_id}", use_container_width=True):
                db.toggle_store_active(store_id, not is_active)
                st.rerun()
        with bc4:
            if platform == "dropi":
                if st.button("📦 Enviar ao Dropi", key=f"dropi_send_{store_id}", use_container_width=True):
                    st.info("Pedidos aprovados serão enviados ao Dropi para fulfillment.")
        with bc5:
            if st.button("🗑️ Remover", key=f"del_{store_id}", use_container_width=True):
                db.delete_store_integration(store_id)
                st.warning("Loja removida."); st.rerun()

        # Publicações desta loja
        pubs = db.get_publications()
        store_pubs = [p for p in pubs if p.get("store_id") == store_id]
        if store_pubs:
            with st.expander(f"📋 {len(store_pubs)} publicação(ões) nesta loja", expanded=False):
                for pub in store_pubs[:10]:
                    pub_status = pub.get("status","")
                    pub_icon = {"publicado":"✅","pendente":"⏳","erro":"❌"}.get(pub_status,"⏳")
                    url = pub.get("platform_listing_url","")
                    listing_id = pub.get("platform_listing_id","")
                    st.markdown(f"{pub_icon} `{listing_id}` — " +
                                (f"[Ver anúncio ↗]({url})" if url else pub_status))


def _render_add_store():
    st.subheader("➕ Conectar Nova Loja")

    platforms = get_all_platforms()
    available = {k:v for k,v in platforms.items() if v.get("status")=="disponível"}

    platform_choice = st.selectbox(
        "Plataforma",
        options=list(available.keys()),
        format_func=lambda x: f"{available[x]['icon']} {available[x]['name']}"
    )

    if platform_choice:
        pinfo = available[platform_choice]
        st.markdown(f"""
        <div style='background:{pinfo['color']}10;border:1px solid {pinfo['color']}40;
                    border-radius:8px;padding:1rem;margin:0.5rem 0'>
            <b>{pinfo['icon']} {pinfo['name']}</b> — {pinfo['description']}<br>
            <small>📚 <a href='{pinfo['docs_url']}' target='_blank'>Documentação da API ↗</a></small>
        </div>""", unsafe_allow_html=True)

        st.markdown("**Funcionalidades:**")
        for feat in pinfo.get("features",[]):
            st.markdown(f"- ✓ {feat}")

        st.divider()
        st.markdown("**Configurar Credenciais:**")

        with st.form(f"add_store_{platform_choice}"):
            store_name = st.text_input("Nome da Loja *", placeholder=f"Ex: Minha Loja {pinfo['name']}")

            fields = pinfo.get("fields",[])
            field_values = {}

            if platform_choice == "shopee":
                st.info("💡 Obtenha suas credenciais em: https://open.shopee.com/")
                field_values["partner_id"] = st.text_input("Partner ID", placeholder="Número ex: 1234567")
                field_values["partner_key"] = st.text_input("Partner Key", type="password")
                field_values["shop_id"] = st.text_input("Shop ID", placeholder="ID da sua loja")
                field_values["access_token"] = st.text_input("Access Token", type="password")

            elif platform_choice == "dropi":
                st.info("💡 Acesse sua conta Dropi em: https://dropi.com.br → Integrações → API")
                field_values["api_key"] = st.text_input("API Key Dropi *", type="password", placeholder="Sua chave de API")
                field_values["store_id"] = st.text_input("Store ID", placeholder="ID da sua loja no Dropi")

            elif platform_choice == "woocommerce":
                st.info("💡 Gere as chaves em: WP Admin → WooCommerce → Configurações → Avançado → API REST")
                field_values["store_url"] = st.text_input("URL da Loja *", placeholder="https://sualore.com.br")
                field_values["consumer_key"] = st.text_input("Consumer Key *", placeholder="ck_...")
                field_values["consumer_secret"] = st.text_input("Consumer Secret *", type="password", placeholder="cs_...")

            elif platform_choice == "nuvemshop":
                st.info("💡 Acesse: Painel Nuvemshop → Aplicativos → API → Gerar token")
                field_values["store_id"] = st.text_input("Store ID (User ID) *", placeholder="Seu ID na Nuvemshop")
                field_values["access_token"] = st.text_input("Access Token *", type="password")

            webhook_url = st.text_input("Webhook URL (opcional)",
                                         placeholder="https://suaaplicacao.com/webhook",
                                         help="URL para receber notificações de novos pedidos")

            submitted = st.form_submit_button(f"➕ Conectar {pinfo['name']}", type="primary")

        if submitted:
            if not store_name:
                st.error("❌ Nome da loja é obrigatório"); return

            # Determina api_key, secret e access_token baseado na plataforma
            api_key = field_values.get("api_key") or field_values.get("partner_key") or field_values.get("consumer_key","")
            api_secret = field_values.get("consumer_secret") or field_values.get("partner_key","")
            store_url = field_values.get("store_url","")
            store_id_val = field_values.get("store_id") or field_values.get("partner_id","")
            access_token = field_values.get("access_token","")

            if not api_key and not access_token:
                st.error("❌ Forneça ao menos uma credencial (API Key ou Token)"); return

            store_data = {
                "id": None,
                "name": store_name,
                "platform": platform_choice,
                "api_key": api_key,
                "api_secret": api_secret,
                "store_url": store_url,
                "store_id": str(store_id_val),
                "access_token": access_token,
                "webhook_url": webhook_url,
                "is_active": True,
                "config_json": json.dumps(field_values)
            }

            with st.spinner("Testando conexão..."):
                test = test_connection(store_data)

            if test["success"]:
                db.save_store_integration(store_data)
                st.success(f"✅ {pinfo['name']} conectado com sucesso!")
                st.balloons()
                st.rerun()
            else:
                st.error(test["message"])
                st.warning("Verifique suas credenciais e tente novamente.")


def _render_platforms():
    st.subheader("📋 Plataformas Disponíveis")
    platforms = get_all_platforms()

    for platform_id, pinfo in platforms.items():
        status = pinfo.get("status","")
        status_color = "#27AE60" if status == "disponível" else "#F39C12"
        status_label = "✅ Disponível" if status == "disponível" else "🔜 Em Breve"

        st.markdown(f"""
        <div style='border:1px solid {pinfo['color']}30;border-left:4px solid {pinfo['color']};
                    border-radius:8px;padding:1rem;margin-bottom:0.8rem'>
            <div style='display:flex;justify-content:space-between;align-items:center'>
                <div>
                    <span style='font-size:1.3rem'>{pinfo['icon']}</span>
                    <b style='font-size:1rem;color:#333;margin-left:0.5rem'>{pinfo['name']}</b>
                    <span style='color:{status_color};font-size:0.8rem;margin-left:0.5rem'>{status_label}</span>
                </div>
                <a href='{pinfo['docs_url']}' target='_blank' style='font-size:0.8rem;color:#666'>
                    📚 Docs API ↗
                </a>
            </div>
            <div style='color:#555;font-size:0.85rem;margin:0.5rem 0'>{pinfo['description']}</div>
            <div style='font-size:0.8rem;color:#888'>{"  ·  ".join(["✓ " + f for f in pinfo.get("features",[])])}</div>
        </div>""", unsafe_allow_html=True)
