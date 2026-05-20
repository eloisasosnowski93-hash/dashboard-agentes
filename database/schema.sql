-- Smart Product Finder v2.0 - Schema do Banco de Dados
-- Inclui: produtos, análises, agentes, integrações de lojas, pedidos

CREATE TABLE IF NOT EXISTS searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    category TEXT,
    min_price REAL DEFAULT 0,
    max_price REAL DEFAULT 0,
    min_rating REAL DEFAULT 0,
    min_sales INTEGER DEFAULT 0,
    ships_from_brazil BOOLEAN DEFAULT FALSE,
    choice_badge BOOLEAN DEFAULT FALSE,
    min_margin REAL DEFAULT 30,
    freight_cost REAL DEFAULT 15,
    target_price REAL DEFAULT 0,
    competition TEXT DEFAULT 'média',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_found INTEGER DEFAULT 0,
    total_approved INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    search_id INTEGER,
    name TEXT NOT NULL,
    link TEXT,
    price REAL,
    rating REAL,
    sales INTEGER,
    delivery_days INTEGER,
    ships_from_brazil BOOLEAN DEFAULT FALSE,
    choice_badge BOOLEAN DEFAULT FALSE,
    image_url TEXT,
    category TEXT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (search_id) REFERENCES searches(id)
);

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL UNIQUE,
    score REAL,
    score_breakdown TEXT,
    ai_potential TEXT,
    ai_target_audience TEXT,
    ai_strengths TEXT,
    ai_weaknesses TEXT,
    ai_risk TEXT,
    ai_price_suggestion REAL,
    ai_shopee_title TEXT,
    ai_description TEXT,
    ai_creative_ideas TEXT,
    ai_hashtags TEXT,
    ai_decision TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Tabela de produtos aprovados com conteúdo gerado pelos agentes
CREATE TABLE IF NOT EXISTS approved_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    analysis_id INTEGER,
    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_by TEXT DEFAULT 'usuario',
    notes TEXT,
    status TEXT DEFAULT 'aprovado',
    -- Conteúdo gerado pelos agentes
    agent_title TEXT,           -- Cadu: título SEO definitivo
    agent_description TEXT,     -- Luna: descrição de conversão
    agent_price REAL,           -- Enzo: preço otimizado
    agent_ad_budget REAL,       -- Enzo: budget sugerido para ads
    agent_keywords TEXT,        -- Cadu: palavras-chave para ads
    agent_creative_brief TEXT,  -- Ariel: brief do criativo
    agent_hashtags TEXT,        -- Luna: hashtags finais
    agent_status TEXT DEFAULT 'pendente', -- pendente / gerado / publicado / erro
    agent_generated_at TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

-- Integrações de lojas
CREATE TABLE IF NOT EXISTS store_integrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    platform TEXT NOT NULL,  -- shopee / dropi / woocommerce / nuvemshop / mercadolivre
    api_key TEXT,
    api_secret TEXT,
    store_url TEXT,
    store_id TEXT,
    access_token TEXT,
    refresh_token TEXT,
    webhook_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_sync TIMESTAMP,
    config_json TEXT,  -- configurações extras em JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Publicações de produtos nas lojas
CREATE TABLE IF NOT EXISTS publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    approved_id INTEGER,
    store_id INTEGER NOT NULL,
    platform_listing_id TEXT,    -- ID do anúncio na plataforma
    platform_listing_url TEXT,   -- URL do anúncio publicado
    status TEXT DEFAULT 'pendente',  -- pendente / publicado / erro / pausado
    published_at TIMESTAMP,
    error_message TEXT,
    views INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (store_id) REFERENCES store_integrations(id)
);

-- Pedidos recebidos via integração
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER,
    publication_id INTEGER,
    product_id TEXT,
    platform_order_id TEXT,
    customer_name TEXT,
    customer_email TEXT,
    quantity INTEGER DEFAULT 1,
    sale_price REAL,
    cost_price REAL,
    profit REAL,
    status TEXT DEFAULT 'novo',  -- novo / processando / enviado / entregue / cancelado
    dropi_order_id TEXT,         -- ID no Dropi se enviado via Dropi
    tracking_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES store_integrations(id)
);

-- Log de atividades dos agentes
CREATE TABLE IF NOT EXISTS agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,   -- cadu / ariel / luna / enzo / sistema
    product_id TEXT,
    action TEXT NOT NULL,
    result TEXT,
    status TEXT DEFAULT 'ok',  -- ok / erro / aviso
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Histórico de decisões
CREATE TABLE IF NOT EXISTS decision_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT,
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_products_search_id ON products(search_id);
CREATE INDEX IF NOT EXISTS idx_analyses_product_id ON analyses(product_id);
CREATE INDEX IF NOT EXISTS idx_approved_product_id ON approved_products(product_id);
CREATE INDEX IF NOT EXISTS idx_publications_product_id ON publications(product_id);
CREATE INDEX IF NOT EXISTS idx_publications_store_id ON publications(store_id);
CREATE INDEX IF NOT EXISTS idx_orders_store_id ON orders(store_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_product_id ON agent_logs(product_id);
