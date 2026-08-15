from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
import requests
import urllib.parse
import os

app = FastAPI(title="Stock Analytics Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def home():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse("<h2>index.html file not found</h2>", status_code=404)

@app.get("/api/search")
def search_stock(keyword: str):
    items = []
    encoded_kw = urllib.parse.quote(keyword)
    
    # Stock API Engine
    try:
        url = f"https://unsplash.com/napi/search/photos?query={encoded_kw}&per_page=20"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            data = res.json()
            for photo in data.get("results", []):
                title = photo.get("alt_description") or photo.get("description") or f"{keyword.title()} Commercial Vector Stock"
                thumb = photo.get("urls", {}).get("small", "")
                if thumb:
                    items.append({
                        "title": title.title(),
                        "thumbnail": thumb,
                        "url": photo.get("links", {}).get("html", "#")
                    })
    except Exception:
        pass

    return {
        "keyword": keyword,
        "count": len(items),
        "results": items
    }
