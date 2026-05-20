"""
Smart Product Finder - Módulo de Banco de Dados
Gerencia conexão SQLite e operações CRUD para todas as entidades do sistema.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path


# Caminho padrão do banco de dados
DB_PATH = Path(__file__).parent.parent / "data" / "smart_finder.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """
    Retorna uma conexão com o banco SQLite.
    Configura row_factory para acessar colunas por nome.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # melhor performance em concorrência
    return conn


def initialize_database():
    """
    Inicializa o banco de dados criando todas as tabelas se não existirem.
    Lê o schema SQL e executa na conexão.
    """
    # Garante que o diretório data/ existe
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        if SCHEMA_PATH.exists():
            schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
            conn.executescript(schema_sql)
        else:
            raise FileNotFoundError(f"Schema não encontrado: {SCHEMA_PATH}")


# ─────────────────────────────────────────────
# OPERAÇÕES DE BUSCA (searches)
# ─────────────────────────────────────────────

def save_search(search_params: dict) -> int:
    """
    Salva uma busca realizada pelo usuário.
    Retorna o ID da busca criada.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO searches (
                keyword, category, min_price, max_price, min_rating,
                min_sales, ships_from_brazil, choice_badge, min_margin,
                freight_cost, target_price, competition, notes
            ) VALUES (
                :keyword, :category, :min_price, :max_price, :min_rating,
                :min_sales, :ships_from_brazil, :choice_badge, :min_margin,
                :freight_cost, :target_price, :competition, :notes
            )
            """,
            search_params
        )
        return cursor.lastrowid


def update_search_totals(search_id: int, total_found: int, total_approved: int):
    """Atualiza os totais de uma busca após coleta e análise."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE searches SET total_found = ?, total_approved = ? WHERE id = ?",
            (total_found, total_approved, search_id)
        )


def get_recent_searches(limit: int = 10) -> list:
    """Retorna as últimas buscas realizadas."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM searches ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


# ─────────────────────────────────────────────
# OPERAÇÕES DE PRODUTO (products)
# ─────────────────────────────────────────────

def save_product(product: dict, search_id: int) -> str:
    """
    Salva um produto coletado vinculado a uma busca.
    Usa INSERT OR REPLACE para evitar duplicatas.
    Retorna o ID do produto.
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO products (
                id, search_id, name, link, price, rating, sales,
                delivery_days, ships_from_brazil, choice_badge,
                image_url, category, collected_at
            ) VALUES (
                :id, :search_id, :name, :link, :price, :rating, :sales,
                :delivery_days, :ships_from_brazil, :choice_badge,
                :image_url, :category, :collected_at
            )
            """,
            {**product, "search_id": search_id}
        )
        return product["id"]


def get_all_products(filters: dict = None) -> list:
    """
    Retorna todos os produtos com suporte a filtros opcionais.
    Filters pode conter: min_score, max_price, min_rating, min_sales, category, status
    """
    query = """
        SELECT 
            p.*,
            a.score,
            a.ai_decision,
            a.ai_shopee_title,
            a.ai_price_suggestion,
            a.score_breakdown,
            CASE WHEN ap.id IS NOT NULL THEN 1 ELSE 0 END as is_approved
        FROM products p
        LEFT JOIN analyses a ON p.id = a.product_id
        LEFT JOIN approved_products ap ON p.id = ap.product_id
        WHERE 1=1
    """
    params = []

    if filters:
        if filters.get("min_score"):
            query += " AND a.score >= ?"
            params.append(filters["min_score"])
        if filters.get("max_price"):
            query += " AND p.price <= ?"
            params.append(filters["max_price"])
        if filters.get("min_rating"):
            query += " AND p.rating >= ?"
            params.append(filters["min_rating"])
        if filters.get("min_sales"):
            query += " AND p.sales >= ?"
            params.append(filters["min_sales"])
        if filters.get("category") and filters["category"] != "Todas":
            query += " AND p.category = ?"
            params.append(filters["category"])
        if filters.get("status") == "aprovado":
            query += " AND ap.id IS NOT NULL"
        elif filters.get("status") == "rejeitado":
            query += " AND ap.id IS NULL AND a.ai_decision = 'rejeitado'"

    query += " ORDER BY a.score DESC NULLS LAST"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_product_by_id(product_id: str) -> dict:
    """Retorna um produto específico com sua análise."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT p.*, a.score, a.score_breakdown, a.ai_decision,
                   a.ai_potential, a.ai_target_audience, a.ai_strengths,
                   a.ai_weaknesses, a.ai_risk, a.ai_price_suggestion,
                   a.ai_shopee_title, a.ai_description, a.ai_creative_ideas,
                   a.ai_hashtags
            FROM products p
            LEFT JOIN analyses a ON p.id = a.product_id
            WHERE p.id = ?
            """,
            (product_id,)
        ).fetchone()
        return dict(row) if row else None


def get_total_products() -> int:
    """Retorna o total de produtos no banco."""
    with get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) FROM products").fetchone()
        return result[0]


# ─────────────────────────────────────────────
# OPERAÇÕES DE ANÁLISE (analyses)
# ─────────────────────────────────────────────

def save_analysis(analysis: dict) -> int:
    """
    Salva a análise de score e IA para um produto.
    Retorna o ID da análise criada.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT OR REPLACE INTO analyses (
                product_id, score, score_breakdown, ai_potential,
                ai_target_audience, ai_strengths, ai_weaknesses,
                ai_risk, ai_price_suggestion, ai_shopee_title,
                ai_description, ai_creative_ideas, ai_hashtags, ai_decision
            ) VALUES (
                :product_id, :score, :score_breakdown, :ai_potential,
                :ai_target_audience, :ai_strengths, :ai_weaknesses,
                :ai_risk, :ai_price_suggestion, :ai_shopee_title,
                :ai_description, :ai_creative_ideas, :ai_hashtags, :ai_decision
            )
            """,
            analysis
        )
        return cursor.lastrowid


def get_best_score() -> float:
    """Retorna o melhor score encontrado entre todos os produtos."""
    with get_connection() as conn:
        result = conn.execute("SELECT MAX(score) FROM analyses").fetchone()
        return result[0] or 0.0


# ─────────────────────────────────────────────
# OPERAÇÕES DE APROVAÇÃO (approved_products)
# ─────────────────────────────────────────────

def approve_product(product_id: str, analysis_id: int = None, notes: str = "") -> bool:
    """
    Aprova um produto e registra no histórico de decisões.
    Retorna True se aprovado com sucesso.
    """
    try:
        with get_connection() as conn:
            # Verifica se já está aprovado
            existing = conn.execute(
                "SELECT id FROM approved_products WHERE product_id = ?",
                (product_id,)
            ).fetchone()

            if not existing:
                conn.execute(
                    """
                    INSERT INTO approved_products (product_id, analysis_id, notes)
                    VALUES (?, ?, ?)
                    """,
                    (product_id, analysis_id, notes)
                )

            # Registra no histórico
            conn.execute(
                "INSERT INTO decision_history (product_id, decision, reason) VALUES (?, 'aprovado', ?)",
                (product_id, notes)
            )
        return True
    except Exception as e:
        print(f"Erro ao aprovar produto: {e}")
        return False


def reject_product(product_id: str, reason: str = "") -> bool:
    """
    Rejeita um produto removendo da lista de aprovados se existir.
    Registra no histórico.
    """
    try:
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM approved_products WHERE product_id = ?",
                (product_id,)
            )
            conn.execute(
                "INSERT INTO decision_history (product_id, decision, reason) VALUES (?, 'rejeitado', ?)",
                (product_id, reason)
            )
        return True
    except Exception as e:
        print(f"Erro ao rejeitar produto: {e}")
        return False


def get_approved_products() -> list:
    """Retorna todos os produtos aprovados com detalhes."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT p.*, a.score, a.ai_shopee_title, a.ai_price_suggestion,
                   a.ai_decision, ap.approved_at, ap.notes as approval_notes, ap.status
            FROM approved_products ap
            JOIN products p ON ap.product_id = p.id
            LEFT JOIN analyses a ON p.id = a.product_id
            ORDER BY ap.approved_at DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def get_total_approved() -> int:
    """Retorna o total de produtos aprovados."""
    with get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) FROM approved_products").fetchone()
        return result[0]


# ─────────────────────────────────────────────
# DASHBOARD STATS
# ─────────────────────────────────────────────

def get_dashboard_stats() -> dict:
    """
    Agrega todas as estatísticas para o dashboard principal.
    Retorna um dicionário com métricas chave.
    """
    with get_connection() as conn:
        total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        total_approved = conn.execute("SELECT COUNT(*) FROM approved_products").fetchone()[0]
        total_rejected = conn.execute(
            "SELECT COUNT(*) FROM decision_history WHERE decision = 'rejeitado'"
        ).fetchone()[0]
        best_score = conn.execute("SELECT MAX(score) FROM analyses").fetchone()[0] or 0
        total_searches = conn.execute("SELECT COUNT(*) FROM searches").fetchone()[0]

        # Top 5 produtos por score
        top_products = conn.execute(
            """
            SELECT p.name, p.price, p.rating, a.score, a.ai_decision
            FROM products p
            JOIN analyses a ON p.id = a.product_id
            ORDER BY a.score DESC
            LIMIT 5
            """
        ).fetchall()

    return {
        "total_products": total_products,
        "total_approved": total_approved,
        "total_rejected": total_rejected,
        "best_score": round(best_score, 1),
        "total_searches": total_searches,
        "top_products": [dict(r) for r in top_products],
    }


def get_categories() -> list:
    """Retorna lista de categorias únicas dos produtos."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM products WHERE category IS NOT NULL ORDER BY category"
        ).fetchall()
        return ["Todas"] + [r[0] for r in rows]
