"""
Smart Product Finder v2.0 - Módulo de Banco de Dados
CRUD completo para produtos, agentes, integrações, publicações e pedidos.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "smart_finder.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        if SCHEMA_PATH.exists():
            conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        else:
            raise FileNotFoundError(f"Schema não encontrado: {SCHEMA_PATH}")


# ── BUSCAS ────────────────────────────────────────────────────────────────────

def save_search(params: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO searches (keyword,category,min_price,max_price,min_rating,
               min_sales,ships_from_brazil,choice_badge,min_margin,freight_cost,
               target_price,competition,notes)
               VALUES (:keyword,:category,:min_price,:max_price,:min_rating,
               :min_sales,:ships_from_brazil,:choice_badge,:min_margin,:freight_cost,
               :target_price,:competition,:notes)""", params)
        return cur.lastrowid


def update_search_totals(search_id: int, total_found: int, total_approved: int):
    with get_connection() as conn:
        conn.execute("UPDATE searches SET total_found=?,total_approved=? WHERE id=?",
                     (total_found, total_approved, search_id))


def get_recent_searches(limit: int = 10) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM searches ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


# ── PRODUTOS ──────────────────────────────────────────────────────────────────

def save_product(product: dict, search_id: int) -> str:
    with get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO products
               (id,search_id,name,link,price,rating,sales,delivery_days,
                ships_from_brazil,choice_badge,image_url,category,collected_at)
               VALUES (:id,:search_id,:name,:link,:price,:rating,:sales,:delivery_days,
               :ships_from_brazil,:choice_badge,:image_url,:category,:collected_at)""",
            {**product, "search_id": search_id})
        return product["id"]


def get_all_products(filters: dict = None) -> list:
    query = """
        SELECT p.*, a.score, a.ai_decision, a.ai_shopee_title, a.ai_price_suggestion,
               a.score_breakdown, a.ai_strengths, a.ai_weaknesses, a.ai_description,
               a.ai_creative_ideas, a.ai_hashtags, a.ai_target_audience, a.ai_risk,
               ap.id as ap_id, ap.status as approval_status, ap.agent_status,
               ap.agent_title, ap.agent_description, ap.agent_price,
               CASE WHEN ap.id IS NOT NULL THEN 1 ELSE 0 END as is_approved
        FROM products p
        LEFT JOIN analyses a ON p.id = a.product_id
        LEFT JOIN approved_products ap ON p.id = ap.product_id
        WHERE 1=1"""
    params = []
    if filters:
        if filters.get("min_score"):
            query += " AND a.score >= ?"; params.append(filters["min_score"])
        if filters.get("max_price"):
            query += " AND p.price <= ?"; params.append(filters["max_price"])
        if filters.get("min_rating"):
            query += " AND p.rating >= ?"; params.append(filters["min_rating"])
        if filters.get("category") and filters["category"] != "Todas":
            query += " AND p.category = ?"; params.append(filters["category"])
        if filters.get("status") == "aprovado":
            query += " AND ap.id IS NOT NULL"
        elif filters.get("status") == "rejeitado":
            query += " AND ap.id IS NULL AND a.ai_decision = 'rejeitado'"
    query += " ORDER BY COALESCE(a.score,0) DESC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_product_by_id(product_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            """SELECT p.*, a.score, a.score_breakdown, a.ai_decision, a.ai_potential,
               a.ai_target_audience, a.ai_strengths, a.ai_weaknesses, a.ai_risk,
               a.ai_price_suggestion, a.ai_shopee_title, a.ai_description,
               a.ai_creative_ideas, a.ai_hashtags,
               ap.agent_title, ap.agent_description, ap.agent_price,
               ap.agent_keywords, ap.agent_creative_brief, ap.agent_hashtags,
               ap.agent_ad_budget, ap.agent_status, ap.id as ap_id
               FROM products p
               LEFT JOIN analyses a ON p.id = a.product_id
               LEFT JOIN approved_products ap ON p.id = ap.product_id
               WHERE p.id = ?""", (product_id,)).fetchone()
        return dict(row) if row else None


def get_total_products() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]


# ── ANÁLISES ──────────────────────────────────────────────────────────────────

def save_analysis(analysis: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT OR REPLACE INTO analyses
               (product_id,score,score_breakdown,ai_potential,ai_target_audience,
                ai_strengths,ai_weaknesses,ai_risk,ai_price_suggestion,ai_shopee_title,
                ai_description,ai_creative_ideas,ai_hashtags,ai_decision)
               VALUES (:product_id,:score,:score_breakdown,:ai_potential,:ai_target_audience,
               :ai_strengths,:ai_weaknesses,:ai_risk,:ai_price_suggestion,:ai_shopee_title,
               :ai_description,:ai_creative_ideas,:ai_hashtags,:ai_decision)""", analysis)
        return cur.lastrowid


def get_best_score() -> float:
    with get_connection() as conn:
        result = conn.execute("SELECT MAX(score) FROM analyses").fetchone()
        return result[0] or 0.0


# ── APROVAÇÕES ────────────────────────────────────────────────────────────────

def approve_product(product_id: str, analysis_id: int = None, notes: str = "") -> bool:
    try:
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM approved_products WHERE product_id=?", (product_id,)).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO approved_products (product_id,analysis_id,notes) VALUES (?,?,?)",
                    (product_id, analysis_id, notes))
            conn.execute(
                "INSERT INTO decision_history (product_id,decision,reason) VALUES (?,'aprovado',?)",
                (product_id, notes))
        return True
    except Exception as e:
        print(f"Erro ao aprovar: {e}"); return False


def reject_product(product_id: str, reason: str = "") -> bool:
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM approved_products WHERE product_id=?", (product_id,))
            conn.execute(
                "INSERT INTO decision_history (product_id,decision,reason) VALUES (?,'rejeitado',?)",
                (product_id, reason))
        return True
    except Exception as e:
        print(f"Erro ao rejeitar: {e}"); return False


def get_approved_products() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT p.*, a.score, a.ai_shopee_title, a.ai_price_suggestion, a.ai_decision,
               ap.id as ap_id, ap.approved_at, ap.notes as approval_notes, ap.status,
               ap.agent_title, ap.agent_description, ap.agent_price, ap.agent_keywords,
               ap.agent_creative_brief, ap.agent_hashtags, ap.agent_ad_budget, ap.agent_status,
               ap.agent_generated_at
               FROM approved_products ap
               JOIN products p ON ap.product_id = p.id
               LEFT JOIN analyses a ON p.id = a.product_id
               ORDER BY ap.approved_at DESC""").fetchall()
        return [dict(r) for r in rows]


def get_total_approved() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM approved_products").fetchone()[0]


def update_approved_agent_content(product_id: str, content: dict) -> bool:
    """Atualiza o conteúdo gerado pelos agentes para um produto aprovado."""
    try:
        with get_connection() as conn:
            conn.execute(
                """UPDATE approved_products SET
                   agent_title=:agent_title, agent_description=:agent_description,
                   agent_price=:agent_price, agent_ad_budget=:agent_ad_budget,
                   agent_keywords=:agent_keywords, agent_creative_brief=:agent_creative_brief,
                   agent_hashtags=:agent_hashtags, agent_status='gerado',
                   agent_generated_at=CURRENT_TIMESTAMP
                   WHERE product_id=:product_id""",
                {**content, "product_id": product_id})
        return True
    except Exception as e:
        print(f"Erro ao salvar conteúdo dos agentes: {e}"); return False


def update_approved_status(product_id: str, status: str) -> bool:
    with get_connection() as conn:
        conn.execute("UPDATE approved_products SET status=? WHERE product_id=?",
                     (status, product_id))
    return True


# ── INTEGRAÇÕES DE LOJAS ──────────────────────────────────────────────────────

def save_store_integration(data: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT OR REPLACE INTO store_integrations
               (id,name,platform,api_key,api_secret,store_url,store_id,
                access_token,webhook_url,is_active,config_json)
               VALUES (:id,:name,:platform,:api_key,:api_secret,:store_url,:store_id,
               :access_token,:webhook_url,:is_active,:config_json)""", data)
        return cur.lastrowid


def get_store_integrations(active_only: bool = False) -> list:
    with get_connection() as conn:
        query = "SELECT * FROM store_integrations"
        if active_only:
            query += " WHERE is_active=1"
        query += " ORDER BY created_at DESC"
        return [dict(r) for r in conn.execute(query).fetchall()]


def get_store_by_id(store_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM store_integrations WHERE id=?", (store_id,)).fetchone()
        return dict(row) if row else None


def delete_store_integration(store_id: int) -> bool:
    with get_connection() as conn:
        conn.execute("DELETE FROM store_integrations WHERE id=?", (store_id,))
    return True


def toggle_store_active(store_id: int, is_active: bool) -> bool:
    with get_connection() as conn:
        conn.execute("UPDATE store_integrations SET is_active=? WHERE id=?",
                     (is_active, store_id))
    return True


def update_store_last_sync(store_id: int):
    with get_connection() as conn:
        conn.execute("UPDATE store_integrations SET last_sync=CURRENT_TIMESTAMP WHERE id=?",
                     (store_id,))


# ── PUBLICAÇÕES ───────────────────────────────────────────────────────────────

def save_publication(data: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO publications (product_id,approved_id,store_id,status)
               VALUES (:product_id,:approved_id,:store_id,'pendente')""", data)
        return cur.lastrowid


def update_publication(pub_id: int, data: dict):
    with get_connection() as conn:
        conn.execute(
            """UPDATE publications SET status=:status, platform_listing_id=:listing_id,
               platform_listing_url=:listing_url, published_at=CURRENT_TIMESTAMP,
               error_message=:error WHERE id=:id""",
            {**data, "id": pub_id})


def get_publications(product_id: str = None) -> list:
    query = """SELECT pub.*, si.name as store_name, si.platform
               FROM publications pub
               JOIN store_integrations si ON pub.store_id = si.id"""
    params = []
    if product_id:
        query += " WHERE pub.product_id=?"; params.append(product_id)
    query += " ORDER BY pub.created_at DESC"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


# ── PEDIDOS ───────────────────────────────────────────────────────────────────

def save_order(data: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO orders (store_id,publication_id,product_id,platform_order_id,
               customer_name,customer_email,quantity,sale_price,cost_price,profit,
               status,dropi_order_id)
               VALUES (:store_id,:publication_id,:product_id,:platform_order_id,
               :customer_name,:customer_email,:quantity,:sale_price,:cost_price,:profit,
               :status,:dropi_order_id)""", data)
        return cur.lastrowid


def get_orders(store_id: int = None, limit: int = 50) -> list:
    query = """SELECT o.*, si.name as store_name, p.name as product_name
               FROM orders o
               LEFT JOIN store_integrations si ON o.store_id = si.id
               LEFT JOIN products p ON o.product_id = p.id"""
    params = []
    if store_id:
        query += " WHERE o.store_id=?"; params.append(store_id)
    query += f" ORDER BY o.created_at DESC LIMIT {limit}"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_orders_stats() -> dict:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        revenue = conn.execute("SELECT COALESCE(SUM(sale_price),0) FROM orders").fetchone()[0]
        profit = conn.execute("SELECT COALESCE(SUM(profit),0) FROM orders").fetchone()[0]
        pending = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status='novo'").fetchone()[0]
    return {"total": total, "revenue": revenue, "profit": profit, "pending": pending}


# ── LOGS DE AGENTES ───────────────────────────────────────────────────────────

def log_agent(agent: str, action: str, product_id: str = None,
              result: str = "", status: str = "ok"):
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO agent_logs (agent,product_id,action,result,status) VALUES (?,?,?,?,?)",
                (agent, product_id, action, result, status))
    except Exception:
        pass


def get_agent_logs(limit: int = 50) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

def get_dashboard_stats() -> dict:
    with get_connection() as conn:
        total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        total_approved = conn.execute("SELECT COUNT(*) FROM approved_products").fetchone()[0]
        total_rejected = conn.execute(
            "SELECT COUNT(*) FROM decision_history WHERE decision='rejeitado'").fetchone()[0]
        best_score = conn.execute("SELECT MAX(score) FROM analyses").fetchone()[0] or 0
        total_searches = conn.execute("SELECT COUNT(*) FROM searches").fetchone()[0]
        total_publications = conn.execute(
            "SELECT COUNT(*) FROM publications WHERE status='publicado'").fetchone()[0]
        total_stores = conn.execute(
            "SELECT COUNT(*) FROM store_integrations WHERE is_active=1").fetchone()[0]
        orders = get_orders_stats()

        top_products = conn.execute(
            """SELECT p.id, p.name, p.price, p.rating, a.score, a.ai_decision
               FROM products p JOIN analyses a ON p.id=a.product_id
               ORDER BY a.score DESC LIMIT 5""").fetchall()

    return {
        "total_products": total_products,
        "total_approved": total_approved,
        "total_rejected": total_rejected,
        "best_score": round(best_score, 1),
        "total_searches": total_searches,
        "total_publications": total_publications,
        "total_stores": total_stores,
        "orders": orders,
        "top_products": [dict(r) for r in top_products],
    }


def get_categories() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM products WHERE category IS NOT NULL ORDER BY category"
        ).fetchall()
        return ["Todas"] + [r[0] for r in rows]
