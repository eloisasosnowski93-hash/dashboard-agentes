"""
Smart Product Finder - Página: Formulário de Busca
Interface para configurar e iniciar uma busca de produtos.
Cadu (SEO) e Enzo (Performance) definiram os campos estratégicos.
"""

import streamlit as st
import uuid
from datetime import datetime

from database import db
from modules import scraper, scoring, ai_analyzer, validators


def render():
    """Renderiza o formulário inteligente de busca."""

    st.header("🔍 Nova Busca de Produtos")
    st.markdown("Configure os parâmetros para minerar produtos com **Demanda Reprimida** na Shopee.")

    # ── STATUS DA IA E SCRAPER ──────────────────────────────────────────────
    ai_status = ai_analyzer.get_ai_status()
    sc_status = scraper.get_scraper_status()

    col_info1, col_info2 = st.columns(2)
    with col_info1:
        if ai_status["active"]:
            st.success(ai_status["message"])
        else:
            st.warning(ai_status["message"])
    with col_info2:
        if sc_status["active"]:
            st.success(sc_status["message"])
        else:
            st.info(sc_status["message"])

    st.divider()

    # ── FORMULÁRIO ─────────────────────────────────────────────────────────
    with st.form("search_form", clear_on_submit=False):

        # ── BLOCO 1: PRODUTO ───────────────────────────────────────────────
        st.markdown("### 🎯 Produto")
        col1, col2 = st.columns([2, 1])
        with col1:
            keyword = st.text_input(
                "Palavra-chave do Produto *",
                placeholder="Ex: organizador de cabos, suporte celular, led noturno...",
                help="Use termos que o comprador digitaria na busca da Shopee"
            )
        with col2:
            category = st.selectbox(
                "Categoria",
                options=[
                    "", "Casa e Decoração", "Eletrônicos", "Moda e Acessórios",
                    "Esporte e Lazer", "Saúde e Beleza", "Pets", "Informática",
                    "Organização", "Papelaria", "Bebês e Crianças", "Automotivo"
                ],
                help="Categoria do produto na Shopee"
            )

        # ── BLOCO 2: FILTROS DE PRODUTO ────────────────────────────────────
        st.markdown("### 💰 Filtros de Produto")
        col3, col4, col5, col6 = st.columns(4)

        with col3:
            min_price = st.number_input(
                "Preço Mínimo (R$)",
                min_value=0.0, max_value=9999.0, value=0.0, step=1.0,
                help="Preço mínimo do produto no AliExpress"
            )
        with col4:
            max_price = st.number_input(
                "Preço Máximo (R$)",
                min_value=0.0, max_value=9999.0, value=100.0, step=1.0,
                help="Preço máximo do produto no AliExpress"
            )
        with col5:
            min_rating = st.slider(
                "Avaliação Mínima ⭐",
                min_value=0.0, max_value=5.0, value=4.0, step=0.1,
                help="Produtos com avaliação menor serão excluídos"
            )
        with col6:
            min_sales = st.number_input(
                "Vendas Mínimas",
                min_value=0, max_value=999999, value=500, step=100,
                help="Prova social mínima exigida"
            )

        col7, col8 = st.columns(2)
        with col7:
            ships_from_brazil = st.checkbox(
                "🇧🇷 Apenas envio do Brasil",
                value=False,
                help="Produtos com envio nacional têm vantagem de entrega na Shopee"
            )
        with col8:
            choice_badge = st.checkbox(
                "✅ Apenas com Selo Choice",
                value=False,
                help="Selo Choice indica fornecedor verificado e qualidade garantida"
            )

        # ── BLOCO 3: ANÁLISE FINANCEIRA ────────────────────────────────────
        st.markdown("### 📊 Análise Financeira (Enzo — ROI)")
        col9, col10, col11 = st.columns(3)

        with col9:
            min_margin = st.number_input(
                "Margem Mínima Desejada (%)",
                min_value=0.0, max_value=100.0, value=40.0, step=5.0,
                help="Margem abaixo deste valor será penalizada no score"
            )
        with col10:
            freight_cost = st.number_input(
                "Custo Estimado de Frete (R$)",
                min_value=0.0, max_value=999.0, value=15.0, step=1.0,
                help="Frete médio que você paga para receber o produto"
            )
        with col11:
            target_price = st.number_input(
                "Preço Pretendido de Venda (R$)",
                min_value=0.0, max_value=9999.0, value=0.0, step=5.0,
                help="Quanto você pretende cobrar na Shopee. Deixe 0 para cálculo automático"
            )

        # ── BLOCO 4: ESTRATÉGIA ────────────────────────────────────────────
        st.markdown("### 🧠 Análise Estratégica (Cadu — SEO)")
        col12, col13 = st.columns([1, 2])

        with col12:
            competition = st.selectbox(
                "Concorrência Percebida",
                options=["baixa", "média", "alta"],
                index=1,
                help="Avalie a quantidade de anúncios similares já existentes na Shopee"
            )

        with col13:
            notes = st.text_area(
                "Observações Estratégicas",
                placeholder="Ex: produto viral no TikTok, sazonalidade no verão, nicho de gamers...",
                height=80,
                help="Contexto adicional que a IA usará para personalizar a análise"
            )

        # ── BLOCO 5: CONFIGURAÇÕES ─────────────────────────────────────────
        st.markdown("### ⚙️ Configurações da Busca")
        col14, col15 = st.columns(2)

        with col14:
            max_results = st.slider(
                "Máximo de Produtos a Coletar",
                min_value=5, max_value=50, value=15, step=5,
                help="Mais produtos = análise mais completa, mas demora mais"
            )

        with col15:
            api_key_input = st.text_input(
                "API Key Anthropic (opcional)",
                type="password",
                placeholder="sk-ant-api03-...",
                help="Cole sua chave para ativar IA real. Deixe vazio para usar análise simulada."
            )

        # ── BOTÃO DE SUBMIT ────────────────────────────────────────────────
        st.divider()
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            submitted = st.form_submit_button(
                "🚀 Iniciar Busca",
                type="primary",
                use_container_width=True
            )
        with col_btn2:
            st.markdown(
                "<div style='padding: 0.6rem 0; color: #666; font-size: 0.85rem;'>"
                "⏱️ A busca demora entre 30 segundos a 2 minutos dependendo da quantidade de produtos."
                "</div>",
                unsafe_allow_html=True
            )

    # ── PROCESSAMENTO DA BUSCA ──────────────────────────────────────────────
    if submitted:
        _process_search(
            keyword=keyword,
            category=category,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            min_sales=min_sales,
            ships_from_brazil=ships_from_brazil if ships_from_brazil else None,
            choice_badge=choice_badge if choice_badge else None,
            min_margin=min_margin,
            freight_cost=freight_cost,
            target_price=target_price,
            competition=competition,
            notes=notes,
            max_results=max_results,
            api_key=api_key_input or None
        )


def _process_search(**params):
    """
    Orquestra o fluxo completo: validação → coleta → score → IA → salvar.
    Exibe progresso em tempo real para o usuário.
    """
    keyword = params.get("keyword", "").strip()

    # ── VALIDAÇÃO ────────────────────────────────────────────────────────────
    is_valid, errors = validators.validate_search_form(params)
    if not is_valid:
        for error in errors:
            st.error(f"❌ {error}")
        return

    # ── FEEDBACK VISUAL ──────────────────────────────────────────────────────
    st.success(f"✅ Iniciando busca por **{keyword}**...")

    progress_bar = st.progress(0, text="Iniciando coleta...")
    status_area = st.empty()
    result_area = st.empty()

    try:
        # ── ETAPA 1: SALVAR BUSCA ───────────────────────────────────────────
        search_id = db.save_search({
            "keyword": keyword,
            "category": params.get("category", ""),
            "min_price": params.get("min_price", 0),
            "max_price": params.get("max_price", 0),
            "min_rating": params.get("min_rating", 0),
            "min_sales": params.get("min_sales", 0),
            "ships_from_brazil": params.get("ships_from_brazil"),
            "choice_badge": params.get("choice_badge"),
            "min_margin": params.get("min_margin", 0),
            "freight_cost": params.get("freight_cost", 0),
            "target_price": params.get("target_price", 0),
            "competition": params.get("competition", "média"),
            "notes": params.get("notes", ""),
        })

        # ── ETAPA 2: COLETAR PRODUTOS ───────────────────────────────────────
        status_area.info("🕷️ Coletando produtos...")

        def update_progress(pct):
            progress_bar.progress(int(pct * 0.4), text=f"Coletando produtos... {int(pct)}%")

        raw_products = scraper.collect_products(
            keyword=keyword,
            category=params.get("category", ""),
            min_price=params.get("min_price", 0),
            max_price=params.get("max_price", 0),
            min_rating=params.get("min_rating", 0),
            min_sales=params.get("min_sales", 0),
            ships_from_brazil=params.get("ships_from_brazil"),
            choice_badge=params.get("choice_badge"),
            max_results=params.get("max_results", 15),
            progress_callback=update_progress
        )

        if not raw_products:
            st.warning("⚠️ Nenhum produto encontrado. Tente ampliar os filtros.")
            return

        status_area.info(f"📊 Calculando scores de {len(raw_products)} produtos...")
        progress_bar.progress(50, text="Calculando scores...")

        # ── ETAPA 3: SCORE + IA POR PRODUTO ────────────────────────────────
        approved_count = 0
        search_params_for_scoring = {
            "target_price": params.get("target_price", 0),
            "freight_cost": params.get("freight_cost", 15),
            "min_margin": params.get("min_margin", 30),
            "competition": params.get("competition", "média"),
        }

        for idx, product in enumerate(raw_products):
            # Valida produto antes de salvar
            is_valid_prod, _ = validators.validate_product_data(product)
            if not is_valid_prod:
                continue

            # Salva produto
            product_id = db.save_product(product, search_id)

            # Calcula score
            score, breakdown = scoring.calculate_score(product, search_params_for_scoring)

            # Análise IA
            ai_result = ai_analyzer.analyze_product_with_ai(
                product,
                {**search_params_for_scoring, "notes": params.get("notes", "")},
                api_key=params.get("api_key")
            )

            # Salva análise completa
            analysis_id = db.save_analysis({
                "product_id": product_id,
                "score": score,
                "score_breakdown": scoring.format_score_breakdown(breakdown),
                "ai_potential": ai_result.get("potential", ""),
                "ai_target_audience": ai_result.get("target_audience", ""),
                "ai_strengths": ", ".join(ai_result.get("strengths", [])),
                "ai_weaknesses": ", ".join(ai_result.get("weaknesses", [])),
                "ai_risk": ai_result.get("risk", ""),
                "ai_price_suggestion": ai_result.get("price_suggestion", 0),
                "ai_shopee_title": ai_result.get("shopee_title", ""),
                "ai_description": ai_result.get("description", ""),
                "ai_creative_ideas": ", ".join(ai_result.get("creative_ideas", [])),
                "ai_hashtags": " ".join(ai_result.get("hashtags", [])),
                "ai_decision": ai_result.get("decision", "revisar"),
            })

            # Auto-aprova se IA recomendou
            if ai_result.get("decision") == "aprovado" and score >= 60:
                db.approve_product(product_id, analysis_id, "Auto-aprovado pelo sistema")
                approved_count += 1

            # Atualiza progresso
            pct = 50 + int((idx + 1) / len(raw_products) * 45)
            progress_bar.progress(pct, text=f"Analisando produto {idx + 1}/{len(raw_products)}...")

        # ── ETAPA 4: ATUALIZAR TOTAIS DA BUSCA ─────────────────────────────
        db.update_search_totals(search_id, len(raw_products), approved_count)

        progress_bar.progress(100, text="✅ Concluído!")
        status_area.empty()

        # ── RESULTADO FINAL ─────────────────────────────────────────────────
        result_area.success(f"""
        ### ✅ Busca Concluída!
        - **{len(raw_products)}** produtos coletados e analisados
        - **{approved_count}** produtos aprovados automaticamente
        - 📊 Veja os resultados na aba **Resultados** no menu lateral
        """)

        # Armazena keyword na session para navegação
        st.session_state["last_search_keyword"] = keyword
        st.session_state["last_search_id"] = search_id

    except Exception as e:
        progress_bar.progress(0)
        status_area.empty()
        st.error(f"❌ Erro durante a busca: {str(e)}")
        st.exception(e)
