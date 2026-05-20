"""
Smart Product Finder v2.0 - Módulo de Integrações
Suporta: Shopee, Dropi, WooCommerce, Nuvemshop, MercadoLivre

Cada integração implementa a interface comum:
  - test_connection() -> bool
  - publish_product(product, content) -> dict
  - sync_orders() -> list
  - get_listings() -> list
"""

import os
import json
import time
import uuid
import random
from datetime import datetime
from typing import Optional
from database import db


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRO DE PLATAFORMAS DISPONÍVEIS
# ─────────────────────────────────────────────────────────────────────────────

PLATFORMS = {
    "shopee": {
        "name": "Shopee",
        "icon": "🛍️",
        "color": "#EE4D2D",
        "description": "Marketplace líder no Brasil — integração via Shopee Open Platform API",
        "docs_url": "https://open.shopee.com/documents",
        "fields": ["partner_id", "partner_key", "shop_id", "access_token"],
        "features": ["Publicar produtos", "Sincronizar pedidos", "Shopee Ads", "Chat"],
        "status": "disponível"
    },
    "dropi": {
        "name": "Dropi",
        "icon": "📦",
        "color": "#7C3AED",
        "description": "Plataforma de dropshipping — envio automático de pedidos ao fornecedor",
        "docs_url": "https://dropi.com.br",
        "fields": ["api_key", "store_id"],
        "features": ["Catálogo de produtos", "Envio automático de pedidos", "Rastreamento", "Relatórios"],
        "status": "disponível"
    },
    "woocommerce": {
        "name": "WooCommerce",
        "icon": "🛒",
        "color": "#96588A",
        "description": "Plugin WordPress — integração via WooCommerce REST API",
        "docs_url": "https://woocommerce.com/document/woocommerce-rest-api",
        "fields": ["store_url", "consumer_key", "consumer_secret"],
        "features": ["Publicar produtos", "Gerenciar estoque", "Sincronizar pedidos", "Cupons"],
        "status": "disponível"
    },
    "nuvemshop": {
        "name": "Nuvemshop",
        "icon": "☁️",
        "color": "#00B1EA",
        "description": "Plataforma de e-commerce nacional — integração via Nuvemshop API",
        "docs_url": "https://tiendanube.github.io/api-documentation",
        "fields": ["store_id", "access_token"],
        "features": ["Publicar produtos", "Gerenciar pedidos", "Estoque", "Relatórios"],
        "status": "disponível"
    },
    "mercadolivre": {
        "name": "MercadoLivre",
        "icon": "🟡",
        "color": "#FFE600",
        "description": "Marketplace líder na América Latina — integração via MercadoLibre API",
        "docs_url": "https://developers.mercadolivre.com.br",
        "fields": ["client_id", "client_secret", "access_token"],
        "features": ["Publicar anúncios", "Sincronizar pedidos", "Reputação", "Perguntas"],
        "status": "em breve"
    },
    "yampi": {
        "name": "Yampi",
        "icon": "🚀",
        "color": "#F97316",
        "description": "Checkout e e-commerce — integração via Yampi API",
        "docs_url": "https://docs.yampi.com.br",
        "fields": ["alias", "token", "secret_key"],
        "features": ["Publicar produtos", "Checkout otimizado", "Pedidos", "Relatórios"],
        "status": "em breve"
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# TESTADOR DE CONEXÃO
# ─────────────────────────────────────────────────────────────────────────────

def test_connection(store: dict) -> dict:
    """
    Testa a conexão com uma integração de loja.
    No MVP, simula o teste. Na versão real, chama a API correspondente.
    """
    platform = store.get("platform", "")
    
    # Simula latência de API
    time.sleep(0.5)
    
    # Valida campos obrigatórios
    required = PLATFORMS.get(platform, {}).get("fields", [])
    config = json.loads(store.get("config_json", "{}") or "{}")
    
    missing = []
    for field in required:
        if not store.get("api_key") and not store.get("access_token") and not config.get(field):
            # Verifica se algum campo foi preenchido
            pass
    
    # No MVP, considera conectado se ao menos api_key ou access_token foi fornecido
    has_credentials = bool(store.get("api_key") or store.get("access_token") or store.get("api_secret"))
    
    if has_credentials:
        return {
            "success": True,
            "message": f"✅ Conectado ao {PLATFORMS.get(platform, {}).get('name', platform)} com sucesso!",
            "store_info": {"name": store.get("name"), "platform": platform}
        }
    else:
        return {
            "success": False,
            "message": f"❌ Credenciais inválidas ou ausentes para {platform}",
        }


# ─────────────────────────────────────────────────────────────────────────────
# PUBLICADOR DE PRODUTOS
# ─────────────────────────────────────────────────────────────────────────────

def publish_product(product: dict, approved_content: dict, store: dict) -> dict:
    """
    Publica um produto aprovado em uma loja integrada.
    
    No MVP: simula a publicação e retorna URL fictícia.
    Para produção real: descomentar o bloco da plataforma correspondente.
    """
    platform = store.get("platform", "")
    product_id = product.get("id", "")
    store_id = store.get("id", 0)
    
    db.log_agent("sistema", f"Publicando em {platform}", product_id)
    
    try:
        # Prepara o listing
        listing = _build_listing(product, approved_content, platform)
        
        # Tenta publicação real
        if platform == "shopee":
            result = _publish_shopee(listing, store)
        elif platform == "dropi":
            result = _publish_dropi(listing, store, product)
        elif platform == "woocommerce":
            result = _publish_woocommerce(listing, store)
        elif platform == "nuvemshop":
            result = _publish_nuvemshop(listing, store)
        else:
            result = _publish_simulated(listing, platform, store)
        
        # Registra publicação no banco
        pub_id = db.save_publication({
            "product_id": product_id,
            "approved_id": approved_content.get("ap_id"),
            "store_id": store_id
        })
        
        db.update_publication(pub_id, {
            "status": "publicado" if result["success"] else "erro",
            "listing_id": result.get("listing_id", ""),
            "listing_url": result.get("listing_url", ""),
            "error": result.get("error", "")
        })
        
        if result["success"]:
            db.update_approved_status(product_id, "publicado")
            db.log_agent("sistema", f"Publicado em {platform}: {result.get('listing_url','')}",
                        product_id, "ok")
        else:
            db.log_agent("sistema", f"Erro ao publicar em {platform}: {result.get('error','')}",
                        product_id, "", "erro")
        
        return result
        
    except Exception as e:
        db.log_agent("sistema", f"Exceção ao publicar: {e}", product_id, str(e), "erro")
        return {"success": False, "error": str(e)}


def _build_listing(product: dict, approved: dict, platform: str) -> dict:
    """Constrói o objeto de listing para a plataforma."""
    title = approved.get("agent_title") or product.get("name", "")
    description = approved.get("agent_description") or product.get("name", "")
    price = approved.get("agent_price") or product.get("ai_price_suggestion") or (product.get("price", 10) * 3)
    
    return {
        "title": title[:120],
        "description": description,
        "price": round(float(price), 2),
        "images": [product.get("image_url", "")],
        "category": product.get("category", ""),
        "stock": 999,  # dropshipping = estoque virtual
        "sku": f"SPF-{product.get('id', '')[:8]}",
        "platform": platform,
    }


def _publish_shopee(listing: dict, store: dict) -> dict:
    """
    Publica produto na Shopee via Open Platform API.
    Documentação: https://open.shopee.com/documents
    
    Para ativar: configure partner_id, partner_key, shop_id, access_token
    na integração da loja.
    """
    # CÓDIGO REAL (descomente quando tiver credenciais):
    # import hashlib, hmac, requests
    # partner_id = int(store.get("api_key", 0))
    # partner_key = store.get("api_secret", "")
    # shop_id = int(store.get("store_id", 0))
    # access_token = store.get("access_token", "")
    # timestamp = int(time.time())
    # path = "/api/v2/product/add_item"
    # base_string = f"{partner_id}{path}{timestamp}{access_token}{shop_id}"
    # sign = hmac.new(partner_key.encode(), base_string.encode(), hashlib.sha256).hexdigest()
    # url = f"https://partner.shopeemobile.com{path}?partner_id={partner_id}&shop_id={shop_id}&timestamp={timestamp}&access_token={access_token}&sign={sign}"
    # payload = {"original_price": listing["price"], "description": listing["description"], ...}
    # response = requests.post(url, json=payload)
    # data = response.json()
    # if data.get("error") == "": return {"success": True, "listing_id": str(data["response"]["item_id"]), ...}
    
    return _publish_simulated(listing, "shopee", store)


def _publish_dropi(listing: dict, store: dict, product: dict) -> dict:
    """
    Envia pedido/produto ao Dropi para fulfillment.
    Dropi automatiza: compra no fornecedor + envio ao cliente.
    
    Para ativar: configure api_key e store_id na integração.
    """
    # CÓDIGO REAL (descomente quando tiver credenciais):
    # import requests
    # headers = {"Authorization": f"Bearer {store.get('api_key')}", "Content-Type": "application/json"}
    # payload = {
    #     "product_url": product.get("link", ""),  # URL do AliExpress
    #     "store_id": store.get("store_id"),
    #     "title": listing["title"],
    #     "price": listing["price"],
    # }
    # response = requests.post("https://api.dropi.com.br/v1/products", json=payload, headers=headers)
    # data = response.json()
    # if data.get("success"): return {"success": True, "listing_id": data["product"]["id"], ...}
    
    return _publish_simulated(listing, "dropi", store)


def _publish_woocommerce(listing: dict, store: dict) -> dict:
    """
    Publica produto via WooCommerce REST API.
    Documentação: https://woocommerce.com/document/woocommerce-rest-api/
    """
    # CÓDIGO REAL (descomente quando tiver credenciais):
    # import requests
    # from requests.auth import HTTPBasicAuth
    # url = f"{store.get('store_url').rstrip('/')}/wp-json/wc/v3/products"
    # auth = HTTPBasicAuth(store.get("api_key"), store.get("api_secret"))
    # payload = {"name": listing["title"], "type": "simple", "regular_price": str(listing["price"]),
    #            "description": listing["description"], "stock_quantity": listing["stock"],
    #            "manage_stock": True, "images": [{"src": img} for img in listing["images"] if img]}
    # response = requests.post(url, json=payload, auth=auth)
    # data = response.json()
    # if response.status_code in [200, 201]:
    #     return {"success": True, "listing_id": str(data["id"]), "listing_url": data.get("permalink", "")}
    
    return _publish_simulated(listing, "woocommerce", store)


def _publish_nuvemshop(listing: dict, store: dict) -> dict:
    """
    Publica produto via Nuvemshop API.
    Documentação: https://tiendanube.github.io/api-documentation/
    """
    # CÓDIGO REAL (descomente quando tiver credenciais):
    # import requests
    # store_id = store.get("store_id")
    # token = store.get("access_token")
    # headers = {"Authentication": f"bearer {token}", "User-Agent": "SmartProductFinder/2.0"}
    # url = f"https://api.nuvemshop.com.br/v1/{store_id}/products"
    # payload = {"name": {"pt": listing["title"]}, "description": {"pt": listing["description"]},
    #            "variants": [{"price": str(listing["price"]), "stock": listing["stock"]}]}
    # response = requests.post(url, json=payload, headers=headers)
    # data = response.json()
    # if response.status_code in [200, 201]:
    #     return {"success": True, "listing_id": str(data["id"]), ...}
    
    return _publish_simulated(listing, "nuvemshop", store)


def _publish_simulated(listing: dict, platform: str, store: dict) -> dict:
    """Simula publicação com dados realistas (modo demo/MVP)."""
    time.sleep(0.3)  # simula latência da API
    
    listing_id = f"{platform[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"
    
    platform_urls = {
        "shopee": f"https://shopee.com.br/product/{random.randint(100000000, 999999999)}",
        "dropi": f"https://dropi.com.br/produtos/{listing_id}",
        "woocommerce": f"{store.get('store_url', 'https://loja.com.br')}/produto/{listing['title'][:20].replace(' ','-').lower()}",
        "nuvemshop": f"https://loja.nuvemshop.com.br/produtos/{listing_id}",
    }
    
    return {
        "success": True,
        "listing_id": listing_id,
        "listing_url": platform_urls.get(platform, f"https://{platform}.com/listing/{listing_id}"),
        "message": f"✅ Publicado com sucesso em {platform} (modo demo)"
    }


# ─────────────────────────────────────────────────────────────────────────────
# SINCRONIZAÇÃO DE PEDIDOS
# ─────────────────────────────────────────────────────────────────────────────

def sync_orders(store: dict) -> list:
    """
    Sincroniza pedidos de uma loja integrada.
    No MVP, gera pedidos simulados. Na versão real, chama a API.
    """
    platform = store.get("platform", "")
    store_id = store.get("id", 0)
    
    db.log_agent("sistema", f"Sincronizando pedidos de {store.get('name')}", 
                 result=f"plataforma: {platform}")
    
    # Busca produtos aprovados desta loja para simular pedidos
    publications = db.get_publications()
    if not publications:
        return []
    
    new_orders = []
    # Gera 1-3 pedidos simulados
    for pub in publications[:random.randint(1, 3)]:
        if pub.get("store_id") != store_id:
            continue
            
        sale_price = round(random.uniform(29.90, 149.90), 2)
        cost = round(sale_price * 0.35, 2)
        profit = round(sale_price - cost - 15, 2)
        
        order_data = {
            "store_id": store_id,
            "publication_id": pub.get("id"),
            "product_id": pub.get("product_id", ""),
            "platform_order_id": f"ORD-{uuid.uuid4().hex[:8].upper()}",
            "customer_name": random.choice(["Ana Silva", "Carlos Santos", "Maria Oliveira", "Pedro Lima"]),
            "customer_email": f"cliente{random.randint(100,999)}@email.com",
            "quantity": random.randint(1, 3),
            "sale_price": sale_price,
            "cost_price": cost,
            "profit": profit,
            "status": "novo",
            "dropi_order_id": None,
        }
        
        order_id = db.save_order(order_data)
        new_orders.append({**order_data, "id": order_id})
    
    db.update_store_last_sync(store_id)
    return new_orders


def send_order_to_dropi(order: dict, dropi_store: dict) -> dict:
    """
    Envia um pedido ao Dropi para fulfillment automático.
    O Dropi compra no fornecedor e envia diretamente ao cliente.
    
    Para ativar: configure a integração Dropi com api_key válida.
    """
    # CÓDIGO REAL:
    # import requests
    # headers = {"Authorization": f"Bearer {dropi_store.get('api_key')}", "Content-Type": "application/json"}
    # payload = {
    #     "external_order_id": order.get("platform_order_id"),
    #     "store_id": dropi_store.get("store_id"),
    #     "product_url": order.get("aliexpress_url"),  # URL do produto no AliExpress
    #     "customer": {
    #         "name": order.get("customer_name"),
    #         "email": order.get("customer_email"),
    #         "address": order.get("shipping_address"),
    #     },
    #     "quantity": order.get("quantity", 1)
    # }
    # response = requests.post("https://api.dropi.com.br/v1/orders", json=payload, headers=headers)
    # data = response.json()
    # if data.get("success"):
    #     db.save_order({**order, "dropi_order_id": data["order"]["id"], "status": "processando"})
    #     return {"success": True, "dropi_order_id": data["order"]["id"]}
    
    # SIMULADO:
    dropi_id = f"DRP-{uuid.uuid4().hex[:8].upper()}"
    return {
        "success": True,
        "dropi_order_id": dropi_id,
        "message": f"Pedido enviado ao Dropi: {dropi_id} (modo demo)"
    }


def get_platform_info(platform: str) -> dict:
    return PLATFORMS.get(platform, {})


def get_all_platforms() -> dict:
    return PLATFORMS
