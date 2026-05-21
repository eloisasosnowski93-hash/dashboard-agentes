"""
Smart Product Finder v2.0 - Módulo de Agentes
Cadu (SEO), Ariel (Visual), Luna (Copy), Enzo (Performance)
Cada agente assume sua responsabilidade ao aprovar um produto.
"""

import os
import json
import random
from typing import Optional
from database import db


# ─────────────────────────────────────────────────────────────────────────────
# ORQUESTRADOR PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def run_all_agents(product: dict, api_key: Optional[str] = None) -> dict:
    """
    Executa todos os agentes em sequência ao aprovar um produto.
    Retorna o conteúdo consolidado gerado por todos os agentes.
    """
    product_id = product.get("id", "")
    db.log_agent("sistema", "Iniciando pipeline de agentes", product_id)

    try:
        # Cadu define o SEO e palavras-chave
        cadu_result = agent_cadu(product, api_key)
        db.log_agent("cadu", "Título SEO e keywords gerados", product_id,
                     cadu_result.get("title", "")[:100])

        # Luna escreve a copy de conversão
        luna_result = agent_luna(product, cadu_result, api_key)
        db.log_agent("luna", "Descrição e hashtags criados", product_id,
                     luna_result.get("description", "")[:100])

        # Ariel cria o brief visual
        ariel_result = agent_ariel(product, cadu_result, api_key)
        db.log_agent("ariel", "Brief de criativo gerado", product_id,
                     ariel_result.get("creative_brief", "")[:100])

        # Enzo define preço e orçamento de ads
        enzo_result = agent_enzo(product, api_key)
        db.log_agent("enzo", "Estratégia de preço e ads definida", product_id,
                     f"Preço: R${enzo_result.get('price',0):.2f} | Budget: R${enzo_result.get('ad_budget',0):.2f}")

        # Consolida resultado
        consolidated = {
            "agent_title": cadu_result.get("title", ""),
            "agent_keywords": ", ".join(cadu_result.get("keywords", [])),
            "agent_description": luna_result.get("description", ""),
            "agent_hashtags": " ".join(luna_result.get("hashtags", [])),
            "agent_creative_brief": ariel_result.get("creative_brief", ""),
            "agent_price": enzo_result.get("price", 0),
            "agent_ad_budget": enzo_result.get("ad_budget", 0),
        }

        # Salva no banco
        db.update_approved_agent_content(product_id, consolidated)
        db.log_agent("sistema", "Pipeline concluído com sucesso", product_id, "ok")

        return {"success": True, "content": consolidated}

    except Exception as e:
        db.log_agent("sistema", f"Erro no pipeline: {e}", product_id, str(e), "erro")
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE CADU — SEO & Mercado
# ─────────────────────────────────────────────────────────────────────────────

def agent_cadu(product: dict, api_key: Optional[str] = None) -> dict:
    """
    Cadu mina Demanda Reprimida e define títulos técnicos para o algoritmo da Shopee.
    Gera: título SEO (120 chars), palavras-chave para ads, análise de demanda.
    """
    name = product.get("name", "")
    category = product.get("category", "")
    sales = product.get("sales", 0)

    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if key and key.startswith("sk-ant-"):
        return _cadu_ai(product, key)

    # Simulado
    # Título Shopee otimizado (fórmula: Palavra-Principal + Especificação + Benefício + Prova Social)
    title_parts = [name[:50]]
    if product.get("choice_badge"):
        title_parts.append("Original")
    if product.get("ships_from_brazil"):
        title_parts.append("Envio BR")
    title_parts.append("Alta Qualidade")
    if sales > 5000:
        title_parts.append(f"{sales//1000}k+ Vendas")

    title = " | ".join(title_parts)[:120]

    # Keywords para Shopee Ads (Enzo usará estas)
    base_keywords = _extract_keywords(name, category)
    long_tail = [f"comprar {kw}" for kw in base_keywords[:2]]
    keywords = base_keywords + long_tail

    # Análise de demanda
    demand_level = "alta" if sales > 10000 else "média" if sales > 2000 else "baixa"

    return {
        "title": title,
        "keywords": keywords[:10],
        "demand_level": demand_level,
        "seo_tips": [
            f"Incluir '{base_keywords[0] if base_keywords else name}' no título para ranquear",
            "Primeiras 30 chars são indexadas com peso maior",
            "Categoria correta aumenta impressões em 40%"
        ]
    }


def _cadu_ai(product: dict, api_key: str) -> dict:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"""Você é Cadu, especialista em SEO para Shopee Brasil.
Produto: {product.get('name')} | Categoria: {product.get('category')} | Vendas: {product.get('sales',0):,}
Gere SOMENTE este JSON:
{{"title":"título SEO 120 chars máx para Shopee","keywords":["kw1","kw2","kw3","kw4","kw5","kw6","kw7","kw8"],"demand_level":"alta|média|baixa","seo_tips":["dica1","dica2","dica3"]}}"""
        msg = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=400,
                                     messages=[{"role": "user", "content": prompt}])
        text = msg.content[0].text.strip().strip("```json").strip("```")
        return json.loads(text)
    except Exception:
        return agent_cadu(product, None)


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE LUNA — Copywriter de Conversão
# ─────────────────────────────────────────────────────────────────────────────

def agent_luna(product: dict, cadu_data: dict, api_key: Optional[str] = None) -> dict:
    """
    Luna escreve descrições que quebram objeções e convertem.
    Antecipa dúvidas: material, tamanho, prazo, garantia.
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if key and key.startswith("sk-ant-"):
        return _luna_ai(product, cadu_data, key)

    name = product.get("name", "Produto")
    rating = product.get("rating", 4.5)
    sales = product.get("sales", 0)
    ships_br = product.get("ships_from_brazil", False)
    delivery = product.get("delivery_days", 20)
    category = product.get("category", "")

    # Público por categoria
    audiences = {
        "Organização": "profissionais e estudantes que buscam mais produtividade",
        "Esporte": "atletas amadores e entusiastas de fitness",
        "Casa e Decoração": "pessoas que querem modernizar o lar",
        "Eletrônicos": "jovens antenados em tecnologia",
        "Saúde e Beleza": "quem prioriza autocuidado e bem-estar",
        "Pets": "tutores que amam seus animais",
        "Informática": "gamers e profissionais de home office",
        "Papelaria": "estudantes e amantes de organização",
    }
    audience = audiences.get(category, "consumidores que buscam qualidade e custo-benefício")

    # Objeções por categoria
    objections = {
        "Eletrônicos": "Funciona no Brasil? → Sim, tensão bivolt. Tem garantia? → 30 dias.",
        "Organização": "Qual o material? → Resistente e durável. Qual o tamanho? → Ver fotos.",
        "Saúde e Beleza": "É seguro? → Materiais hipoalergênicos testados. Funciona mesmo? → {sales:,} comprovam.",
        "Pets": "É seguro para animais? → Sim, materiais não-tóxicos aprovados.",
    }
    faq = objections.get(category, "Dúvidas? → Atendimento via chat Shopee em horário comercial.")

    description = f"""✅ {name.upper()} — O favorito de {sales:,} clientes!

Ideal para {audience}, este produto chegou para resolver de vez o problema que você conhece bem.

⭐ **{rating}/5 estrelas** em avaliações verificadas
📦 **{sales:,} pedidos** — prova de que funciona de verdade
{'🇧🇷 **Envio do Brasil** — entrega em até ' + str(delivery) + ' dias úteis' if ships_br else f'🚀 **Entrega em {delivery} dias** — rastreamento incluso'}

🎯 **Para quem é este produto?**
Para {audience} que já perderam tempo com soluções mediocres e buscam algo que realmente entrega.

💡 **O que você recebe:**
→ Produto conforme anunciado, embalado com cuidado
→ Atendimento pós-venda via chat Shopee
→ Satisfação garantida ou devolução sem burocracia

❓ **Perguntas frequentes (Luna responde):**
• {faq}
• Prazo de entrega: {delivery} dias úteis após confirmação do pagamento
• Embalagem: protegida e discreta
• Suporte: chat Shopee, horário comercial, resposta em até 2h

🔥 **Não perca** — preço especial por tempo limitado!"""

    # Hashtags estratégicas
    category_tags = {
        "Organização": ["#organização", "#homeoffice", "#produtividade", "#organized"],
        "Esporte": ["#fitness", "#esporte", "#treino", "#sport"],
        "Casa e Decoração": ["#decoração", "#homedecor", "#casanova", "#home"],
        "Eletrônicos": ["#tech", "#gadget", "#tecnologia", "#eletronicos"],
        "Saúde e Beleza": ["#beleza", "#skincare", "#autocuidado", "#wellness"],
        "Pets": ["#pet", "#cachorro", "#gato", "#petlover"],
        "Informática": ["#gamer", "#setup", "#homeoffice", "#pc"],
        "Papelaria": ["#papelaria", "#estudos", "#journal", "#stationery"],
    }
    base_tags = category_tags.get(category, ["#shopee", "#oferta", "#compras"])
    hashtags = base_tags + ["#fretegrátis", "#shopee", "#melhoresprecos"]

    return {
        "description": description,
        "hashtags": hashtags[:8],
        "cta": f"🛒 Compre agora e receba em {delivery} dias!",
        "objection_handling": [
            "Material e qualidade: conforme especificação técnica e fotos",
            f"Prazo de entrega: {delivery} dias úteis com rastreamento",
            "Garantia: 30 dias — satisfação garantida",
            "Suporte: chat Shopee em horário comercial"
        ]
    }


def _luna_ai(product: dict, cadu_data: dict, api_key: str) -> dict:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"""Você é Luna, copywriter de conversão para Shopee Brasil.
Produto: {product.get('name')} | Avaliação: {product.get('rating')}/5 | Vendas: {product.get('sales',0):,}
Título SEO (Cadu): {cadu_data.get('title','')}
Gere SOMENTE este JSON:
{{"description":"descrição completa quebra-objeções 4-5 parágrafos","hashtags":["#tag1","#tag2","#tag3","#tag4","#tag5","#tag6","#tag7","#tag8"],"cta":"call-to-action 1 linha","objection_handling":["resposta obj1","resposta obj2","resposta obj3","resposta obj4"]}}"""
        msg = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=800,
                                     messages=[{"role": "user", "content": prompt}])
        text = msg.content[0].text.strip().strip("```json").strip("```")
        return json.loads(text)
    except Exception:
        return agent_luna(product, cadu_data, None)


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE ARIEL — Visual Merchandiser
# ─────────────────────────────────────────────────────────────────────────────

def agent_ariel(product: dict, cadu_data: dict, api_key: Optional[str] = None) -> dict:
    """
    Ariel não faz 'arte de Instagram'. Ele cria layouts que geram cliques.
    Gera: brief do criativo, especificações de foto de capa, infográfico.
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if key and key.startswith("sk-ant-"):
        return _ariel_ai(product, cadu_data, key)

    name = product.get("name", "")
    category = product.get("category", "")
    sales = product.get("sales", 0)
    rating = product.get("rating", 4.5)

    # Paletas por categoria
    palettes = {
        "Eletrônicos": "Azul tecnológico (#1a1a2e, #0f3460) + Ciano elétrico (#00b4d8). Fundo escuro.",
        "Casa e Decoração": "Bege quente (#f5e6d3, #d4a373) + Verde sage (#a8c5a0). Fundo neutro.",
        "Saúde e Beleza": "Rosa suave (#ffb3c6, #ff85a1) + Branco puro. Fundo clean.",
        "Esporte": "Preto sólido + Laranja vibrante (#ff6b35). Alto contraste.",
        "Pets": "Amarelo mel (#ffd166) + Laranja suave. Tom amigável e quente.",
        "Organização": "Azul slate (#4a6fa5) + Branco + Cinza claro. Tom profissional.",
        "Papelaria": "Pastel variado (lilás, rosa, verde menta). Tom fofo e organizado.",
        "Informática": "Roxo neon (#9b5de5) + Preto. Estética gamer/tech.",
    }
    palette = palettes.get(category, "Laranja vibrante (#FF6B35) + Branco. Tom energético.")

    creative_brief = f"""🎨 BRIEF DE CRIATIVO — {name[:50]}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📸 FOTO DE CAPA (800x800px):
• Ângulo principal: 3/4 frontal mostrando o produto completo
• Contexto de uso: mostrar o produto sendo utilizado por pessoa real
• Fundo: {'fundo branco limpo' if category in ['Saúde e Beleza', 'Eletrônicos'] else 'ambiente real de uso'}
• Iluminação: luz natural difusa, sem sombras duras
• Destaque: zoom no detalhe que diferencia (qualidade/acabamento)

🎨 PALETA DE CORES:
{palette}

📊 INFOGRÁFICO (1:1 quadrado):
• Card 1: Problema que resolve (ícone grande + texto impactante)
• Card 2: Como funciona (3 passos simples com ícones)
• Card 3: {rating}⭐ / {sales:,} vendas (prova social destacada)
• Card 4: Comparativo Antes x Depois (se aplicável)
• Card 5: Garantia + Entrega (ícones de segurança)

🎬 VÍDEO REEL (9:16, 15-30s):
• 0-3s: Hook — mostrar o PROBLEMA claramente
• 3-10s: Solução — produto em uso resolvendo o problema
• 10-20s: Resultado — antes e depois / reação satisfeita
• 20-30s: CTA — "Link na bio / Shopee" com preço aparecendo

✍️ COPY DE IMAGEM (máx 3 linhas, fonte grande):
Linha 1: "{name[:30]}"
Linha 2: "⭐{rating} · {sales:,} vendas"
Linha 3: "🔥 Aproveite agora"

⚠️ EVITAR: logos de outras marcas, modelos com rostos não-autorizados,
   fundos bagunçados, textos pixelados, emojis em excesso"""

    return {
        "creative_brief": creative_brief,
        "cover_specs": "800x800px, fundo branco ou contextual, produto centralizado",
        "infographic_cards": ["Problema", "Solução", "Prova Social", "Garantia", "CTA"],
        "color_palette": palette,
        "video_structure": "Hook 3s → Demo 10s → Resultado 10s → CTA 7s"
    }


def _ariel_ai(product: dict, cadu_data: dict, api_key: str) -> dict:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"""Você é Ariel, visual merchandiser especializado em Shopee Brasil.
Produto: {product.get('name')} | Categoria: {product.get('category')}
Gere SOMENTE este JSON:
{{"creative_brief":"brief detalhado do criativo","cover_specs":"specs da foto de capa","infographic_cards":["card1","card2","card3","card4","card5"],"color_palette":"paleta de cores descrita","video_structure":"estrutura do vídeo reel"}}"""
        msg = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=600,
                                     messages=[{"role": "user", "content": prompt}])
        text = msg.content[0].text.strip().strip("```json").strip("```")
        return json.loads(text)
    except Exception:
        return agent_ariel(product, cadu_data, None)


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE ENZO — Gestor de Performance
# ─────────────────────────────────────────────────────────────────────────────

def agent_enzo(product: dict, api_key: Optional[str] = None) -> dict:
    """
    Enzo cuida do Shopee Ads e define ROI.
    Gera: preço otimizado, orçamento de ads, estratégia de lances.
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if key and key.startswith("sk-ant-"):
        return _enzo_ai(product, key)

    cost = product.get("price", 10)
    sales = product.get("sales", 0)
    rating = product.get("rating", 4.0)

    # Cálculo de preço otimizado por Enzo
    # Fórmula: Custo × Multiplicador baseado na concorrência e demanda
    if sales > 15000:
        multiplier = 2.8  # produto validado, margem mais apertada OK
    elif sales > 5000:
        multiplier = 3.2
    else:
        multiplier = 3.8  # nicho, margem maior para compensar risco

    suggested_price = round(cost * multiplier, 2)
    # Arredonda para número psicológico (terminando em .90 ou .99)
    base = int(suggested_price)
    suggested_price = base + 0.90 if suggested_price - base < 0.5 else base + 0.99

    margin = round(((suggested_price - cost - 15) / suggested_price) * 100, 1)

    # Orçamento diário de Shopee Ads
    # Regra de Enzo: começar conservador, escalar só com dados
    if margin >= 50:
        ad_budget = round(suggested_price * 0.15, 2)  # 15% do preço para ads
        strategy = "Agressivo — margem alta permite investimento maior"
    elif margin >= 35:
        ad_budget = round(suggested_price * 0.10, 2)  # 10%
        strategy = "Moderado — equilibra custo de aquisição e margem"
    else:
        ad_budget = round(suggested_price * 0.05, 2)  # 5%
        strategy = "Conservador — margem apertada, foco em CPC baixo"

    # ROAS estimado (Return on Ad Spend)
    roas = round(suggested_price / max(ad_budget * 0.3, 1), 1)

    return {
        "price": suggested_price,
        "margin": margin,
        "ad_budget": ad_budget,
        "roas_target": roas,
        "strategy": strategy,
        "bid_recommendation": "CPC automático por 7 dias, depois ajustar por palavra-chave",
        "performance_kpis": [
            f"CTR alvo: >2%",
            f"CPC máximo: R$ {round(ad_budget * 0.3, 2)}",
            f"ROAS mínimo: {roas}x",
            f"Margem após ads: >{margin - 10:.0f}%"
        ]
    }


def _enzo_ai(product: dict, api_key: str) -> dict:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        cost = product.get("price", 10)
        prompt = f"""Você é Enzo, gestor de performance Shopee Ads.
Produto: {product.get('name')} | Custo: R${cost} | Vendas: {product.get('sales',0):,}
Gere SOMENTE este JSON:
{{"price":0.00,"margin":0.0,"ad_budget":0.00,"roas_target":0.0,"strategy":"descrição da estratégia","bid_recommendation":"recomendação de lance","performance_kpis":["kpi1","kpi2","kpi3","kpi4"]}}"""
        msg = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=400,
                                     messages=[{"role": "user", "content": prompt}])
        text = msg.content[0].text.strip().strip("```json").strip("```")
        return json.loads(text)
    except Exception:
        return agent_enzo(product, None)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _extract_keywords(name: str, category: str) -> list:
    """Extrai palavras-chave relevantes do nome e categoria do produto."""
    # Remove palavras genéricas
    stopwords = {"de", "para", "com", "e", "a", "o", "em", "do", "da", "um", "uma"}
    words = [w.lower() for w in name.split() if len(w) > 3 and w.lower() not in stopwords]
    
    category_keywords = {
        "Eletrônicos": ["eletrônico", "tecnologia", "gadget"],
        "Casa e Decoração": ["casa", "decoração", "lar"],
        "Saúde e Beleza": ["beleza", "saúde", "cuidado"],
        "Esporte": ["esporte", "fitness", "treino"],
        "Pets": ["pet", "animal", "cachorro", "gato"],
        "Organização": ["organização", "produtividade"],
        "Informática": ["computador", "setup", "gamer"],
    }
    extra = category_keywords.get(category, [])
    return list(dict.fromkeys(words[:6] + extra))[:8]


def get_agents_status() -> dict:
    """Retorna status dos agentes e última atividade."""
    logs = db.get_agent_logs(limit=20)
    agents = {}
    for log in logs:
        agent = log.get("agent", "")
        if agent not in agents:
            agents[agent] = {
                "last_action": log.get("action", ""),
                "last_status": log.get("status", "ok"),
                "last_at": log.get("created_at", "")[:16]
            }
    return agents
