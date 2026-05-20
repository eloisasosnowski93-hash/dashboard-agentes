"""
Smart Product Finder - Módulo de Análise por IA
Luna (Copywriter de Conversão) e Cadu (SEO) alimentam este módulo.

Integração com API Anthropic para análise real.
Em modo demo (sem API key), usa análises simuladas realistas.
"""

import os
import json
import random
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DA API
# Para ativar a IA real, defina a variável de ambiente:
#   export ANTHROPIC_API_KEY="sua-chave-aqui"
# Ou adicione no arquivo .env na raiz do projeto.
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Você é um especialista em dropshipping e marketplace brasileiro (Shopee).
Sua tarefa é analisar produtos para venda online e retornar SOMENTE um JSON válido com a estrutura exata solicitada.
Não adicione texto antes ou depois do JSON. Apenas o JSON puro."""


def analyze_product_with_ai(product: dict, search_params: dict, api_key: Optional[str] = None) -> dict:
    """
    Analisa um produto usando IA (Anthropic) ou simulação.
    
    Args:
        product: Dados do produto
        search_params: Parâmetros da busca original
        api_key: Chave da API Anthropic (opcional, sobrescreve env var)
    
    Returns:
        dict com análise completa do produto
    """
    # Prioridade: argumento > variável de ambiente > modo simulado
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    if key and key.startswith("sk-ant-"):
        return _analyze_with_real_ai(product, search_params, key)
    else:
        return _analyze_simulated(product, search_params)


def _analyze_with_real_ai(product: dict, search_params: dict, api_key: str) -> dict:
    """
    Chama a API Anthropic para análise real do produto.
    Usa o modelo claude-sonnet para equilíbrio entre qualidade e custo.
    """
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        prompt = _build_analysis_prompt(product, search_params)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Remove possíveis backticks de markdown
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        analysis = json.loads(response_text)
        analysis["source"] = "anthropic_api"
        return analysis

    except ImportError:
        # Biblioteca anthropic não instalada
        return {**_analyze_simulated(product, search_params), "source": "simulated_no_lib"}
    except json.JSONDecodeError as e:
        return {**_analyze_simulated(product, search_params), "source": f"simulated_json_error: {e}"}
    except Exception as e:
        return {**_analyze_simulated(product, search_params), "source": f"simulated_error: {e}"}


def _build_analysis_prompt(product: dict, search_params: dict) -> str:
    """Constrói o prompt de análise para a API."""
    return f"""Analise este produto para venda no marketplace Shopee Brasil:

PRODUTO:
- Nome: {product.get('name')}
- Preço de custo (AliExpress): R$ {product.get('price', 0):.2f}
- Avaliação: {product.get('rating', 0)}/5
- Vendas: {product.get('sales', 0):,}
- Prazo de entrega: {product.get('delivery_days', 0)} dias
- Envia do Brasil: {"Sim" if product.get('ships_from_brazil') else "Não"}
- Selo Choice: {"Sim" if product.get('choice_badge') else "Não"}
- Categoria: {product.get('category', 'Não informada')}

CONTEXTO DA BUSCA:
- Preço pretendido de venda: R$ {search_params.get('target_price', 0):.2f}
- Custo de frete estimado: R$ {search_params.get('freight_cost', 0):.2f}
- Concorrência percebida: {search_params.get('competition', 'média')}
- Observações estratégicas: {search_params.get('notes', 'Nenhuma')}

Retorne SOMENTE este JSON (sem markdown, sem texto extra):
{{
  "potential": "alto|médio|baixo",
  "target_audience": "descrição do público-alvo em 1-2 frases",
  "strengths": ["ponto forte 1", "ponto forte 2", "ponto forte 3"],
  "weaknesses": ["ponto fraco 1", "ponto fraco 2"],
  "risk": "baixo|médio|alto — justificativa breve",
  "price_suggestion": 0.00,
  "shopee_title": "título otimizado para SEO Shopee (máx 120 chars)",
  "description": "descrição persuasiva focada em benefícios (3-4 parágrafos)",
  "creative_ideas": ["ideia de criativo 1", "ideia de criativo 2", "ideia de criativo 3"],
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5"],
  "decision": "aprovado|revisar|rejeitado"
}}"""


def _analyze_simulated(product: dict, search_params: dict) -> dict:
    """
    Análise simulada realista para modo demo ou quando sem API key.
    Gera conteúdo dinâmico baseado nos dados reais do produto.
    
    Luna (Copywriter) escreveu os templates de copy abaixo.
    """
    name = product.get("name", "Produto")
    price = product.get("price", 10)
    rating = product.get("rating", 4.0)
    sales = product.get("sales", 0)
    category = product.get("category", "Geral")
    ships_br = product.get("ships_from_brazil", False)
    target_price = search_params.get("target_price", price * 3)
    freight = search_params.get("freight_cost", 15)

    # Calcula margem real
    margin = ((target_price - price - freight) / target_price * 100) if target_price > 0 else 0

    # Determina potencial
    if rating >= 4.7 and sales >= 10000 and margin >= 40:
        potential = "alto"
        decision = "aprovado"
    elif rating >= 4.3 and sales >= 3000 and margin >= 25:
        potential = "médio"
        decision = "aprovado" if margin >= 35 else "revisar"
    else:
        potential = "baixo"
        decision = "revisar" if margin >= 20 else "rejeitado"

    # Públicos-alvo por categoria
    audiences = {
        "Organização": "Profissionais e estudantes que buscam produtividade e organização no home office",
        "Esporte": "Atletas amadores e entusiastas de atividades físicas entre 20-40 anos",
        "Casa e Decoração": "Donas de casa e decoradores DIY que buscam modernizar o lar com bom custo-benefício",
        "Eletrônicos": "Jovens adultos antenados em tecnologia que buscam custo-benefício",
        "Saúde e Beleza": "Mulheres entre 25-45 anos que priorizam bem-estar e autocuidado",
        "Pets": "Tutores de pets entre 25-40 anos que tratam animais como membros da família",
        "Informática": "Gamers, estudantes e profissionais de home office",
        "Papelaria": "Estudantes, professores e entusiastas de journaling e organização",
        "Acessórios": "Jovens adultos que combinam funcionalidade com estilo",
    }
    audience = audiences.get(category, "Consumidores em geral que buscam qualidade e bom preço")

    # Pontos fortes dinâmicos
    strengths = []
    if ships_br:
        strengths.append("🇧🇷 Envio nacional — entrega rápida gera mais confiança e menos cancelamentos")
    if product.get("choice_badge"):
        strengths.append("✅ Selo Choice AliExpress — validação de qualidade reconhecida")
    if sales >= 10000:
        strengths.append(f"📦 {sales:,} vendas — forte prova social que aumenta conversão")
    if rating >= 4.7:
        strengths.append(f"⭐ Avaliação {rating}/5 — clientes satisfeitos, baixo índice de devolução")
    if margin >= 40:
        strengths.append(f"💰 Margem estimada de {margin:.0f}% — excelente retorno sobre investimento")
    if not strengths:
        strengths = ["Produto com preço acessível para entrada no mercado", "Nicho com demanda crescente"]

    # Pontos fracos dinâmicos
    weaknesses = []
    if not ships_br:
        weaknesses.append(f"⏳ Frete internacional ({product.get('delivery_days', 20)} dias) pode gerar reclamações")
    if margin < 30:
        weaknesses.append(f"⚠️ Margem de {margin:.0f}% é apertada — pouco espaço para anúncios pagos")
    if sales < 1000:
        weaknesses.append("📉 Poucas vendas — produto ainda sem validação de mercado")
    if not weaknesses:
        weaknesses = ["Concorrência estabelecida exige diferencial de preço ou atendimento"]

    # Risco
    if decision == "aprovado":
        risk = "baixo — produto validado com boa margem e demanda comprovada"
    elif decision == "revisar":
        risk = "médio — ajustar preço ou estratégia antes de lançar"
    else:
        risk = "alto — margem insuficiente ou demanda não comprovada"

    # Sugestão de preço
    if target_price > 0:
        price_suggestion = round(target_price * 1.05, 2)
    else:
        price_suggestion = round(price * 3.2, 2)

    # Título Shopee otimizado (Cadu - SEO)
    title_templates = [
        f"{name} | Original | Envio Rápido | Alta Qualidade | Shopee",
        f"{name} Premium | Melhor Preço | Frete Grátis | Entrega Rápida",
        f"Kit {name} | Top Venda | Qualidade Premium | Shopee Brasil",
    ]
    shopee_title = random.choice(title_templates)[:120]

    # Descrição (Luna - Copywriter)
    description = f"""✅ **Por que escolher {name}?**
Este produto foi selecionado com critérios rigorosos de qualidade e custo-benefício para você, {audience.split(' que ')[0] if ' que ' in audience else 'consumidor inteligente'}.

🎯 **Benefícios principais:**
Com avaliação de {rating}/5 baseada em {sales:,} vendas, este produto já provou seu valor no mercado. Você terá em mãos um item de qualidade comprovada.

📦 **Entrega e garantia:**
{'Produto enviado do Brasil para entrega ágil.' if ships_br else f'Prazo de entrega estimado: {product.get("delivery_days", 20)} dias úteis.'} Satisfação garantida ou devolução do dinheiro.

❓ **Dúvidas frequentes:**
• Material: conforme especificação técnica do produto
• Tamanho/medidas: disponível nas fotos do anúncio
• Suporte: atendimento via chat Shopee em horário comercial"""

    # Ideias de criativo (Ariel - Visual Merchandiser)
    creative_ideas = [
        f"Foto antes/depois mostrando o problema que {name} resolve",
        f"Vídeo de unboxing com zoom nos detalhes de qualidade e acabamento",
        f"Infográfico comparando {name} com o produto convencional"
    ]

    # Hashtags
    category_hashtags = {
        "Organização": ["#organização", "#homeoffice", "#produtividade"],
        "Esporte": ["#fitness", "#sport", "#saúde"],
        "Casa e Decoração": ["#decoração", "#home", "#casanova"],
        "Eletrônicos": ["#tech", "#gadget", "#eletrônicos"],
        "Saúde e Beleza": ["#beleza", "#cuidados", "#wellness"],
        "Pets": ["#pet", "#cachorro", "#gato"],
    }
    base_tags = category_hashtags.get(category, ["#shopee", "#oferta"])
    hashtags = base_tags + ["#dropshipping", "#fretegrátis", "#promoção"]

    return {
        "potential": potential,
        "target_audience": audience,
        "strengths": strengths[:4],
        "weaknesses": weaknesses[:3],
        "risk": risk,
        "price_suggestion": price_suggestion,
        "shopee_title": shopee_title,
        "description": description,
        "creative_ideas": creative_ideas,
        "hashtags": hashtags[:7],
        "decision": decision,
        "source": "simulated"
    }


def is_ai_configured() -> bool:
    """Verifica se a API da IA está configurada."""
    key = os.getenv("ANTHROPIC_API_KEY", "")
    return bool(key and key.startswith("sk-ant-"))


def get_ai_status() -> dict:
    """Retorna o status atual da integração com IA."""
    if is_ai_configured():
        return {
            "active": True,
            "model": "claude-sonnet-4-20250514",
            "message": "✅ IA Anthropic ativa — análises em tempo real"
        }
    else:
        return {
            "active": False,
            "model": "simulado",
            "message": "⚠️ Modo simulado — configure ANTHROPIC_API_KEY para IA real"
        }
