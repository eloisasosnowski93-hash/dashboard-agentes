"""Smart Product Finder v2.0 - Análise por IA (Anthropic ou simulado)"""
import os, json, random
from typing import Optional

SYSTEM_PROMPT = "Especialista em dropshipping Shopee Brasil. Retorne SOMENTE JSON válido, sem markdown."

def analyze_product_with_ai(product: dict, search_params: dict, api_key: Optional[str] = None) -> dict:
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if key and key.startswith("sk-ant-"):
        return _real_ai(product, search_params, key)
    return _simulated(product, search_params)

def _real_ai(product, params, key):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        prompt = f"""Produto: {product.get('name')} | Custo: R${product.get('price',0):.2f}
Rating: {product.get('rating',0)}/5 | Vendas: {product.get('sales',0):,}
Brasil: {'Sim' if product.get('ships_from_brazil') else 'Não'} | Choice: {'Sim' if product.get('choice_badge') else 'Não'}
Preço venda: R${params.get('target_price',0):.2f} | Frete: R${params.get('freight_cost',0):.2f}
Concorrência: {params.get('competition','média')}
Retorne SOMENTE este JSON:
{{"potential":"alto|médio|baixo","target_audience":"público","strengths":["f1","f2","f3"],"weaknesses":["f1","f2"],"risk":"nível — justificativa","price_suggestion":0.00,"shopee_title":"título 120chars","description":"descrição 3 parágrafos","creative_ideas":["i1","i2","i3"],"hashtags":["#t1","#t2","#t3","#t4","#t5"],"decision":"aprovado|revisar|rejeitado"}}"""
        msg = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=1200,
                                     system=SYSTEM_PROMPT, messages=[{"role":"user","content":prompt}])
        text = msg.content[0].text.strip().strip("```json").strip("```")
        r = json.loads(text); r["source"] = "anthropic_api"; return r
    except Exception as e:
        return {**_simulated(product, params), "source": f"simulated_error:{e}"}

def _simulated(product, params):
    name = product.get("name","Produto"); price = product.get("price",10)
    rating = product.get("rating",4.0); sales = product.get("sales",0)
    category = product.get("category","Geral"); ships_br = product.get("ships_from_brazil",False)
    target = params.get("target_price", price*3); freight = params.get("freight_cost",15)
    margin = ((target-price-freight)/target*100) if target > 0 else 0
    potential = "alto" if rating>=4.7 and sales>=10000 and margin>=40 else "médio" if rating>=4.3 and sales>=3000 else "baixo"
    decision = "aprovado" if potential in ["alto"] or (potential=="médio" and margin>=35) else "revisar" if margin>=20 else "rejeitado"
    audiences = {"Organização":"Profissionais e estudantes produtivos","Esporte":"Atletas e entusiastas fitness 20-40 anos",
                 "Casa e Decoração":"Decoradores DIY","Eletrônicos":"Jovens antenados em tech","Saúde e Beleza":"Mulheres 25-45 autocuidado",
                 "Pets":"Tutores que amam pets","Informática":"Gamers e home office","Papelaria":"Estudantes e journaling"}
    audience = audiences.get(category,"Consumidores que buscam qualidade e preço")
    strengths = []
    if ships_br: strengths.append("🇧🇷 Envio nacional — entrega rápida e confiança")
    if product.get("choice_badge"): strengths.append("✅ Selo Choice — qualidade verificada")
    if sales >= 10000: strengths.append(f"📦 {sales:,} vendas — prova social forte")
    if rating >= 4.7: strengths.append(f"⭐ {rating}/5 — baixo índice de devolução")
    if not strengths: strengths = ["Preço acessível para entrada","Nicho com demanda crescente"]
    weaknesses = []
    if not ships_br: weaknesses.append(f"⏳ Frete internacional {product.get('delivery_days',20)}d")
    if margin < 30: weaknesses.append(f"⚠️ Margem {margin:.0f}% apertada")
    if not weaknesses: weaknesses = ["Concorrência estabelecida exige diferencial"]
    risk = "baixo — produto validado" if decision=="aprovado" else "médio — revisar estratégia" if decision=="revisar" else "alto — não recomendado"
    price_sug = round(target*1.05,2) if target > 0 else round(price*3.2,2)
    title = f"{name[:50]} | Original | {'Envio BR' if ships_br else 'Alta Qualidade'} | Shopee"[:120]
    desc = f"""✅ {name} — escolhido por {sales:,} clientes!
Para {audience}: produto selecionado com critérios rigorosos de qualidade.
⭐ {rating}/5 | 📦 {sales:,} vendas | {'🇧🇷 Envio BR' if ships_br else f'🚀 {product.get("delivery_days",20)}d entrega'}
Satisfação garantida ou devolução do dinheiro."""
    tags = {"Organização":["#organização","#homeoffice","#produtividade"],"Esporte":["#fitness","#sport","#treino"],
            "Casa e Decoração":["#decoração","#home","#casanova"],"Eletrônicos":["#tech","#gadget","#tecnologia"]}
    hashtags = tags.get(category,["#shopee","#oferta"]) + ["#fretegrátis","#promoção","#compras"]
    return {"potential":potential,"target_audience":audience,"strengths":strengths[:4],"weaknesses":weaknesses[:3],
            "risk":risk,"price_suggestion":price_sug,"shopee_title":title,"description":desc,
            "creative_ideas":[f"Foto antes/depois de {name}","Vídeo unboxing com zoom qualidade","Infográfico vs concorrente"],
            "hashtags":hashtags[:7],"decision":decision,"source":"simulated"}

def is_ai_configured():
    k = os.getenv("ANTHROPIC_API_KEY",""); return bool(k and k.startswith("sk-ant-"))

def get_ai_status():
    if is_ai_configured():
        return {"active":True,"model":"claude-sonnet-4-20250514","message":"✅ IA Anthropic ativa — análises em tempo real"}
    return {"active":False,"model":"simulado","message":"⚠️ Modo simulado — configure ANTHROPIC_API_KEY para IA real"}
