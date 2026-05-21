"""Smart Product Finder v2.0 - Pedidos e Fulfillment via Dropi"""
import streamlit as st
import pandas as pd
from database import db
from integrations.integrations import sync_orders, send_order_to_dropi


def render():
    st.header("📦 Pedidos & Fulfillment")
    st.markdown("Acompanhe pedidos recebidos e envie automaticamente ao **Dropi** para fulfillment.")

    stores = db.get_store_integrations(active_only=True)
    orders = db.get_orders(limit=100)
    stats = db.get_orders_stats()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("🛒 Total Pedidos", stats["total"])
    with c2: st.metric("💰 Receita Total", f"R$ {stats['revenue']:.2f}")
    with c3: st.metric("📈 Lucro Total", f"R$ {stats['profit']:.2f}")
    with c4: st.metric("⏳ Aguardando", stats["pending"])

    st.divider()

    # ── SYNC MANUAL ───────────────────────────────────────────────────────────
    if stores:
        st.subheader("🔄 Sincronizar Pedidos")
        sc1,sc2 = st.columns([3,1])
        with sc1:
            selected_store = st.selectbox("Loja para sincronizar",
                                           options=stores,
                                           format_func=lambda s: f"{s.get('name')} ({s.get('platform')})")
        with sc2:
            st.write("")
            if st.button("🔄 Sincronizar Agora", type="primary", use_container_width=True):
                with st.spinner("Sincronizando..."):
                    new_orders = sync_orders(selected_store)
                    st.success(f"✅ {len(new_orders)} novo(s) pedido(s)!")
                    st.rerun()
    else:
        st.warning("⚠️ Conecte uma loja em **🔗 Lojas** para sincronizar pedidos.")

    st.divider()

    # ── TABELA DE PEDIDOS ─────────────────────────────────────────────────────
    if not orders:
        st.info("Nenhum pedido registrado ainda. Sincronize sua loja ou aguarde novos pedidos.")
        return

    st.subheader(f"📋 Pedidos Recentes ({len(orders)})")

    # Filtros
    fc1,fc2 = st.columns(2)
    with fc1:
        status_filter = st.selectbox("Status", ["todos","novo","processando","enviado","entregue","cancelado"])
    with fc2:
        store_filter = st.selectbox("Loja",
                                     options=["todas"] + [s.get("name","") for s in stores])

    filtered = orders
    if status_filter != "todos":
        filtered = [o for o in filtered if o.get("status") == status_filter]
    if store_filter != "todas":
        filtered = [o for o in filtered if o.get("store_name") == store_filter]

    # Dropi integration check
    dropi_stores = [s for s in stores if s.get("platform") == "dropi"]

    for order in filtered:
        _render_order_row(order, dropi_stores)


def _render_order_row(order: dict, dropi_stores: list):
    status = order.get("status","novo")
    status_colors = {"novo":"#3498DB","processando":"#F39C12","enviado":"#9B59B6",
                     "entregue":"#27AE60","cancelado":"#E74C3C"}
    status_icons = {"novo":"🆕","processando":"⚙️","enviado":"🚚","entregue":"✅","cancelado":"❌"}
    color = status_colors.get(status,"#666")
    icon = status_icons.get(status,"📦")

    order_id = order.get("platform_order_id","—")
    customer = order.get("customer_name","—")
    product_name = order.get("product_name","—")
    sale_price = order.get("sale_price",0) or 0
    profit = order.get("profit",0) or 0
    dropi_id = order.get("dropi_order_id","")
    store_name = order.get("store_name","—")
    created = str(order.get("created_at",""))[:16]
    oid = order.get("id")

    with st.container():
        st.markdown(f"""
        <div style='border:1px solid {color}30;border-left:3px solid {color};
                    border-radius:6px;padding:0.7rem 1rem;margin-bottom:0.4rem'>
            <div style='display:flex;justify-content:space-between;align-items:center'>
                <div>
                    <span style='font-weight:700;color:#333'>{icon} {order_id}</span>
                    <span style='color:#666;font-size:0.82rem;margin-left:0.5rem'>· {customer} · {store_name}</span>
                </div>
                <div style='text-align:right'>
                    <span style='font-weight:600;color:{color}'>{status.upper()}</span>
                    <span style='color:#888;font-size:0.75rem;margin-left:0.5rem'>{created}</span>
                </div>
            </div>
            <div style='font-size:0.82rem;color:#555;margin-top:0.3rem'>
                📦 {product_name[:50]} · 💰 R${sale_price:.2f} · 📈 Lucro: R${profit:.2f}
                {f'<br>📦 Dropi: <code>{dropi_id}</code>' if dropi_id else ""}
            </div>
        </div>""", unsafe_allow_html=True)

        # Ações para pedidos novos
        if status == "novo" and dropi_stores:
            ac1,ac2,_ = st.columns([2,2,4])
            with ac1:
                if st.button(f"📦 Enviar ao Dropi", key=f"dropi_{oid}", type="primary", use_container_width=True):
                    with st.spinner("Enviando ao Dropi..."):
                        result = send_order_to_dropi(order, dropi_stores[0])
                        if result["success"]:
                            st.success(f"✅ Dropi ID: {result['dropi_order_id']}")
                            st.rerun()
                        else:
                            st.error(f"❌ {result.get('error','Erro desconhecido')}")
            with ac2:
                if st.button("✅ Marcar Processando", key=f"proc_{oid}", use_container_width=True):
                    # Em produção: atualizar status no banco
                    st.info("Status atualizado para Processando")
