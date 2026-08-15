from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
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

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockTracker Pro - TAS Master Alternative</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-white min-h-screen font-sans">
    <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50 p-4">
        <div class="max-w-6xl mx-auto flex justify-between items-center">
            <div class="flex items-center space-x-2">
                <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/30">ST</div>
                <h1 class="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">StockTracker Pro</h1>
            </div>
            <span class="text-xs bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-full border border-emerald-500/20 font-medium">● Free Active</span>
        </div>
    </header>

    <main class="max-w-6xl mx-auto px-4 py-12">
        <div class="text-center max-w-2xl mx-auto mb-10">
            <h2 class="text-3xl sm:text-4xl font-extrabold tracking-tight mb-3">Stock Keyword & Asset Research</h2>
            <p class="text-slate-400 text-sm">Discover trending assets, titles, and download ideas instantly</p>
            
            <div class="mt-8 flex flex-col sm:flex-row gap-2">
                <input id="searchInput" type="text" placeholder="e.g. sunset landscape, cyber technology, business ai" 
                    class="w-full px-4 py-3.5 rounded-xl bg-slate-900 border border-slate-800 focus:outline-none focus:border-blue-500 text-white placeholder-slate-500 text-sm shadow-inner"
                    onkeypress="if(event.key === 'Enter') fetchData()">
                <button onclick="fetchData()" class="bg-blue-600 hover:bg-blue-500 text-white px-8 py-3.5 rounded-xl font-semibold text-sm transition shadow-lg shadow-blue-600/30 whitespace-nowrap">
                    Search Assets
                </button>
            </div>
        </div>

        <div id="loader" class="hidden text-center py-16">
            <div class="inline-block animate-spin rounded-full h-10 w-10 border-4 border-slate-700 border-t-blue-500 mb-3"></div>
            <p class="text-slate-400 text-sm">Fetching live marketplace data...</p>
        </div>

        <div id="noticeBox" class="hidden max-w-xl mx-auto mb-8 p-4 rounded-xl text-xs text-center border"></div>
        <div id="resultsGrid" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6"></div>
    </main>

    <script>
        async function fetchData() {
            const query = document.getElementById("searchInput").value.trim();
            if(!query) return alert("Please type a keyword!");

            const grid = document.getElementById("resultsGrid");
            const loader = document.getElementById("loader");
            const noticeBox = document.getElementById("noticeBox");
            
            grid.innerHTML = "";
            noticeBox.className = "hidden max-w-xl mx-auto mb-8 p-4 rounded-xl text-xs text-center border";
            noticeBox.innerText = "";
            loader.classList.remove("hidden");

            try {
                const res = await fetch(`/api/search?keyword=${encodeURIComponent(query)}`);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                loader.classList.add("hidden");

                if (!data.results || data.results.length === 0) {
                    noticeBox.className = "max-w-xl mx-auto mb-8 p-4 rounded-xl text-xs text-center border bg-slate-900 border-slate-800 text-slate-400 block";
                    noticeBox.innerText = `No assets found for "${query}". Try another search term.`;
                    return;
                }

                data.results.forEach(item => {
                    const card = document.createElement("div");
                    card.className = "bg-slate-900/90 border border-slate-800/80 rounded-2xl overflow-hidden shadow-lg hover:border-slate-700 transition flex flex-col justify-between group";
                    card.innerHTML = `
                        <div class="h-48 bg-slate-950 overflow-hidden relative">
                            <img src="${item.thumbnail}" alt="${item.title}" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400'">
                        </div>
                        <div class="p-4 flex flex-col justify-between flex-grow">
                            <p class="text-xs text-slate-300 font-medium line-clamp-2 mb-4 leading-relaxed" title="${item.title}">${item.title}</p>
                            <button onclick="copyText('${item.title.replace(/'/g, "\\'")}', this)" 
                                class="w-full text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 py-2.5 rounded-lg font-semibold transition border border-slate-700/50">
                                Copy Title
                            </button>
                        </div>
                    `;
                    grid.appendChild(card);
                });
            } catch (err) {
                loader.classList.add("hidden");
                noticeBox.className = "max-w-xl mx-auto mb-8 p-4 rounded-xl text-xs text-center border bg-rose-500/10 border-rose-500/20 text-rose-400 block";
                noticeBox.innerText = "Error loading data. Please wait a few seconds and try again.";
            }
        }

        function copyText(text, btn) {
            navigator.clipboard.writeText(text);
            const originalText = btn.innerText;
            btn.innerText = "✓ Copied!";
            btn.classList.add("bg-emerald-600", "text-white");
            setTimeout(() => {
                btn.innerText = originalText;
                btn.classList.remove("bg-emerald-600", "text-white");
            }, 2000);
        }
    </script>
</body>
</html>
"""

@app.get("/")
def home():
    return Response(content=HTML_PAGE, media_type="text/html")

@app.get("/api/search")
def search_stock(keyword: str):
    items = []
    encoded_kw = urllib.parse.quote(keyword)
    
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
                title = (img_tag.get("alt") if img_tag else "") or (link_tag.get("title") if link_tag else "") or f"{keyword.title()} Asset"
                thumb = img_tag.get("src", "") if img_tag else ""
                item_url = "https://stock.adobe.com" + link_tag["href"] if link_tag else url
                if thumb and "http" in thumb:
                    items.append({"title": title, "thumbnail": thumb, "url": item_url})
    except Exception:
        pass

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

    return {"keyword": keyword, "count": len(items), "results": items}
