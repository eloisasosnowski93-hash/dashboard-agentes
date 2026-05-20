-- Smart Product Finder - Schema do Banco de Dados
-- Criado para suportar todas as funcionalidades do MVP

-- Tabela de buscas realizadas
CREATE TABLE IF NOT EXISTS searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    category TEXT,
    min_price REAL,
    max_price REAL,
    min_rating REAL,
    min_sales INTEGER,
    ships_from_brazil BOOLEAN,
    choice_badge BOOLEAN,
    min_margin REAL,
    freight_cost REAL,
    target_price REAL,
    competition TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_found INTEGER DEFAULT 0,
    total_approved INTEGER DEFAULT 0
);

-- Tabela de produtos coletados
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

-- Tabela de análises (score + IA)
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    score REAL,
    score_breakdown TEXT,  -- JSON com detalhes do score
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
    ai_decision TEXT,  -- aprovado / revisar / rejeitado
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Tabela de produtos aprovados
CREATE TABLE IF NOT EXISTS approved_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    analysis_id INTEGER,
    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_by TEXT DEFAULT 'usuario',
    notes TEXT,
    status TEXT DEFAULT 'aprovado',  -- aprovado / publicado / pausado
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

-- Tabela de histórico de decisões
CREATE TABLE IF NOT EXISTS decision_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    decision TEXT NOT NULL,  -- aprovado / rejeitado / revisado
    reason TEXT,
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_products_search_id ON products(search_id);
CREATE INDEX IF NOT EXISTS idx_analyses_product_id ON analyses(product_id);
CREATE INDEX IF NOT EXISTS idx_approved_product_id ON approved_products(product_id);
CREATE INDEX IF NOT EXISTS idx_decision_product_id ON decision_history(product_id);
