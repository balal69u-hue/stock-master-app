from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import urllib.parse
import os
import re
from datetime import datetime

app = FastAPI(title="TAS Master Real-Time Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=Response)
def home():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="text/html")
    return Response(content="<h2>TAS Master Engine Running...</h2>", media_type="text/html")

def calculate_time_ago(date_str):
    try:
        dt = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d")
        now = datetime(2026, 8, 16)
        diff_days = (now - dt).days
        if diff_days < 30:
            return f"{max(1, diff_days)} days ago", dt.strftime("%b %d, %Y")
        months = max(1, diff_days // 30)
        return f"{months} months ago", dt.strftime("%b %d, %Y")
    except Exception:
        return "Recent", "2026"

@app.get("/api/track")
def track_adobe_stock(query: str, search_type: str = "contributor", sort_by: str = "relevance"):
    items = []
    clean_q = query.strip()
    encoded_q = urllib.parse.quote(clean_q)
    order_val = "nb_downloads" if sort_by == "downloads" else "relevance"

    # Adobe Target URLs
    target_urls = []
    if search_type == "contributor":
        target_urls = [
            f"https://stock.adobe.com/Ajax/Search?creator_id={encoded_q}&search_type=creator&limit=100&order={order_val}",
            f"https://stock.adobe.com/contributor/{encoded_q}?order={order_val}&limit=100"
        ]
    else:
        target_urls = [
            f"https://stock.adobe.com/Ajax/Search?k={encoded_q}&search_type=usermenu-search&limit=100&order={order_val}",
            f"https://stock.adobe.com/search?k={encoded_q}&order={order_val}&limit=100"
        ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Requested-With": "XMLHttpRequest"
    }

    # Strategy 1: Direct & Proxied requests to bypass Cloudflare DC blocks
    for t_url in target_urls:
        proxied_endpoints = [
            t_url,
            f"https://api.allorigins.win/raw?url={urllib.parse.quote(t_url)}",
            f"https://corsproxy.io/?{urllib.parse.quote(t_url)}"
        ]
        
        for ep in proxied_endpoints:
            try:
                res = requests.get(ep, headers=headers, timeout=8)
                if res.status_code == 200:
                    text_resp = res.text
                    
                    # 1. Parse JSON response (Ajax)
                    try:
                        data = json.loads(text_resp)
                        raw_items = data.get("items", {})
                        items_list = list(raw_items.values()) if isinstance(raw_items, dict) else (raw_items if isinstance(raw_items, list) else [])
                        
                        for file in items_list:
                            asset_id = file.get("id")
                            title = file.get("title") or f"Stock Asset #{asset_id}"
                            thumb = file.get("thumbnail_500_url") or file.get("thumbnail_url") or ""
                            downloads = file.get("nb_downloads", 0)
                            
                            creation_date = file.get("creation_date") or "2026-04-01"
                            time_ago, date_formatted = calculate_time_ago(creation_date)
                            
                            category = "Graphic Resources"
                            if isinstance(file.get("category"), dict):
                                category = file.get("category").get("name", "Graphic Resources")
                                
                            raw_kw = file.get("keywords", [])
                            tags_list = [k.get("name", "").lower() if isinstance(k, dict) else str(k).lower() for k in raw_kw if k]
                            tags_str = ", ".join(tags_list)

                            if thumb:
                                items.append({
                                    "id": str(asset_id),
                                    "title": title,
                                    "thumbnail": thumb,
                                    "downloads": int(downloads) if downloads else 0,
                                    "time_ago": time_ago,
                                    "date_formatted": date_formatted,
                                    "category": category or "Vectors",
                                    "tags": tags_str,
                                    "url": f"https://stock.adobe.com/{asset_id}"
                                })
                    except Exception:
                        pass

                    # 2. Parse HTML Initial State if JSON is not returned
                    if len(items) == 0:
                        matches = re.findall(r'window\.__INITIAL_STATE__\s*=\s*({.*?});</script>', text_resp)
                        if matches:
                            init_data = json.loads(matches[0])
                            search_results = init_data.get("search", {}).get("results", {}).get("items", [])
                            for file in search_results:
                                asset_id = file.get("id")
                                title = file.get("title") or f"Stock Asset #{asset_id}"
                                thumb = file.get("thumbnail_500_url") or file.get("thumbnail_url") or ""
                                downloads = file.get("nb_downloads", 0)
                                creation_date = file.get("creation_date") or "2026-01-01"
                                time_ago, date_formatted = calculate_time_ago(creation_date)
                                
                                category = "Graphic Resources"
                                if isinstance(file.get("category"), dict):
                                    category = file.get("category").get("name", "Graphic Resources")

                                raw_kw = file.get("keywords", [])
                                tags_list = [k.get("name", "").lower() if isinstance(k, dict) else str(k).lower() for k in raw_kw if k]

                                if thumb:
                                    items.append({
                                        "id": str(asset_id),
                                        "title": title,
                                        "thumbnail": thumb,
                                        "downloads": int(downloads) if downloads else 0,
                                        "time_ago": time_ago,
                                        "date_formatted": date_formatted,
                                        "category": category,
                                        "tags": ", ".join(tags_list),
                                        "url": f"https://stock.adobe.com/{asset_id}"
                                    })

                    if len(items) > 0:
                        break
            except Exception:
                continue
        if len(items) > 0:
            break

    # Sort descending by downloads if requested
    if sort_by == "downloads":
        items.sort(key=lambda x: x["downloads"], reverse=True)

    return {
        "query": clean_q,
        "search_type": search_type,
        "total_items": len(items),
        "results": items
    }
