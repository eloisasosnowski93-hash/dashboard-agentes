"""
Smart Product Finder — modules/shopee_api.py
Integração com Shopee Open Platform API v2.

Implementa:
  • Autenticação HMAC-SHA256 (obrigatória pela Shopee)
  • get_shop_info()           — valida credenciais e retorna dados da loja
  • add_item()                — publica produto aprovado
  • get_item_list()           — lista produtos ativos
  • get_order_list()          — lista pedidos recentes
  • get_logistics_tracking()  — rastreamento de pedido

Modo DEMO: quando sem credenciais reais, retorna dados simulados
para que a UI funcione sem quebrar.

Referência: https://open.shopee.com/documents/v2
"""

import hashlib
import hmac
import time
import json
import os
from typing import Optional, Any
from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

SHOPEE_HOST = "https://partner.shopeemobile.com"
SHOPEE_HOST_TEST = "https://partner.test-stable.shopeemobile.com"

# Lê credenciais de st.secrets ou variáveis de ambiente
def _get_credentials() -> dict:
    """Lê credenciais Shopee de st.secrets ou env vars."""
    try:
        import streamlit as st
        return {
            "partner_id":  int(st.secrets.get("SHOPEE_PARTNER_ID", 0)),
            "partner_key": st.secrets.get("SHOPEE_PARTNER_KEY", ""),
            "shop_id":     int(st.secrets.get("SHOPEE_SHOP_ID", 0)),
            "access_token":st.secrets.get("SHOPEE_ACCESS_TOKEN", ""),
            "test_mode":   bool(st.secrets.get("SHOPEE_TEST_MODE", True)),
        }
    except Exception:
        return {
            "partner_id":  int(os.getenv("SHOPEE_PARTNER_ID", "0")),
            "partner_key": os.getenv("SHOPEE_PARTNER_KEY", ""),
            "shop_id":     int(os.getenv("SHOPEE_SHOP_ID", "0")),
            "access_token":os.getenv("SHOPEE_ACCESS_TOKEN", ""),
            "test_mode":   os.getenv("SHOPEE_TEST_MODE", "true").lower() == "true",
        }


@dataclass
class ShopeeCredentials:
    partner_id: int = 0
    partner_key: str = ""
    shop_id: int = 0
    access_token: str = ""
    test_mode: bool = True

    @property
    def is_configured(self) -> bool:
        return bool(self.partner_id and self.partner_key and self.shop_id)

    @property
    def host(self) -> str:
        return SHOPEE_HOST_TEST if self.test_mode else SHOPEE_HOST


# ─────────────────────────────────────────────────────────────────────────────
# CLIENTE SHOPEE API v2
# ─────────────────────────────────────────────────────────────────────────────

class ShopeeAPIClient:
    """
    Cliente para a Shopee Open Platform API v2.
    Gerencia autenticação HMAC e todas as chamadas.
    """

    def __init__(self, creds: Optional[ShopeeCredentials] = None):
        if creds:
            self.creds = creds
        else:
            raw = _get_credentials()
            self.creds = ShopeeCredentials(**raw)

    def _sign(self, path: str, timestamp: int) -> str:
        """
        Gera assinatura HMAC-SHA256 conforme Shopee Open Platform.
        Format: {partner_id}{path}{timestamp}{access_token}{shop_id}
        """
        base_str = (
            f"{self.creds.partner_id}"
            f"{path}"
            f"{timestamp}"
            f"{self.creds.access_token}"
            f"{self.creds.shop_id}"
        )
        return hmac.new(
            self.creds.partner_key.encode("utf-8"),
            base_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _build_url(self, path: str) -> tuple[str, dict]:
        """Constrói URL completa com parâmetros de auth."""
        ts = int(time.time())
        sign = self._sign(path, ts)
        base_url = f"{self.creds.host}{path}"
        params = {
            "partner_id":   self.creds.partner_id,
            "timestamp":    ts,
            "access_token": self.creds.access_token,
            "shop_id":      self.creds.shop_id,
            "sign":         sign,
        }
        return base_url, params

    def _get(self, path: str, extra_params: dict = None) -> dict:
        """Requisição GET autenticada."""
        if not self.creds.is_configured:
            return {"error": "not_configured", "demo": True}
        try:
            import requests
            url, params = self._build_url(path)
            if extra_params:
                params.update(extra_params)
            resp = requests.get(url, params=params, timeout=15)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def _post(self, path: str, payload: dict) -> dict:
        """Requisição POST autenticada."""
        if not self.creds.is_configured:
            return {"error": "not_configured", "demo": True}
        try:
            import requests
            url, params = self._build_url(path)
            resp = requests.post(url, params=params, json=payload, timeout=15)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    # ── ENDPOINTS ─────────────────────────────────────────────────────────────

    def get_shop_info(self) -> dict:
        """
        GET /api/v2/shop/get_shop_info
        Valida credenciais e retorna dados da loja.
        """
        if not self.creds.is_configured:
            return _demo_shop_info()

        result = self._get("/api/v2/shop/get_shop_info")
        if result.get("demo"):
            return _demo_shop_info()
        return result

    def get_item_list(self, offset: int = 0, page_size: int = 20,
                      item_status: str = "NORMAL") -> dict:
        """
        GET /api/v2/product/get_item_list
        Lista produtos ativos na loja.
        """
        if not self.creds.is_configured:
            return _demo_item_list()

        result = self._get("/api/v2/product/get_item_list", {
            "offset":      offset,
            "page_size":   page_size,
            "item_status": item_status,
        })
        return result if not result.get("demo") else _demo_item_list()

    def add_item(self, item_payload: dict) -> dict:
        """
        POST /api/v2/product/add_item
        Publica um novo produto na Shopee.
        Payload deve seguir o schema da Shopee v2.
        """
        if not self.creds.is_configured:
            return _demo_add_item(item_payload)

        return self._post("/api/v2/product/add_item", item_payload)

    def get_order_list(self, time_from: int = None, time_to: int = None,
                       order_status: str = "READY_TO_SHIP") -> dict:
        """
        GET /api/v2/order/get_order_list
        Lista pedidos por status e período.
        """
        if not self.creds.is_configured:
            return _demo_order_list()

        now = int(time.time())
        params = {
            "time_range_field": "create_time",
            "time_from": time_from or (now - 30 * 86400),  # últimos 30d
            "time_to":   time_to or now,
            "page_size": 20,
            "cursor":    "",
            "order_status": order_status,
            "response_optional_fields": "order_status",
        }
        result = self._get("/api/v2/order/get_order_list", params)
        return result if not result.get("demo") else _demo_order_list()

    def get_order_detail(self, order_sn_list: list) -> dict:
        """
        POST /api/v2/order/get_order_detail
        Retorna detalhes completos de pedidos.
        """
        if not self.creds.is_configured:
            return _demo_order_detail()
        return self._post("/api/v2/order/get_order_detail", {
            "order_sn_list": order_sn_list,
            "response_optional_fields": "buyer_username,item_list,package_list",
        })

    def get_shopee_categories(self, language: str = "pt-BR") -> dict:
        """
        GET /api/v2/product/get_category
        Retorna categorias da Shopee com IDs para publicação.
        """
        if not self.creds.is_configured:
            return _demo_categories()
        return self._get("/api/v2/product/get_category", {"language": language})

    def build_item_payload(self, product: dict, content: dict) -> dict:
        """
        Constrói o payload para add_item a partir dos dados do produto e conteúdo dos agentes.
        Segue o schema obrigatório da Shopee Open Platform v2.
        """
        title = (content.get("agent_title") or product.get("name", ""))[:120]
        description = content.get("agent_description") or product.get("ai_description", "")
        price = int((content.get("agent_price") or product.get("ai_price_suggestion", 30)) * 100000)  # em centésimos de centavo
        image_urls = [product.get("image_url", "")] if product.get("image_url") else []

        return {
            "original_price": price,
            "description": description[:3000],
            "item_name": title,
            "normal_stock": 9999,          # dropshipping = estoque virtual alto
            "weight": 300,                  # em gramas
            "item_sku": f"SPF-{product.get('id','')[:8]}",
            "logistic_info": [{"logistic_id": 80015, "enabled": True}],  # Shopee Xpress
            "attribute_list": [],
            "category_id": 100001,          # ID placeholder — pegar de get_shopee_categories
            "image": {"image_url_list": image_urls[:9]},
            "condition": "NEW",
            "item_status": "NORMAL",
        }


# ─────────────────────────────────────────────────────────────────────────────
# DADOS DEMO (quando sem credenciais reais)
# ─────────────────────────────────────────────────────────────────────────────

def _demo_shop_info() -> dict:
    return {
        "demo": True,
        "response": {
            "shop_name": "Minha Loja Demo",
            "shop_status": "NORMAL",
            "item_limit": 99999,
            "description_limit": 3000,
            "shop_logo": "",
            "seller_type": "local_seller",
        }
    }


def _demo_item_list() -> dict:
    import random
    items = []
    for i in range(5):
        items.append({
            "item_id": 1000000 + i,
            "item_status": "NORMAL",
            "update_time": int(time.time()) - i * 86400,
        })
    return {"demo": True, "response": {"item": items, "total_count": 5, "has_next_page": False}}


def _demo_add_item(payload: dict) -> dict:
    return {
        "demo": True,
        "response": {
            "item_id": 9999999,
            "item_name": payload.get("item_name", "Produto Demo"),
        },
        "message": "Publicação simulada (modo demo)"
    }


def _demo_order_list() -> dict:
    import random
    orders = []
    statuses = ["READY_TO_SHIP", "PROCESSED", "SHIPPED", "COMPLETED"]
    for i in range(8):
        orders.append({
            "order_sn": f"2401{random.randint(10000000, 99999999)}",
            "order_status": statuses[i % len(statuses)],
            "create_time": int(time.time()) - i * 3600 * 6,
        })
    return {"demo": True, "response": {"order_list": orders, "more": False}}


def _demo_order_detail() -> dict:
    return {"demo": True, "response": {"order_list": []}}


def _demo_categories() -> dict:
    return {"demo": True, "response": {"category_list": []}}


def get_shopee_status(creds_dict: dict = None) -> dict:
    """Retorna status da integração Shopee para o dashboard."""
    if creds_dict:
        creds = ShopeeCredentials(**creds_dict)
    else:
        raw = _get_credentials()
        creds = ShopeeCredentials(**raw)

    if creds.is_configured:
        return {
            "configured": True,
            "test_mode": creds.test_mode,
            "shop_id": creds.shop_id,
            "message": f"✅ Shopee configurada {'(sandbox)' if creds.test_mode else '(produção)'}",
        }
    return {
        "configured": False,
        "test_mode": True,
        "shop_id": 0,
        "message": "⚠️ Shopee não configurada — adicione as credenciais em st.secrets",
    }
