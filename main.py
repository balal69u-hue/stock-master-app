from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import urllib.parse
import os
import re
from datetime import datetime

app = FastAPI(title="Adobe Stock Contributor Real-Time Engine")

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
    return Response(content="<h2>TAS Master Tracker Running...</h2>", media_type="text/html")

def calculate_time_ago(date_str):
    try:
        dt = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d")
        now = datetime.utcnow()
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

    # 1. Real Contributor URL with Download Order
    if search_type == "contributor":
        order = "nb_downloads" if sort_by == "downloads" else "relevance"
        target_url = f"https://stock.adobe.com/contributor/{encoded_q}?order={order}&limit=100"
    else:
        order = "nb_downloads" if sort_by == "downloads" else "relevance"
        target_url = f"https://stock.adobe.com/search?k={encoded_q}&order={order}&limit=100"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

    try:
        session = requests.Session()
        res = session.get(target_url, headers=headers, timeout=12)
        
        if res.status_code == 200:
            # Extract Adobe's Internal State JSON
            matches = re.findall(r'window\.__INITIAL_STATE__\s*=\s*({.*?});</script>', res.text)
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
                    
                    creation_date = file.get("creation_date") or ""
                    time_ago, date_formatted = calculate_time_ago(creation_date)
                    
                    category = "Graphic Resources"
                    if isinstance(file.get("category"), dict):
                        category = file.get("category").get("name", "Graphic Resources")
                    
                    # Exact lowercase comma-separated keywords
                    raw_kw = file.get("keywords", [])
                    tags_list = []
                    for k in raw_kw:
                        t = k.get("name") if isinstance(k, dict) else str(k)
                        if t:
                            tags_list.append(t.strip().lower())
                    
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
        print(f"Error parsing state: {e}")

    # Fallback to direct Ajax Gateway
    if len(items) == 0:
        try:
            ajax_url = f"https://stock.adobe.com/Ajax/Search?creator_id={encoded_q}&search_type=creator&limit=60&order=nb_downloads"
            a_res = requests.get(ajax_url, headers={"User-Agent": headers["User-Agent"], "X-Requested-With": "XMLHttpRequest"}, timeout=10)
            if a_res.status_code == 200:
                a_data = a_res.json()
                raw_items = a_data.get("items", {})
                items_list = list(raw_items.values()) if isinstance(raw_items, dict) else raw_items
                for file in items_list:
                    thumb = file.get("thumbnail_500_url") or file.get("thumbnail_url") or ""
                    if thumb:
                        raw_kw = file.get("keywords", [])
                        tags_list = [k.get("name", "").lower() if isinstance(k, dict) else str(k).lower() for k in raw_kw if k]
                        items.append({
                            "id": str(file.get("id")),
                            "title": file.get("title", f"Stock #{file.get('id')}"),
                            "thumbnail": thumb,
                            "downloads": int(file.get("nb_downloads") or 0),
                            "time_ago": "Active",
                            "date_formatted": "2026",
                            "category": "Illustrations",
                            "tags": ", ".join(tags_list),
                            "url": f"https://stock.adobe.com/{file.get('id')}"
                        })
        except Exception:
            pass

    # Sort descending by downloads if requested
    if sort_by == "downloads":
        items.sort(key=lambda x: x["downloads"], reverse=True)

    return {
        "query": clean_q,
        "search_type": search_type,
        "total_items": len(items),
        "results": items
    }
