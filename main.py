from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import urllib.parse
import os

app = FastAPI(title="Adobe Stock Real-Time Analytics Engine")

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
    return Response(content="System Active. Loading...", media_type="text/html")

@app.get("/api/search")
def search_adobe_stock(keyword: str):
    items = []
    encoded_kw = urllib.parse.quote(keyword)
    
    # Direct Adobe Stock Engine Endpoint
    adobe_api_url = (
        f"https://stock.adobe.com/Rest/Libraries/1/Search/Files?"
        f"locale=en_US&search_parameters[words]={encoded_kw}&"
        f"search_parameters[limit]=24&"
        f"search_parameters[order]=relevance&"
        f"result_columns[]=id&"
        f"result_columns[]=title&"
        f"result_columns[]=thumbnail_url&"
        f"result_columns[]=thumbnail_500_url&"
        f"result_columns[]=keywords&"
        f"result_columns[]=creator_name&"
        f"result_columns[]=nb_downloads"
    )
    
    headers = {
        "x-product": "StockSearch/1.0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        res = requests.get(adobe_api_url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            files = data.get("files", [])
            
            for file in files:
                title = file.get("title") or f"{keyword.title()} Asset"
                thumb = file.get("thumbnail_500_url") or file.get("thumbnail_url") or ""
                asset_id = file.get("id")
                creator = file.get("creator_name", "Contributor")
                downloads = file.get("nb_downloads", 0)
                
                # Tags list extraction
                tags_list = []
                for kw_item in file.get("keywords", []):
                    if isinstance(kw_item, dict):
                        tags_list.append(kw_item.get("name", "").lower())
                    elif isinstance(kw_item, str):
                        tags_list.append(kw_item.lower())
                
                tags_str = ", ".join(tags_list[:25]) if tags_list else f"{keyword.lower()}, stock, vector, commercial"
                
                if thumb:
                    items.append({
                        "id": str(asset_id),
                        "title": title,
                        "thumbnail": thumb,
                        "creator": creator,
                        "downloads": f"{downloads:,}" if downloads else "High Demand",
                        "tags": tags_str,
                        "url": f"https://stock.adobe.com/{asset_id}"
                    })
    except Exception as e:
        print(f"Error fetching Adobe Stock: {e}")

    return {
        "keyword": keyword,
        "source": "Adobe Stock Real-Time",
        "count": len(items),
        "results": items
    }
