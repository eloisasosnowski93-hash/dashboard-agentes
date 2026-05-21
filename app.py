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
from pages import (
        dashboard, 
        search_form, 
        results, 
        approved_products, 
        stores, 
        orders, 
        viability
    )
except Exception as e:
    st.error(f"Erro ao carregar módulos: {e}")
<style>
    #MainMenu{visibility:hidden}footer{visibility:hidden}header{visibility:hidden}
    .main .block-container{padding-top:1rem;padding-bottom:2rem;max-width:1200px}
    [data-testid="stMetricValue"]{font-size:1.5rem;font-weight:700;color:#FF6B35}
    [data-testid="stMetricLabel"]{font-size:0.78rem;color:#666}
    [data-testid="stSidebar"]{background:linear-gradient(180deg,#1a1a2e,#16213e)}
    [data-testid="stSidebar"] *{color:#e8e8e8 !important}
    .stButton>button[kind="primary"]{background:linear-gradient(135deg,#FF6B35,#F7931E);
        border:none;color:white;font-weight:600;border-radius:8px;transition:all .2s}
    .stButton>button[kind="primary"]:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(255,107,53,.4)}
    [data-testid="stExpander"]{border:1px solid #e0e0e0;border-radius:8px;margin-bottom:.4rem}
    .stProgress>div>div{background:linear-gradient(90deg,#FF6B35,#F7931E)}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:1rem 0 .5rem'>
        <div style='font-size:2rem'>🛒</div>
        <div style='font-size:1rem;font-weight:700;color:#FF6B35'>Smart Product Finder</div>
        <div style='font-size:.7rem;color:#aaa;margin-top:.2rem'>v2.1 · MEI + Shopee Intelligence</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

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
