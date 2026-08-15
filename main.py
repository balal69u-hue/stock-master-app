from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import urllib.parse

app = FastAPI(title="Stock Analytics Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_PAGE = """


    
    
    StockTracker Pro - TAS Master Alternative
    


    
        
            
                ST
                StockTracker Pro
            
            ● Free Engine Active
        
    

    
        
            Stock Keyword & Asset Research
            Discover top-selling concepts, high-performing titles, and metadata instantly.
            
            
                
                
                    Search Assets
                
            
        

        
            
            Fetching stock assets & metadata...
        

        
        
    

    


"""

@app.get("/")
def home():
    return Response(content=HTML_PAGE, media_type="text/html")

@app.get("/api/search")
def search_stock(keyword: str):
    items = []
    encoded_kw = urllib.parse.quote(keyword)
    
    # Unsplash Stock API Engine
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

    # Backup Openverse Stock Engine
    if len(items) == 0:
        try:
            ov_url = f"https://api.openverse.engineering/v1/images/?q={encoded_kw}&page_size=20"
            res = requests.get(ov_url, timeout=8).json()
            for img in res.get("results", []):
                items.append({
                    "title": (img.get("title") or f"{keyword.title()} Asset").title(),
                    "thumbnail": img.get("thumbnail") or img.get("url"),
                    "url": img.get("foreign_landing_url", "#")
                })
        except Exception:
            pass

    return {
        "keyword": keyword,
        "count": len(items),
        "results": items
    }
