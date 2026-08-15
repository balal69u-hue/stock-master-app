from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import urllib.parse
import os
import re
from datetime import datetime

app = FastAPI(title="TAS Master Clone Engine")

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
        months = diff_days // 30
        return f"{months} months ago", dt.strftime("%b %d, %Y")
    except Exception:
        return "Recent", "2026"

@app.get("/api/track")
def track_adobe_stock(query: str, search_type: str = "contributor", sort_by: str = "relevance", content_type: str = "all"):
    items = []
    clean_q = query.strip()
    encoded_q = urllib.parse.quote(clean_q)

    # Sort parameter mapping
    order_param = "relevance"
    if sort_by == "downloads":
        order_param = "nb_downloads"
    elif sort_by == "newest":
        order_param = "creation_date"

    # Direct Adobe Stock Gateway Request
    if search_type == "contributor":
        api_url = f"https://stock.adobe.com/Ajax/Search?creator_id={encoded_q}&search_type=creator&limit=100&order={order_param}"
    else:
        api_url = f"https://stock.adobe.com/Ajax/Search?k={encoded_q}&search_type=usermenu-search&limit=100&order={order_param}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": f"https://stock.adobe.com/contributor/{encoded_q}"
    }

    try:
        res = requests.get(api_url, headers=headers, timeout=12)
        if res.status_code == 200:
            data = res.json()
            raw_items = data.get("items", {})
            items_list = list(raw_items.values()) if isinstance(raw_items, dict) else (raw_items if isinstance(raw_items, list) else [])

            for file in items_list:
                asset_id = file.get("id")
                title = file.get("title") or f"Stock Asset #{asset_id}"
                thumb = file.get("thumbnail_500_url") or file.get("thumbnail_url") or ""
                downloads = file.get("nb_downloads", 0)
                if downloads is None or downloads == "":
                    downloads = 0
                
                creation_date = file.get("creation_date") or "2026-04-01"
                time_ago, date_formatted = calculate_time_ago(creation_date)
                
                category = file.get("category", {}).get("name") if isinstance(file.get("category"), dict) else "Graphic Resources"
                
                # Tags parsing
                raw_kw = file.get("keywords", [])
                tags_list = []
                for k in raw_kw:
                    t = k.get("name") if isinstance(k, dict) else str(k)
                    if t:
                        tags_list.append(t.strip().lower())
                
                tags_str = ", ".join(tags_list) if tags_list else f"{clean_q.lower()}, vector, stock, commercial"

                if thumb:
                    items.append({
                        "id": str(asset_id),
                        "title": title,
                        "thumbnail": thumb,
                        "downloads": int(downloads),
                        "time_ago": time_ago,
                        "date_formatted": date_formatted,
                        "category": category or "Vectors",
                        "tags": tags_str,
                        "url": f"https://stock.adobe.com/{asset_id}"
                    })
    except Exception as e:
        print(f"Error fetching data: {e}")

    # Fallback to direct Adobe HTML structure if Ajax returns empty
    if len(items) == 0:
        try:
            html_url = f"https://stock.adobe.com/contributor/{encoded_q}" if search_type == "contributor" else f"https://stock.adobe.com/search?k={encoded_kw}"
            h_res = requests.get(html_url, headers=headers, timeout=12)
            if h_res.status_code == 200:
                matches = re.findall(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', h_res.text)
                if matches:
                    init_data = json.loads(matches[0])
                    files = init_data.get("search", {}).get("results", {}).get("items", [])
                    for f in files:
                        items.append({
                            "id": str(f.get("id")),
                            "title": f.get("title", f"Adobe Stock #{f.get('id')}"),
                            "thumbnail": f.get("thumbnail_url", ""),
                            "downloads": int(f.get("nb_downloads", 0)),
                            "time_ago": "Recent",
                            "date_formatted": "Aug 2026",
                            "category": "Illustration",
                            "tags": ", ".join([k.lower() for k in f.get("keywords", [])]),
                            "url": f"https://stock.adobe.com/{f.get('id')}"
                        })
        except Exception:
            pass

    return {
        "query": clean_q,
        "search_type": search_type,
        "total_items": len(items),
        "results": items
    }
