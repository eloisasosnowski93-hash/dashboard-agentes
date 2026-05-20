"""Smart Product Finder v2.0 - Formulário de Busca"""
import streamlit as st
from database import db
from modules import scraper, scoring, ai_analyzer, validators


def render():
    st.header("🔍 Nova Busca de Produtos")
    st.markdown("Configure os parâmetros para minerar produtos com **Demanda Reprimida** na Shopee.")

    ai_status = ai_analyzer.get_ai_status()
    sc_status = scraper.get_scraper_status()
    c1,c2 = st.columns(2)
    with c1:
        if ai_status["active"]: st.success(ai_status["message"])
        else: st.warning(ai_status["message"])
    with c2:
        if sc_status["active"]: st.success(sc_status["message"])
        else: st.info(sc_status["message"])

    st.divider()

    # Preenche campos se for repetição de busca
    repeat = st.session_state.pop("repeat_search", None)

    with st.form("search_form"):
        st.markdown("### 🎯 Produto")
        c1,c2 = st.columns([2,1])
        with c1:
            keyword = st.text_input("Palavra-chave *", value=repeat.get("keyword","") if repeat else "",
                                    placeholder="Ex: organizador cabos, suporte celular, led noturno...")
        with c2:
            cat_opts = ["","Casa e Decoração","Eletrônicos","Moda e Acessórios","Esporte e Lazer",
                        "Saúde e Beleza","Pets","Informática","Organização","Papelaria","Bebês","Automotivo"]
            category = st.selectbox("Categoria", options=cat_opts)

        st.markdown("### 💰 Filtros")
        c3,c4,c5,c6 = st.columns(4)
        with c3: min_price = st.number_input("Preço Mín (R$)", min_value=0.0, value=0.0, step=1.0)
        with c4: max_price = st.number_input("Preço Máx (R$)", min_value=0.0, value=100.0, step=1.0)
        with c5: min_rating = st.slider("Avaliação Mín ⭐", 0.0, 5.0, 4.0, 0.1)
        with c6: min_sales = st.number_input("Vendas Mín", min_value=0, value=500, step=100)
        c7,c8 = st.columns(2)
        with c7: ships_br = st.checkbox("🇧🇷 Apenas envio do Brasil")
        with c8: choice_badge = st.checkbox("✅ Apenas Selo Choice")

        st.markdown("### 📊 Financeiro (Enzo — ROI)")
        c9,c10,c11 = st.columns(3)
        with c9: min_margin = st.number_input("Margem Mín (%)", 0.0, 100.0, 40.0, 5.0)
        with c10: freight_cost = st.number_input("Custo Frete (R$)", 0.0, 999.0, 15.0, 1.0)
        with c11: target_price = st.number_input("Preço de Venda (R$)", 0.0, 9999.0, 0.0, 5.0,
                                                   help="Deixe 0 para cálculo automático")

        st.markdown("### 🧠 Estratégia (Cadu — SEO)")
        c12,c13 = st.columns([1,2])
        with c12: competition = st.selectbox("Concorrência", ["baixa","média","alta"], index=1)
        with c13: notes = st.text_area("Observações", placeholder="Ex: viral no TikTok, sazonalidade...", height=70)

        st.markdown("### ⚙️ Configurações")
        c14,c15 = st.columns(2)
        with c14: max_results = st.slider("Máx Produtos", 5, 50, 15, 5)
        with c15: api_key_input = st.text_input("API Key Anthropic (opcional)", type="password",
                                                  placeholder="sk-ant-api03-...")

        st.divider()
        cb1,cb2 = st.columns([1,3])
        with cb1: submitted = st.form_submit_button("🚀 Iniciar Busca", type="primary", use_container_width=True)
        with cb2: st.markdown("<div style='padding:0.6rem;color:#666;font-size:0.85rem'>⏱️ Demora 30s–2min dependendo da quantidade</div>",unsafe_allow_html=True)

    if submitted:
        _process(keyword=keyword, category=category, min_price=min_price, max_price=max_price,
                 min_rating=min_rating, min_sales=min_sales, ships_from_brazil=ships_br or None,
                 choice_badge=choice_badge or None, min_margin=min_margin, freight_cost=freight_cost,
                 target_price=target_price, competition=competition, notes=notes,
                 max_results=max_results, api_key=api_key_input or None)


def _process(**params):
    keyword = params.get("keyword","").strip()
    is_valid, errors = validators.validate_search_form(params)
    if not is_valid:
        for e in errors: st.error(f"❌ {e}")
        return

    st.success(f"✅ Iniciando busca por **{keyword}**...")
    bar = st.progress(0, text="Iniciando...")
    status = st.empty(); result = st.empty()

    try:
        search_id = db.save_search({
            "keyword":keyword,"category":params.get("category",""),
            "min_price":params.get("min_price",0),"max_price":params.get("max_price",0),
            "min_rating":params.get("min_rating",0),"min_sales":params.get("min_sales",0),
            "ships_from_brazil":params.get("ships_from_brazil"),
            "choice_badge":params.get("choice_badge"),
            "min_margin":params.get("min_margin",0),"freight_cost":params.get("freight_cost",0),
            "target_price":params.get("target_price",0),"competition":params.get("competition","média"),
            "notes":params.get("notes","")})

        status.info("🕷️ Coletando produtos...")
        def upd(pct): bar.progress(int(pct*0.4), text=f"Coletando... {int(pct)}%")

        from modules import scraper as sc
        raw = sc.collect_products(keyword=keyword, category=params.get("category",""),
                                   min_price=params.get("min_price",0), max_price=params.get("max_price",0),
                                   min_rating=params.get("min_rating",0), min_sales=params.get("min_sales",0),
                                   ships_from_brazil=params.get("ships_from_brazil"),
                                   choice_badge=params.get("choice_badge"),
                                   max_results=params.get("max_results",15), progress_callback=upd)

        if not raw:
            st.warning("⚠️ Nenhum produto encontrado. Amplie os filtros."); return

        status.info(f"📊 Analisando {len(raw)} produtos...")
        bar.progress(50, text="Calculando scores...")

        sp = {"target_price":params.get("target_price",0),"freight_cost":params.get("freight_cost",15),
              "min_margin":params.get("min_margin",30),"competition":params.get("competition","média")}

        approved_count = 0
        from modules import scoring as sc_mod, ai_analyzer, validators as val
        for idx, product in enumerate(raw):
            ok, _ = val.validate_product_data(product)
            if not ok: continue
            pid = db.save_product(product, search_id)
            score, breakdown = sc_mod.calculate_score(product, sp)
            ai_r = ai_analyzer.analyze_product_with_ai(product, {**sp,"notes":params.get("notes","")},
                                                        api_key=params.get("api_key"))
            analysis_id = db.save_analysis({
                "product_id":pid,"score":score,
                "score_breakdown":sc_mod.format_score_breakdown(breakdown),
                "ai_potential":ai_r.get("potential",""),"ai_target_audience":ai_r.get("target_audience",""),
                "ai_strengths":", ".join(ai_r.get("strengths",[])),"ai_weaknesses":", ".join(ai_r.get("weaknesses",[])),
                "ai_risk":ai_r.get("risk",""),"ai_price_suggestion":ai_r.get("price_suggestion",0),
                "ai_shopee_title":ai_r.get("shopee_title",""),"ai_description":ai_r.get("description",""),
                "ai_creative_ideas":", ".join(ai_r.get("creative_ideas",[])),"ai_hashtags":" ".join(ai_r.get("hashtags",[])),
                "ai_decision":ai_r.get("decision","revisar")})
            if ai_r.get("decision")=="aprovado" and score>=60:
                db.approve_product(pid, analysis_id, "Auto-aprovado")
                approved_count += 1
            pct = 50 + int((idx+1)/len(raw)*45)
            bar.progress(pct, text=f"Produto {idx+1}/{len(raw)}...")

        db.update_search_totals(search_id, len(raw), approved_count)
        bar.progress(100, text="✅ Concluído!")
        status.empty()
        result.success(f"""### ✅ Busca Concluída!
- **{len(raw)}** produtos coletados
- **{approved_count}** aprovados automaticamente
- Veja em **📊 Resultados** no menu""")
        st.session_state["last_search_keyword"] = keyword
        st.session_state["last_search_id"] = search_id

    except Exception as e:
        bar.progress(0); status.empty()
        st.error(f"❌ Erro: {e}"); st.exception(e)
