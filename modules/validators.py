"""
Smart Product Finder - Módulo de Validação
Valida os dados do formulário de busca antes de iniciar qualquer coleta.
"""

from typing import Tuple, List


def validate_search_form(params: dict) -> Tuple[bool, List[str]]:
    """
    Valida todos os campos do formulário de busca.
    
    Retorna:
        (True, []) se válido
        (False, [lista de erros]) se inválido
    """
    errors = []

    # Palavra-chave obrigatória
    keyword = params.get("keyword", "").strip()
    if not keyword:
        errors.append("A palavra-chave do produto é obrigatória.")
    elif len(keyword) < 3:
        errors.append("A palavra-chave deve ter pelo menos 3 caracteres.")
    elif len(keyword) > 100:
        errors.append("A palavra-chave não pode ter mais de 100 caracteres.")

    # Faixa de preço
    min_price = params.get("min_price", 0)
    max_price = params.get("max_price", 0)
    if min_price < 0:
        errors.append("O preço mínimo não pode ser negativo.")
    if max_price < 0:
        errors.append("O preço máximo não pode ser negativo.")
    if max_price > 0 and min_price > max_price:
        errors.append("O preço mínimo não pode ser maior que o preço máximo.")

    # Avaliação mínima
    min_rating = params.get("min_rating", 0)
    if not (0 <= min_rating <= 5):
        errors.append("A avaliação mínima deve estar entre 0 e 5.")

    # Quantidade mínima de vendas
    min_sales = params.get("min_sales", 0)
    if min_sales < 0:
        errors.append("A quantidade mínima de vendas não pode ser negativa.")

    # Margem mínima
    min_margin = params.get("min_margin", 0)
    if min_margin < 0:
        errors.append("A margem mínima não pode ser negativa.")
    if min_margin > 100:
        errors.append("A margem mínima não pode ser maior que 100%.")

    # Custo de frete
    freight_cost = params.get("freight_cost", 0)
    if freight_cost < 0:
        errors.append("O custo de frete não pode ser negativo.")

    # Preço de venda pretendido
    target_price = params.get("target_price", 0)
    if target_price < 0:
        errors.append("O preço de venda pretendido não pode ser negativo.")

    # Concorrência percebida
    competition = params.get("competition", "")
    valid_competition = ["baixa", "média", "alta", ""]
    if competition not in valid_competition:
        errors.append("Concorrência deve ser: baixa, média ou alta.")

    return len(errors) == 0, errors


def validate_product_data(product: dict) -> Tuple[bool, List[str]]:
    """
    Valida os dados de um produto coletado pelo scraper.
    Garante integridade antes de salvar no banco.
    """
    errors = []

    if not product.get("id"):
        errors.append("Produto sem ID.")

    if not product.get("name"):
        errors.append("Produto sem nome.")

    price = product.get("price", 0)
    if price is None or price <= 0:
        errors.append("Produto com preço inválido.")

    rating = product.get("rating", 0)
    if rating is not None and not (0 <= rating <= 5):
        errors.append(f"Avaliação inválida: {rating}")

    return len(errors) == 0, errors


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Remove caracteres problemáticos e limita o tamanho de strings."""
    if not value:
        return ""
    return str(value).strip()[:max_length]
