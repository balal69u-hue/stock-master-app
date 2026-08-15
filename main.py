from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import urllib.parse
import os
import re
from datetime import datetime

app = FastAPI(title="TAS Master Live Analytics Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCRAPER_API_KEY = "6c78c85ef4a662dae7a7655738afc93f"

@app.get("/", response_class=Response)
def home():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="text/html")
    return Response(content="<h2>TAS Master Live Engine Active</h2>", media_type="text/html")

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
        return "16 days ago", "Jul 30, 2026"

@app.get("/api/track")
def track_adobe_stock(query: str, search_type: str = "contributor", sort_by: str = "relevance"):
    items = []
    clean_q = query.strip()
    encoded_q = urllib.parse.quote(clean_q)
    order_val = "nb_downloads" if sort_by == "downloads" else "relevance"

    # Direct Adobe Ajax Search
    if search_type == "contributor":
        adobe_target = f"https://stock.adobe.com/Ajax/Search?creator_id={encoded_q}&search_type=creator&limit=100&order={order_val}"
    else:
        adobe_target = f"https://stock.adobe.com/Ajax/Search?k={encoded_q}&search_type=usermenu-search&limit=100&order={order_val}"

    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={urllib.parse.quote(adobe_target)}"

    try:
        res = requests.get(scraper_url, timeout=25)
        if res.status_code == 200:
            data = res.json()
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
                        "category": category,
                        "tags": tags_str,
                        "url": f"https://stock.adobe.com/{asset_id}"
                    })
    except Exception as e:
        print(f"Tracking error: {e}")

    if sort_by == "downloads":
        items.sort(key=lambda x: x["downloads"], reverse=True)

    return {
        "query": clean_q,
        "search_type": search_type,
        "total_items": len(items),
        "results": items
    }
