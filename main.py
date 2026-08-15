from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = FastAPI(title="Stock Analytics Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_CONTENT = """


    
    
    StockTracker Pro - TAS Master Alternative
    



    
    
        
            
                ST
                StockTracker Pro
            
            ● System Active (Free)
        
    

    
    
        
            Stock Keyword & Asset Research
            Search any niche to discover real trending concepts, commercial titles, and high-ranking tags.
            
            
                
                
                    Search Assets
                
            
        

        
        
            
            Fetching live marketplace data...
        

        
        

        
        
    

    


"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(content=HTML_CONTENT)

@app.get("/api/search")
def search_stock(keyword: str):
    items = []
    encoded_kw = urllib.parse.quote(keyword)
    
    # 1. Adobe Stock Scraper
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        url = f"https://stock.adobe.com/search?k={encoded_kw}"
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            cells = soup.find_all("div", {"data-t": "search-result-cell"})
            for cell in cells[:16]:
                img_tag = cell.find("img")
                link_tag = cell.find("a", href=True)
                title = (img_tag.get("alt") if img_tag else "") or (link_tag.get("title") if link_tag else "") or f"{keyword.title()} Stock Asset"
                thumb = img_tag.get("src", "") if img_tag else ""
                item_url = "https://stock.adobe.com" + link_tag["href"] if link_tag else url
                if thumb and "http" in thumb:
                    items.append({"title": title, "thumbnail": thumb, "url": item_url})
    except Exception:
        pass

    # 2. Smart High-Quality Fallback
    if len(items) == 0:
        try:
            backup_url = f"https://lexica.art/api/v1/search?q={encoded_kw}"
            b_res = requests.get(backup_url, timeout=6).json()
            if "images" in b_res:
                for img in b_res["images"][:16]:
                    items.append({
                        "title": img.get("prompt", f"{keyword.title()} Commercial Concept")[:90],
                        "thumbnail": img.get("srcSmall", img.get("src")),
                        "url": f"https://stock.adobe.com/search?k={encoded_kw}"
                    })
        except Exception:
            pass

    return {
        "keyword": keyword,
        "count": len(items),
        "results": items
    }
