# 🛒 Smart Product Finder

> **Descubra produtos com Demanda Reprimida para Shopee — Powered by IA**

Sistema inteligente de descoberta, análise e priorização de produtos para marketplace e dropshipping. Criado para o time de 4 personas: Cadu (SEO), Ariel (Visual), Luna (Copy) e Enzo (Performance).

---

## 📋 Índice

1. [Instalação](#instalação)
2. [Como rodar](#como-rodar)
3. [Configurar IA real (Anthropic)](#configurar-ia-real)
4. [Ativar Scraper real (AliExpress)](#ativar-scraper-real)
5. [Estrutura do projeto](#estrutura-do-projeto)
6. [Melhorias futuras](#melhorias-futuras)

---

## ⚡ Instalação

### Pré-requisitos
- Python 3.9 ou superior
- pip

### Passo a passo

```bash
# 1. Clone ou extraia o projeto
cd smart_product_finder

# 2. Crie um ambiente virtual (recomendado)
python -m venv venv

# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt
```

---

## 🚀 Como Rodar

```bash
# Na raiz do projeto (onde está app.py)
streamlit run app.py
```

O app abrirá automaticamente em `http://localhost:8501`

### Fluxo de uso:
1. **Dashboard** → veja KPIs e ranking
2. **Nova Busca** → configure palavra-chave e filtros → clique em "Iniciar Busca"
3. **Resultados** → analise produtos, veja score e análise IA, aprove ou rejeite
4. **Aprovados** → produtos prontos para publicação, com copy e título Shopee gerados

---

## 🤖 Configurar IA Real

Por padrão, o sistema usa análise **simulada** (sem custo, sem chave).

Para ativar a IA real com **Claude (Anthropic)**:

### Opção 1: Variável de ambiente (recomendado para produção)
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-SuaChaveAqui"
streamlit run app.py
```

### Opção 2: No formulário de busca
Cole sua chave no campo **"API Key Anthropic"** diretamente na interface.

### Opção 3: Arquivo `.env` (instale python-dotenv)
```bash
pip install python-dotenv
```
Crie `.env` na raiz:
```
ANTHROPIC_API_KEY=sk-ant-api03-SuaChaveAqui
```
Adicione no início de `app.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

**Onde obter a chave:** https://console.anthropic.com

**Custo estimado:** ~$0.003 por análise de produto (claude-sonnet)

---

## 🕷️ Ativar Scraper Real (AliExpress)

Por padrão, o sistema usa **modo demo** com dados simulados realistas.

### Para ativar o scraping real:

```bash
# 1. Instale o Playwright
pip install playwright

# 2. Instale o browser Chromium
playwright install chromium

# 3. Ative o modo real
export SCRAPER_MODE=real
streamlit run app.py
```

### ⚠️ Importante sobre o scraping real:
- O AliExpress usa proteção anti-bot agressiva
- Para uso em produção, considere:
  - **Proxies rotativos** (BrightData, Oxylabs, Smartproxy)
  - **Delays aleatórios** entre requisições
  - **API oficial** do AliExpress (AliExpress Open Platform): https://openapi.aliexpress.com
  - **Serviços de dados** como SerpApi, Apify, ou ScrapingBee

---

## 🗂️ Estrutura do Projeto

```
smart_product_finder/
│
├── app.py                      # Ponto de entrada + roteamento de páginas
├── requirements.txt            # Dependências Python
├── README.md                   # Esta documentação
│
├── database/
│   ├── __init__.py
│   ├── db.py                   # Conexão SQLite + CRUD (todas as entidades)
│   └── schema.sql              # DDL das tabelas
│
├── modules/
│   ├── __init__.py
│   ├── scraper.py              # Coleta de produtos (demo + real Playwright)
│   ├── scoring.py              # Algoritmo de score 0-100 (8 critérios)
│   ├── ai_analyzer.py          # Integração Anthropic + análise simulada
│   ├── exporter.py             # Export CSV / Excel / JSON
│   └── validators.py           # Validação de formulários e dados
│
├── pages/
│   ├── __init__.py
│   ├── dashboard.py            # KPIs, ranking, últimas buscas
│   ├── search_form.py          # Formulário inteligente de busca
│   ├── results.py              # Tabela de resultados + filtros + ações
│   └── approved_products.py    # Pipeline de produtos aprovados
│
└── data/
    ├── demo_products.json       # 10 produtos realistas para modo demo
    └── smart_finder.db          # Banco SQLite (criado automaticamente)
```

---

## 📊 Sistema de Score (0-100)

| Critério | Peso | O que avalia |
|---|---|---|
| Margem de Preço | 25 pts | `((venda - custo - frete) / venda) * 100` |
| Avaliação | 20 pts | Nota de 0 a 5 estrelas |
| Volume de Vendas | 20 pts | Prova social — quantidade de vendas |
| Envio do Brasil | 10 pts | Entrega rápida = menos cancelamentos |
| Concorrência | 10 pts | Baixa = janela de oportunidade |
| Selo Choice | 8 pts | Fornecedor verificado AliExpress |
| Potencial Visual | 4 pts | Categoria + keywords visuais |
| Risco de Saturação | 3 pts | Volume vs. genericidade do nicho |

**Classificação:**
- 🟢 80-100: Excelente
- 🔵 65-79: Bom  
- 🟡 50-64: Regular
- 🟠 35-49: Fraco
- 🔴 0-34: Ruim

---

## 🔮 Melhorias Futuras

### Curto prazo (v1.1)
- [ ] Integração com API oficial do AliExpress
- [ ] Monitoramento de preço (alertas de variação)
- [ ] Histórico de score ao longo do tempo
- [ ] Comparação lado a lado de produtos

### Médio prazo (v2.0)
- [ ] Publicação automática na Shopee via API
- [ ] Geração de imagens com IA (Midjourney / DALL-E)
- [ ] Análise de tendências (Google Trends + TikTok)
- [ ] Dashboard de performance pós-publicação
- [ ] Integração com Enzo Ads (Shopee Ads API)

### Longo prazo (v3.0)
- [ ] Multi-usuário com autenticação
- [ ] Módulo de precificação dinâmica
- [ ] Análise de sentimento de reviews
- [ ] Previsão de demanda com ML
- [ ] App mobile (React Native)

---

## 🐛 Solução de Problemas

**"Module not found"**  
→ Certifique-se de rodar `streamlit run app.py` a partir da raiz do projeto

**"Database not found"**  
→ O banco é criado automaticamente na primeira execução em `data/smart_finder.db`

**"Playwright not found"**  
→ Normal no modo demo. Para scraping real: `pip install playwright && playwright install chromium`

**Export Excel não funciona**  
→ Execute: `pip install openpyxl`

---

## 📄 Licença

Uso interno — Smart Product Finder Team (Cadu, Ariel, Luna, Enzo)
