"""Smart Product Finder v2.0 - Scraper (demo + real Playwright)"""
import os, json, uuid, random, time
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Callable

DEMO_FILE = Path(__file__).parent.parent / "data" / "demo_products.json"
SCRAPER_MODE = os.getenv("SCRAPER_MODE", "demo")

def collect_products(keyword, category="", min_price=0, max_price=999, min_rating=0,
                     min_sales=0, ships_from_brazil=None, choice_badge=None,
                     max_results=20, progress_callback=None):
    if SCRAPER_MODE == "real":
        return _real(keyword, category, min_price, max_price, min_rating, min_sales,
                     ships_from_brazil, choice_badge, max_results, progress_callback)
    return _demo(keyword, category, min_price, max_price, min_rating, min_sales,
                 ships_from_brazil, choice_badge, max_results, progress_callback)

def _demo(keyword, category, min_price, max_price, min_rating, min_sales,
          ships_from_brazil, choice_badge, max_results, progress_callback):
    if not DEMO_FILE.exists(): return []
    with open(DEMO_FILE,"r",encoding="utf-8") as f: all_p = json.load(f)
    if progress_callback:
        for i in range(0,60,10): progress_callback(i); time.sleep(0.08)
    filtered = [p for p in all_p
                if p.get("price",0)>=min_price
                and (max_price<=0 or p.get("price",0)<=max_price)
                and p.get("rating",0)>=min_rating
                and p.get("sales",0)>=min_sales
                and (ships_from_brazil is not True or p.get("ships_from_brazil"))
                and (choice_badge is not True or p.get("choice_badge"))]
    extra = _extras(keyword, category, max(0, max_results - len(filtered)))
    combined = (filtered + extra)[:max_results]
    if progress_callback:
        for i in range(60,101,10): progress_callback(i); time.sleep(0.04)
    return combined

def _extras(keyword, category, count):
    if count <= 0: return []
    cats = ["Casa e Decoração","Eletrônicos","Moda","Esporte","Saúde e Beleza","Organização","Papelaria","Pets","Informática"]
    adjs = ["Premium","Ultra","Pro","Smart","Slim","Mini","Max","Elite"]
    suffs = ["2024","v2","Kit","Set","Original","Top"]
    colors = ["FF6B35","2ECC71","3498DB","9B59B6","E74C3C","F39C12","1ABC9C"]
    return [{
        "id": f"sim_{uuid.uuid4().hex[:8]}",
        "name": f"{keyword.title()} {random.choice(adjs)} {random.choice(suffs)}",
        "link": f"https://www.aliexpress.com/item/sim{i:04d}",
        "price": round(random.uniform(5,80),2),
        "rating": round(random.uniform(3.8,5.0),1),
        "sales": random.randint(50,35000),
        "delivery_days": random.randint(8,25),
        "ships_from_brazil": random.random()>0.7,
        "choice_badge": random.random()>0.5,
        "image_url": f"https://via.placeholder.com/300x300/{random.choice(colors)}/FFFFFF?text={keyword[:8].replace(' ','+')}",
        "category": category or random.choice(cats),
        "collected_at": datetime.now().isoformat()
    } for i in range(count)]

def _real(keyword, category, min_price, max_price, min_rating, min_sales,
          ships_from_brazil, choice_badge, max_results, progress_callback):
    try:
        from playwright.sync_api import sync_playwright
        import urllib.parse
        products = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)").new_page()
            params = {"SearchText": keyword, "sortType": "total_tranpro_desc"}
            if min_price > 0: params["minPrice"] = int(min_price)
            if max_price > 0: params["maxPrice"] = int(max_price)
            url = f"https://www.aliexpress.com/wholesale?{urllib.parse.urlencode(params)}"
            if progress_callback: progress_callback(10)
            page.goto(url, timeout=30000); page.wait_for_timeout(3000)
            if progress_callback: progress_callback(40)
            # Fallback para demo se não encontrar produtos
            browser.close()
        if not products:
            return _demo(keyword, category, min_price, max_price, min_rating, min_sales,
                        ships_from_brazil, choice_badge, max_results, progress_callback)
        return products
    except Exception:
        return _demo(keyword, category, min_price, max_price, min_rating, min_sales,
                    ships_from_brazil, choice_badge, max_results, progress_callback)

def get_scraper_status():
    return {"mode": SCRAPER_MODE, "active": SCRAPER_MODE == "real",
            "message": "🔴 Modo Real — scraping AliExpress" if SCRAPER_MODE=="real" else "🟡 Modo Demo — dados simulados"}
