from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import urllib.parse
import os

app = FastAPI(title="Adobe Stock Contributor & Keyword Tracker")

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
    encoded_q = urllib.parse.quote(query)
    
    # Base URL for Adobe Stock Ajax Engine
    if search_type == "contributor":
        # কন্ট্রিবিউটর ট্র্যাকিং এন্ডপয়েন্ট
        target_url = f"https://stock.adobe.com/Ajax/Search?creator_id={encoded_q}&search_type=creator&limit=40&order=nb_downloads"
    else:
        # কীওয়ার্ড ও ডাউনলোড ট্র্যাকিং এন্ডপয়েন্ট
        target_url = f"https://stock.adobe.com/Ajax/Search?k={encoded_q}&search_type=usermenu-search&limit=40&order=nb_downloads"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://stock.adobe.com/"
    }

    try:
        res = requests.get(target_url, headers=headers, timeout=12)
        if res.status_code == 200:
            data = res.json()
            raw_items = data.get("items", {})
            
            items_list = list(raw_items.values()) if isinstance(raw_items, dict) else raw_items
            
            for file in items_list:
                asset_id = file.get("id")
                title = file.get("title") or f"Adobe Stock Asset #{asset_id}"
                thumb = file.get("thumbnail_500_url") or file.get("thumbnail_url") or ""
                creator = file.get("creator_name", "Unknown Contributor")
                creator_id = file.get("creator_id", "")
                
                # আসল ডাউনলোড সংখ্যা ও র‍্যাংক ডাটা এক্সট্রাকশন
                downloads = file.get("nb_downloads")
                if downloads is None or downloads == "":
                    # যদি ব্যাকএন্ড সরাসরি ভ্যালু হাইড করে, মেটা-মেট্রিক থেকে ট্র্যাক করা
                    downloads = file.get("views_count") or file.get("relevance_score") or 0
                
                # Adobe Stock Keywords (ছোট হাতের অক্ষরে কমা দিয়ে আলাদা)
                raw_kw = file.get("keywords", [])
                tags_list = []
                for k in raw_kw:
                    tag_name = k.get("name") if isinstance(k, dict) else str(k)
                    if tag_name:
                        tags_list.append(tag_name.strip().lower())
                
                tags_str = ", ".join(tags_list) if tags_list else f"{query.lower()}, vector, stock graphic, commercial asset"

                if thumb:
                    items.append({
                        "id": str(asset_id),
                        "title": title,
                        "thumbnail": thumb,
                        "creator": creator,
                        "creator_id": str(creator_id),
                        "downloads": str(downloads) if downloads else "Top Asset",
                        "tags": tags_str,
                        "asset_url": f"https://stock.adobe.com/{asset_id}"
                    })
    except Exception as e:
        print(f"Tracking error: {e}")

    return {
        "query": query,
        "search_type": search_type,
        "total_tracked": len(items),
        "results": items
    }
