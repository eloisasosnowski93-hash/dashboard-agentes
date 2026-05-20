"""
Smart Product Finder — app.py
Ponto de entrada principal da aplicação Streamlit.

Execução:
    streamlit run app.py

Arquitetura:
    app.py → router de páginas
    pages/  → módulos de interface
    modules/ → lógica de negócio
    database/ → persistência SQLite
"""

import sys
import os

# Garante que o diretório raiz do projeto está no PYTHONPATH
# Necessário para os imports funcionarem independente de onde o app é rodado
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# ── CONFIGURAÇÃO DA PÁGINA ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Product Finder",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Smart Product Finder v1.0 — Descubra produtos com Demanda Reprimida para Shopee"
    }
)

# ── INICIALIZAÇÃO DO BANCO ────────────────────────────────────────────────────
from database import db

@st.cache_resource
def init_db():
    """Inicializa o banco de dados uma única vez por sessão."""
    db.initialize_database()
    return True

init_db()

# ── IMPORTAÇÕES DAS PÁGINAS ───────────────────────────────────────────────────
from pages import dashboard, search_form, results, approved_products

# ── CSS GLOBAL ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Esconde o header padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Estilo global */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Métricas */
    [data-testid="stMetricValue"] {
        font-size: 1.6rem;
        font-weight: 700;
        color: #FF6B35;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        color: #666;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e8e8e8 !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 0.95rem;
        padding: 0.3rem 0;
    }

    /* Botões primários */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FF6B35, #F7931E);
        border: none;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.2s;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255,107,53,0.4);
    }

    /* Expanders */
    [data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
    }

    /* Progresso */
    .stProgress > div > div {
        background: linear-gradient(90deg, #FF6B35, #F7931E);
    }

    /* Inputs */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        border-radius: 8px;
        border: 1.5px solid #e0e0e0;
        transition: border-color 0.2s;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #FF6B35;
        box-shadow: 0 0 0 2px rgba(255,107,53,0.15);
    }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0 0.5rem;'>
        <div style='font-size: 2.5rem'>🛒</div>
        <div style='font-size: 1.1rem; font-weight: 700; color: #FF6B35;'>
            Smart Product Finder
        </div>
        <div style='font-size: 0.75rem; color: #aaa; margin-top: 0.2rem;'>
            v1.0 · Shopee Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Navegação principal
    page = st.radio(
        "Navegação",
        options=[
            "🏠 Dashboard",
            "🔍 Nova Busca",
            "📊 Resultados",
            "✅ Aprovados",
        ],
        label_visibility="collapsed"
    )

    st.divider()

    # ── PERSONAS ──────────────────────────────────────────────────────────────
    with st.expander("👥 Personas do Time", expanded=False):
        st.markdown("""
        <div style='font-size: 0.8rem; color: #ccc; line-height: 1.6;'>
        🔵 <b>Cadu</b> — SEO & Mercado<br>
        Demanda Reprimida + Títulos Shopee
        <br><br>
        🎨 <b>Ariel</b> — Visual Merchandiser<br>
        Fotos de capa + Infográficos
        <br><br>
        ✍️ <b>Luna</b> — Copywriter<br>
        Descrições + Quebra de objeções
        <br><br>
        📈 <b>Enzo</b> — Performance/Ads<br>
        ROI + Shopee Ads
        </div>
        """, unsafe_allow_html=True)

    # ── STATUS ─────────────────────────────────────────────────────────────────
    from modules.ai_analyzer import get_ai_status
    from modules.scraper import get_scraper_status

    ai_st = get_ai_status()
    sc_st = get_scraper_status()

    st.markdown(f"""
    <div style='font-size: 0.75rem; color: #aaa; margin-top: 0.5rem;'>
        {ai_st["message"]}<br>
        {sc_st["message"]}
    </div>
    """, unsafe_allow_html=True)

# ── ROTEAMENTO ─────────────────────────────────────────────────────────────────
if "🏠 Dashboard" in page:
    dashboard.render()
elif "🔍 Nova Busca" in page:
    search_form.render()
elif "📊 Resultados" in page:
    results.render()
elif "✅ Aprovados" in page:
    approved_products.render()
