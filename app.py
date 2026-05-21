import sys
import os
import streamlit as st

# Adiciona a raiz do projeto ao PATH do Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
"""
Smart Product Finder v2.1 — app.py
Adicionado: Análise de Viabilidade Enterprise (tab nova)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st

st.set_page_config(
    page_title="Smart Product Finder v2",
    page_icon="🛒", layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Smart Product Finder v2.1 — Shopee + Viabilidade MEI"}
)

from database import db

@st.cache_resource
def init_db():
    db.initialize_database()
    return True
init_db()

try:
    from pages import dashboard, search_form, results, approved_products, stores, orders, viability
except Exception as e:
    st.error(f"Erro ao importar módulos: {e}")

with st.sidebar:
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    [data-testid="stMetricValue"] {font-size: 1.5rem; font-weight: 700;}
</style>
""", unsafe_allow_html=True)
    if "nav" not in st.session_state:
        st.session_state["nav"] = "🏠 Dashboard"

    nav_options = [
        "🏠 Dashboard",
        "📐 Viabilidade",
        "🔍 Nova Busca",
        "📊 Resultados",
        "✅ Aprovados",
        "🔗 Lojas",
        "📦 Pedidos",
    ]
    current = st.session_state.get("nav","🏠 Dashboard")
    idx = nav_options.index(current) if current in nav_options else 0
    page = st.radio("", nav_options, index=idx, label_visibility="collapsed")
    st.session_state["nav"] = page
    st.divider()

    with st.expander("👥 Agentes", expanded=False):
        st.markdown("""
        <div style='font-size:.78rem;color:#ccc;line-height:1.7'>
        🔵 <b>Cadu</b> — SEO & Mercado<br>
        🎨 <b>Ariel</b> — Visual Merchandiser<br>
        ✍️ <b>Luna</b> — Copywriter<br>
        📈 <b>Enzo</b> — Performance Ads
        </div>""", unsafe_allow_html=True)

    from modules.ai_analyzer import get_ai_status
    from modules.scraper import get_scraper_status
    from modules.shopee_api import get_shopee_status
    ai_st = get_ai_status()
    sc_st = get_scraper_status()
    sp_st = get_shopee_status()
    stores_active = db.get_store_integrations(active_only=True)
    st.markdown(f"""
    <div style='font-size:.72rem;color:#aaa;line-height:1.8'>
        {'✅' if ai_st['active'] else '⚠️'} IA: {'Anthropic' if ai_st['active'] else 'Simulada'}<br>
        {'🔴' if sc_st['active'] else '🟡'} Scraper: {sc_st['mode'].title()}<br>
        {'✅' if sp_st['configured'] else '⚠️'} Shopee: {'Configurada' if sp_st['configured'] else 'Não config.'}<br>
        🔗 Lojas: {len(stores_active)} ativa(s)
    </div>""", unsafe_allow_html=True)

if "🏠 Dashboard" in page:       dashboard.render()
elif "📐 Viabilidade" in page:   viability.render()
elif "🔍 Nova Busca" in page:    search_form.render()
elif "📊 Resultados" in page:    results.render()
elif "✅ Aprovados" in page:     approved_products.render()
elif "🔗 Lojas" in page:         stores.render()
elif "📦 Pedidos" in page:       orders.render()
