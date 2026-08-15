from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import urllib.parse
import os

app = FastAPI(title="Adobe Stock Analytics Engine")

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
    return Response(content="<h2>System Active.</h2>", media_type="text/html")

@app.get("/api/search")
def search_adobe_stock(keyword: str):
    items = []
    encoded_kw = urllib.parse.quote(keyword)
    
    # 1. Adobe Stock Public Gateway Endpoint
    try:
        url = f"https://stock.adobe.com/Ajax/Search?k={encoded_kw}&search_type=usermenu-search&limit=24&order=relevance"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": f"https://stock.adobe.com/search?k={encoded_kw}"
        }
        res = requests.get(url, headers=headers, timeout=9)
        if res.status_code == 200:
            data = res.json()
            items_raw = data.get("items", {})
            if isinstance(items_raw, dict):
                items_list = list(items_raw.values())
            else:
                items_list = items_raw
                
            for item in items_list:
                thumb = item.get("thumbnail_url") or item.get("thumbnail_500_url") or ""
                title = item.get("title") or f"{keyword.title()} Stock Asset"
                asset_id = item.get("id")
                keywords_data = item.get("keywords", [])
                
                tags = []
                for kw in keywords_data:
                    if isinstance(kw, dict):
                        tags.append(kw.get("name", "").lower())
                    elif isinstance(kw, str):
                        tags.append(kw.lower())
                
                tags_str = ", ".join(tags[:25]) if tags else f"{keyword.lower()}, vector, background, graphic, stock"
                
                if thumb:
                    items.append({
                        "id": str(asset_id),
                        "title": title,
                        "thumbnail": thumb,
                        "tags": tags_str,
                        "url": f"https://stock.adobe.com/{asset_id}"
                    })
    except Exception as e:
        print("Ajax fetch error:", e)

    # 2. Openverse Commercial Creative Stock Fallback
    if len(items) == 0:
        try:
            ov_url = f"https://api.openverse.engineering/v1/images/?q={encoded_kw}&page_size=20"
            res = requests.get(ov_url, headers={"User-Agent": "StockMaster/1.0"}, timeout=8).json()
            for img in res.get("results", []):
                tags_data = [t.get("name", "").lower() for t in img.get("tags", []) if isinstance(t, dict)]
                items.append({
                    "id": str(img.get("id")),
                    "title": (img.get("title") or f"{keyword.title()} Stock Design").title(),
                    "thumbnail": img.get("thumbnail") or img.get("url"),
                    "tags": ", ".join(tags_data[:20]) if tags_data else f"{keyword.lower()}, design, commercial, asset",
                    "url": img.get("foreign_landing_url", "#")
                })
        except Exception as e:
            print("Fallback error:", e)

    return {
        "keyword": keyword,
        "count": len(items),
        "results": items
    }
