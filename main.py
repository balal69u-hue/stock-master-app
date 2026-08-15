from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os

app = FastAPI(title="Stock Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"status": "running", "message": "Stock Tracker API is live!"}

@app.get("/api/search")
def search_stock(keyword: str):
    try:
        encoded_kw = urllib.parse.quote(keyword)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }
        url = f"https://stock.adobe.com/search?k={encoded_kw}"
        response = requests.get(url, headers=headers, timeout=15)
        
        soup = BeautifulSoup(response.text, "html.parser")
        items = []
        
        cells = soup.find_all("div", {"data-t": "search-result-cell"})
        for cell in cells[:16]:
            img_tag = cell.find("img")
            link_tag = cell.find("a", href=True)
            
            title = ""
            if img_tag:
                title = img_tag.get("alt") or img_tag.get("title") or ""
            if not title and link_tag:
                title = link_tag.get("title") or ""
            if not title:
                title = f"{keyword.capitalize()} Stock Asset"
                
            thumb = img_tag.get("src", "") if img_tag else ""
            item_url = "https://stock.adobe.com" + link_tag["href"] if link_tag else url
            
            if thumb:
                items.append({
                    "title": title,
                    "thumbnail": thumb,
                    "url": item_url
                })
                
        return {"keyword": keyword, "count": len(items), "results": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
