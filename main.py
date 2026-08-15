from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import urllib.parse
import os
import re
from datetime import datetime

app = FastAPI(title="TAS Master Engine")

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

    # 1. Adobe Real Contributor Target
    if search_type == "contributor":
        adobe_target = f"https://stock.adobe.com/contributor/{encoded_q}?order={order_val}&limit=100"
    else:
        adobe_target = f"https://stock.adobe.com/search?k={encoded_q}&order={order_val}&limit=100"

    # ScraperAPI with Full JS Bypass
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={urllib.parse.quote(adobe_target)}&country_code=us"

    try:
        res = requests.get(scraper_url, timeout=35)
        if res.status_code == 200:
            html_text = res.text

            # Parse Adobe's Internal State
            matches = re.findall(r'window\.__INITIAL_STATE__\s*=\s*({.*?});</script>', html_text)
            if matches:
                init_data = json.loads(matches[0])
                search_data = init_data.get("search", {})
                results_data = search_data.get("results", {})
                raw_items = results_data.get("items", [])

                for file in raw_items:
                    asset_id = file.get("id")
                    title = file.get("title") or f"Adobe Stock #{asset_id}"
                    thumb = file.get("thumbnail_500_url") or file.get("thumbnail_url") or ""
                    downloads = file.get("nb_downloads", 0)
                    
                    creation_date = file.get("creation_date") or "2026-01-01"
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

            # Backup DOM Regex Search
            if len(items) == 0:
                json_blocks = re.findall(r'{"id":\d+,"title":".*?","thumbnail_url":".*?"}', html_text)
                for block in json_blocks[:100]:
                    try:
                        f = json.loads(block)
                        items.append({
                            "id": str(f.get("id")),
                            "title": f.get("title"),
                            "thumbnail": f.get("thumbnail_500_url") or f.get("thumbnail_url"),
                            "downloads": int(f.get("nb_downloads") or 0),
                            "time_ago": "Active",
                            "date_formatted": "2026",
                            "category": "Vectors",
                            "tags": "vector, graphic, commercial asset",
                            "url": f"https://stock.adobe.com/{f.get('id')}"
                        })
                    except Exception:
                        pass
    except Exception as e:
        print(f"Error: {e}")

    if sort_by == "downloads":
        items.sort(key=lambda x: x["downloads"], reverse=True)

    return {
        "query": clean_q,
        "search_type": search_type,
        "total_items": len(items),
        "results": items
    }
