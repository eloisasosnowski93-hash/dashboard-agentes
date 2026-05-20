"""Smart Product Finder v2.0 - Scoring de produtos (0-100)"""
import json
from typing import Tuple

def calculate_score(product: dict, search_params: dict) -> Tuple[float, dict]:
    breakdown = {}
    total = 0.0
    s, d = _score_price_margin(product, search_params)
    breakdown["price_margin"] = {"score": s, "max": 25, "detail": d}; total += s
    s, d = _score_rating(product.get("rating", 0))
    breakdown["rating"] = {"score": s, "max": 20, "detail": d}; total += s
    s, d = _score_sales(product.get("sales", 0))
    breakdown["sales_volume"] = {"score": s, "max": 20, "detail": d}; total += s
    s, d = _score_shipping(product.get("ships_from_brazil", False), product.get("delivery_days", 30))
    breakdown["shipping"] = {"score": s, "max": 10, "detail": d}; total += s
    s = 8 if product.get("choice_badge") else 0
    breakdown["choice_badge"] = {"score": s, "max": 8, "detail": "Selo Choice ✓" if s else "Sem Choice"}; total += s
    s, d = _score_competition(search_params.get("competition", "média"))
    breakdown["competition"] = {"score": s, "max": 10, "detail": d}; total += s
    s, d = _score_visual(product)
    breakdown["visual_potential"] = {"score": s, "max": 4, "detail": d}; total += s
    s, d = _score_saturation(product)
    breakdown["saturation_risk"] = {"score": s, "max": 3, "detail": d}; total += s
    return round(min(total, 100), 1), breakdown

def _score_price_margin(product, params):
    cost = product.get("price", 0); freight = params.get("freight_cost", 15)
    target = params.get("target_price", 0)
    if target <= 0 or cost <= 0:
        if cost < 15: return 20, f"Custo baixo R${cost:.2f} — bom potencial"
        elif cost < 30: return 15, f"Custo moderado R${cost:.2f}"
        else: return 8, f"Custo elevado R${cost:.2f}"
    margin = ((target - cost - freight) / target) * 100
    if margin >= 60: return 25, f"Margem excelente: {margin:.1f}%"
    elif margin >= 45: return 20, f"Margem boa: {margin:.1f}%"
    elif margin >= 30: return 14, f"Margem aceitável: {margin:.1f}%"
    elif margin >= 15: return 7, f"Margem baixa: {margin:.1f}%"
    else: return 2, f"Margem insuficiente: {margin:.1f}%"

def _score_rating(r):
    if r >= 4.8: return 20, f"Excepcional: {r}⭐"
    elif r >= 4.5: return 16, f"Muito boa: {r}⭐"
    elif r >= 4.0: return 12, f"Boa: {r}⭐"
    elif r >= 3.5: return 7, f"Regular: {r}⭐"
    elif r > 0: return 3, f"Baixa: {r}⭐"
    else: return 0, "Sem avaliações"

def _score_sales(s):
    if s >= 20000: return 20, f"Altíssimo: {s:,} vendas"
    elif s >= 10000: return 17, f"Muito alto: {s:,} vendas"
    elif s >= 5000: return 14, f"Alto: {s:,} vendas"
    elif s >= 1000: return 10, f"Moderado: {s:,} vendas"
    elif s >= 100: return 6, f"Baixo: {s:,} vendas"
    elif s > 0: return 3, f"Poucas: {s} vendas"
    else: return 0, "Sem dados"

def _score_shipping(br, days):
    if br: return (10, f"🇧🇷 Brasil: {days}d — vantagem máxima") if days <= 7 else (8, f"🇧🇷 Brasil: {days}d")
    if days <= 15: return 4, f"Internacional rápido: {days}d"
    elif days <= 25: return 2, f"Internacional médio: {days}d"
    else: return 0, f"Internacional lento: {days}d"

def _score_competition(c):
    m = {"baixa": (10, "Baixa — janela de oportunidade"), "média": (5, "Média — necessário diferencial"), "alta": (1, "Alta — difícil destaque")}
    return m.get(c.lower(), (5, "Não informada"))

def _score_visual(p):
    name = p.get("name","").lower(); cat = p.get("category","").lower()
    s = 0
    if p.get("image_url"): s += 2
    if any(k in cat for k in ["casa","decoração","moda","beleza","esporte"]): s += 1
    if any(k in name for k in ["led","kit","premium","design","colorido"]): s += 1
    labels = {0:"Baixo",1:"Moderado",2:"Bom",3:"Alto",4:"Excepcional"}
    return min(s,4), f"Potencial visual: {labels.get(s,'Moderado')}"

def _score_saturation(p):
    sales = p.get("sales",0); cat = p.get("category","").lower()
    generic = any(g in cat for g in ["eletrônicos","capas","carregadores"])
    if sales > 50000 and generic: return 0, "Alto risco de saturação"
    elif sales > 20000: return 1, "Risco moderado"
    else: return 3, "Baixo risco — espaço disponível"

def get_score_label(score):
    if score >= 80: return "🟢 EXCELENTE", "#27AE60"
    elif score >= 65: return "🔵 BOM", "#2980B9"
    elif score >= 50: return "🟡 REGULAR", "#F39C12"
    elif score >= 35: return "🟠 FRACO", "#E67E22"
    else: return "🔴 RUIM", "#E74C3C"

def format_score_breakdown(b): return json.dumps(b, ensure_ascii=False)
def parse_score_breakdown(s):
    if not s: return {}
    try: return json.loads(s)
    except: return {}
