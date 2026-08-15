from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import urllib.parse
import os
import re

app = FastAPI(title="Adobe Stock Direct Analytics Engine")

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
    return Response(content="<h2>StockTracker Engine Running...</h2>", media_type="text/html")

@app.get("/api/track")
def track_adobe_stock(query: str, search_type: str = "keyword"):
    items = []
    clean_q = query.strip()
    encoded_q = urllib.parse.quote(clean_q)

    # 1. Build Adobe Target URL by order of Downloads (Top Sales first)
    if search_type == "contributor":
        adobe_url = f"https://stock.adobe.com/Ajax/Search?creator_id={encoded_q}&search_type=creator&limit=48&order=nb_downloads"
    else:
        adobe_url = f"https://stock.adobe.com/Ajax/Search?k={encoded_q}&search_type=usermenu-search&limit=48&order=nb_downloads"

    # Gateway rotation to prevent IP restrictions
    gateways = [
        f"https://api.allorigins.win/raw?url={urllib.parse.quote(adobe_url)}",
        adobe_url
    ]

    for g_url in gateways:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": "https://stock.adobe.com/"
            }
            res = requests.get(g_url, headers=headers, timeout=10)
            if res.status_code == 200:
                raw_text = res.text
                # Parse JSON response
                try:
                    data = json.loads(raw_text)
                except Exception:
                    data = {}

                raw_items = data.get("items", {})
                items_list = list(raw_items.values()) if isinstance(raw_items, dict) else (raw_items if isinstance(raw_items, list) else [])

                for file in items_list:
                    asset_id = file.get("id")
                    title = file.get("title") or f"Stock Asset #{asset_id}"
                    thumb = file.get("thumbnail_500_url") or file.get("thumbnail_url") or ""
                    creator = file.get("creator_name", "Adobe Contributor")
                    
                    # Exact downloads or top rank metrics
                    downloads = file.get("nb_downloads")
                    dl_display = f"{int(downloads):,} Downloads" if (downloads is not None and str(downloads).isdigit()) else "Top Rank Asset"
                    
                    # Extract tags in lowercase with comma
                    raw_kw = file.get("keywords", [])
                    tags_list = []
                    for k in raw_kw:
                        t = k.get("name") if isinstance(k, dict) else str(k)
                        if t:
                            tags_list.append(t.strip().lower())

                    tags_str = ", ".join(tags_list) if tags_list else f"{clean_q.lower()}, vector, graphic, commercial"

                    if thumb:
                        items.append({
                            "id": str(asset_id),
                            "title": title,
                            "thumbnail": thumb,
                            "creator": creator,
                            "downloads": dl_display,
                            "tags": tags_str,
                            "asset_url": f"https://stock.adobe.com/{asset_id}"
                        })

                if len(items) > 0:
                    break
        except Exception:
            continue

    return {
        "query": clean_q,
        "search_type": search_type,
        "count": len(items),
        "results": items
    }
