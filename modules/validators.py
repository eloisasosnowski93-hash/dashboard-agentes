"""Smart Product Finder v2.0 - Validators"""
from typing import Tuple, List

def validate_search_form(params: dict) -> Tuple[bool, List[str]]:
    errors = []
    kw = params.get("keyword","").strip()
    if not kw: errors.append("Palavra-chave obrigatória.")
    elif len(kw) < 3: errors.append("Palavra-chave: mínimo 3 caracteres.")
    elif len(kw) > 100: errors.append("Palavra-chave: máximo 100 caracteres.")
    mn, mx = params.get("min_price",0), params.get("max_price",0)
    if mn < 0: errors.append("Preço mínimo não pode ser negativo.")
    if mx < 0: errors.append("Preço máximo não pode ser negativo.")
    if mx > 0 and mn > mx: errors.append("Preço mínimo maior que máximo.")
    if not (0 <= params.get("min_rating",0) <= 5): errors.append("Avaliação entre 0 e 5.")
    if params.get("min_sales",0) < 0: errors.append("Vendas mínimas não pode ser negativo.")
    if not (0 <= params.get("min_margin",0) <= 100): errors.append("Margem entre 0 e 100%.")
    if params.get("freight_cost",0) < 0: errors.append("Frete não pode ser negativo.")
    if params.get("competition","") not in ["baixa","média","alta",""]: errors.append("Concorrência: baixa, média ou alta.")
    return len(errors)==0, errors

def validate_product_data(product: dict) -> Tuple[bool, List[str]]:
    errors = []
    if not product.get("id"): errors.append("Produto sem ID.")
    if not product.get("name"): errors.append("Produto sem nome.")
    price = product.get("price", 0)
    if price is None or price <= 0: errors.append("Preço inválido.")
    return len(errors)==0, errors

def sanitize_string(value: str, max_length: int = 500) -> str:
    if not value: return ""
    return str(value).strip()[:max_length]
