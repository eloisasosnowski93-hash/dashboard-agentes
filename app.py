"""
Smart Product Finder v2.0 — app.py
Ponto de entrada principal.

Novidades v2.0:
- Agentes IA (Cadu, Luna, Ariel, Enzo) geram conteúdo ao aprovar
- Integrações de lojas: Shopee, Dropi, WooCommerce, Nuvemshop
- Publicação automática de produtos
- Gestão de pedidos e fulfillment via Dropi
- Dashboard com links clicáveis e log de agentes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="Smart Product Finder v2",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Smart Product Finder v2.0 — Shopee Intelligence + Agentes IA"}
)

# ── INIT DB ───────────────────────────────────────────────────────────────────
from database import db

@st.cache_resource
def init_db():
    db.initialize_database()
    return True

init_db()

# ── IMPORTS ───────────────────────────────────────────────────────────────────
from pages import dashboard, search_form, results, approved_products, stores, orders

# ── CSS GLOBAL ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    #MainMenu {visibility:hidden;}
    footer {visibility:hidden;}
    header {visibility:hidden;}
    .main .block-container {padding-top:1rem;padding-bottom:2rem;max-width:1200px}
    [data-testid="stMetricValue"] {font-size:1.5rem;font-weight:700;color:#FF6B35}
    [data-testid="stMetricLabel"] {font-size:0.78rem;color:#666}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#1a1a2e,#16213e)}
    [data-testid="stSidebar"] * {color:#e8e8e8 !important}
    .stButton>button[kind="primary"] {
        background:linear-gradient(135deg,#FF6B35,#F7931E);border:none;
        color:white;font-weight:600;border-radius:8px;transition:all .2s
    }
    .stButton>button[kind="primary"]:hover {transform:translateY(-1px);box-shadow:0 4px 12px rgba(255,107,53,.4)}
    [data-testid="stExpander"] {border:1px solid #e0e0e0;border-radius:8px;margin-bottom:0.4rem}
    .stProgress>div>div {background:linear-gradient(90deg,#FF6B35,#F7931E)}
</style>""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:1rem 0 0.5rem'>
        <div style='font-size:2rem'>🛒</div>
        <div style='font-size:1rem;font-weight:700;color:#FF6B35'>Smart Product Finder</div>
        <div style='font-size:0.7rem;color:#aaa;margin-top:0.2rem'>v2.0 · Shopee Intelligence</div>
    </div>""", unsafe_allow_html=True)

    st.divider()

    # Navegação
    if "nav" not in st.session_state:
        st.session_state["nav"] = "🏠 Dashboard"

    nav_options = [
        "🏠 Dashboard",
        "🔍 Nova Busca",
        "📊 Resultados",
        "✅ Aprovados",
        "🔗 Lojas",
        "📦 Pedidos",
    ]

    # Permite navegação programática (ex: botão Ver no dashboard)
    current_nav = st.session_state.get("nav", "🏠 Dashboard")
    nav_index = nav_options.index(current_nav) if current_nav in nav_options else 0

    page = st.radio("", options=nav_options, index=nav_index, label_visibility="collapsed")
    st.session_state["nav"] = page

    st.divider()

    # Agentes
    with st.expander("👥 Agentes do Time", expanded=False):
        st.markdown("""
        <div style='font-size:0.78rem;color:#ccc;line-height:1.7'>
        🔵 <b>Cadu</b> — SEO & Mercado<br>
        <span style='color:#aaa;font-size:0.72rem'>Demanda Reprimida · Título Shopee · Keywords</span><br><br>
        🎨 <b>Ariel</b> — Visual Merchandiser<br>
        <span style='color:#aaa;font-size:0.72rem'>Brief Criativo · Foto de Capa · Infográfico</span><br><br>
        ✍️ <b>Luna</b> — Copywriter<br>
        <span style='color:#aaa;font-size:0.72rem'>Descrição · Quebra de Objeções · Hashtags</span><br><br>
        📈 <b>Enzo</b> — Performance<br>
        <span style='color:#aaa;font-size:0.72rem'>Preço Otimizado · Shopee Ads · ROI</span>
        </div>""", unsafe_allow_html=True)

    # Status rápido
    from modules.ai_analyzer import get_ai_status
    from modules.scraper import get_scraper_status
    ai_st = get_ai_status()
    sc_st = get_scraper_status()
    stores_active = db.get_store_integrations(active_only=True)

    st.markdown(f"""
    <div style='font-size:0.72rem;color:#aaa;margin-top:0.5rem;line-height:1.8'>
        {'✅' if ai_st['active'] else '⚠️'} IA: {'Anthropic' if ai_st['active'] else 'Simulada'}<br>
        {'🔴' if sc_st['active'] else '🟡'} Scraper: {sc_st['mode'].title()}<br>
        🔗 Lojas: {len(stores_active)} ativa(s)
    </div>""", unsafe_allow_html=True)

# ── ROTEAMENTO ─────────────────────────────────────────────────────────────────
if "🏠 Dashboard" in page:
    dashboard.render()
elif "🔍 Nova Busca" in page:
    search_form.render()
elif "📊 Resultados" in page:
    results.render()
elif "✅ Aprovados" in page:
    approved_products.render()
elif "🔗 Lojas" in page:
    stores.render()
elif "📦 Pedidos" in page:
    orders.render()
