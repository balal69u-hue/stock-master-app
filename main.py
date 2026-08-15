from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import requests
import json
import urllib.parse
import os
import re
from datetime import datetime


# =========================================================
# TAS MASTER
# Adobe Stock Tracker using ScraperAPI
# =========================================================

app = FastAPI(
    title="TAS Master - Adobe Stock Tracker",
    version="2.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# SCRAPERAPI
# =========================================================

SCRAPER_API_KEY = "6c78c85ef4a662dae7a7655738afc93f"


# =========================================================
# CONSTANTS
# =========================================================

ADOBE_BASE_URL = "https://stock.adobe.com"

SCRAPER_URL = "https://api.scraperapi.com"


# =========================================================
# HOME
# =========================================================

@app.get("/", response_class=Response)
def home():

    if os.path.exists("index.html"):

        with open("index.html", "r", encoding="utf-8") as f:

            return Response(
                content=f.read(),
                media_type="text/html"
            )

    return Response(
        content="""
        <html>
            <head>
                <title>TAS Master</title>
            </head>

            <body>
                <h2>TAS Master Live Engine Active</h2>
                <p>Adobe Stock ScraperAPI backend is running.</p>
            </body>
        </html>
        """,
        media_type="text/html"
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/api/health")
def health():

    return {
        "status": "online",
        "engine": "ScraperAPI",
        "adobe_stock": True,
        "scraperapi_configured": bool(SCRAPER_API_KEY)
    }


# =========================================================
# DATE FORMAT
# =========================================================

def format_date(date_string):

    if not date_string:
        return ""

    try:

        date_part = str(date_string).split("T")[0]

        dt = datetime.strptime(
            date_part,
            "%Y-%m-%d"
        )

        return dt.strftime("%b %d, %Y")

    except Exception:

        return str(date_string)


# =========================================================
# TIME AGO
# =========================================================

def calculate_time_ago(date_string):

    if not date_string:
        return ""

    try:

        date_part = str(date_string).split("T")[0]

        dt = datetime.strptime(
            date_part,
            "%Y-%m-%d"
        )

        today = datetime.now()

        diff_days = (
            today.date() - dt.date()
        ).days

        if diff_days <= 0:
            return "Today"

        if diff_days == 1:
            return "1 day ago"

        if diff_days < 30:
            return f"{diff_days} days ago"

        if diff_days < 365:

            months = diff_days // 30

            if months == 1:
                return "1 month ago"

            return f"{months} months ago"

        years = diff_days // 365

        if years == 1:
            return "1 year ago"

        return f"{years} years ago"

    except Exception:

        return ""


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(value):

    if value is None:
        return ""

    if not isinstance(value, str):
        value = str(value)

    return (
        value
        .replace("\\/", "/")
        .replace("\\\"", '"')
        .strip()
    )


# =========================================================
# EXTRACT KEYWORDS
# =========================================================

def extract_keywords(file_data):

    keywords = file_data.get(
        "keywords",
        []
    )

    result = []

    if isinstance(keywords, list):

        for keyword in keywords:

            if isinstance(keyword, dict):

                name = keyword.get("name")

                if name:
                    result.append(
                        clean_text(name)
                    )

            elif keyword:

                result.append(
                    clean_text(keyword)
                )

    return result


# =========================================================
# CATEGORY
# =========================================================

def extract_category(file_data):

    category = file_data.get(
        "category"
    )

    if isinstance(category, dict):

        return clean_text(
            category.get(
                "name",
                "Graphic Resources"
            )
        )

    if isinstance(category, str):

        return category

    return "Graphic Resources"


# =========================================================
# DOWNLOAD COUNT
# =========================================================

def extract_downloads(file_data):

    possible_fields = [
        "nb_downloads",
        "downloads",
        "download_count",
        "downloadCount"
    ]

    for field in possible_fields:

        value = file_data.get(field)

        if value is not None:

            try:
                return int(value)

            except Exception:
                pass

    # Do NOT invent a number.
    return None


# =========================================================
# BUILD ASSET
# =========================================================

def build_asset(file_data, fallback_query=""):

    asset_id = (
        file_data.get("id")
        or file_data.get("asset_id")
    )

    if not asset_id:
        return None


    title = (
        file_data.get("title")
        or file_data.get("name")
        or f"Stock Asset #{asset_id}"
    )


    thumbnail = (
        file_data.get("thumbnail_500_url")
        or file_data.get("thumbnail_url")
        or file_data.get("thumbnail_300_url")
        or file_data.get("thumbnail_160_url")
        or file_data.get("thumbnail")
        or ""
    )


    thumbnail = clean_text(
        thumbnail
    )


    creation_date = (
        file_data.get("creation_date")
        or file_data.get("creationDate")
        or file_data.get("created")
        or ""
    )


    keywords = extract_keywords(
        file_data
    )


    downloads = extract_downloads(
        file_data
    )


    creator_id = (
        file_data.get("creator_id")
        or file_data.get("creatorId")
    )


    creator_name = (
        file_data.get("creator_name")
        or file_data.get("creatorName")
        or ""
    )


    details_url = (
        file_data.get("details_url")
        or file_data.get("detailsUrl")
        or ""
    )


    if not details_url:

        details_url = (
            f"{ADOBE_BASE_URL}/{asset_id}"
        )


    return {

        "id": str(asset_id),

        "title": clean_text(title),

        "thumbnail": thumbnail,

        "downloads": downloads,

        "downloads_available": (
            downloads is not None
        ),

        "creator_id": creator_id,

        "creator_name": clean_text(
            creator_name
        ),

        "category": extract_category(
            file_data
        ),

        "content_type": (
            file_data.get("content_type")
            or file_data.get("contentType")
            or ""
        ),

        "media_type_id": file_data.get(
            "media_type_id"
        ),

        "vector_type": file_data.get(
            "vector_type"
        ),

        "width": file_data.get(
            "width"
        ),

        "height": file_data.get(
            "height"
        ),

        "creation_date": creation_date,

        "date_formatted": format_date(
            creation_date
        ),

        "time_ago": calculate_time_ago(
            creation_date
        ),

        "tags": (
            ", ".join(keywords)
            if keywords
            else (
                f"{fallback_query.lower()}, "
                "stock"
            )
        ),

        "keywords": keywords,

        "url": details_url
    }


# =========================================================
# FIND JSON OBJECTS IN HTML
# =========================================================

def extract_initial_state(html):

    results = []


    # -----------------------------------------------------
    # Pattern 1
    # -----------------------------------------------------

    patterns = [

        r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;</script>',

        r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*</script>',

        r'<script[^>]*>\s*window\.__INITIAL_STATE__\s*=\s*(\{.*?\});?\s*</script>'
    ]


    for pattern in patterns:

        matches = re.findall(
            pattern,
            html,
            flags=re.DOTALL
        )

        for match in matches:

            try:

                data = json.loads(
                    match
                )

                if isinstance(data, dict):

                    results.append(data)

            except Exception:

                continue


    return results


# =========================================================
# FIND ASSET DATA RECURSIVELY
# =========================================================

def find_asset_lists(obj):

    found = []


    if isinstance(obj, dict):

        # Common Adobe structures
        for key in [
            "items",
            "files",
            "results",
            "assets"
        ]:

            value = obj.get(key)

            if isinstance(value, list):

                if value:

                    # Check whether this looks like assets
                    asset_count = 0

                    for item in value:

                        if isinstance(item, dict):

                            if (
                                item.get("id")
                                or item.get("asset_id")
                            ):
                                asset_count += 1

                    if asset_count > 0:

                        found.append(value)


        for value in obj.values():

            found.extend(
                find_asset_lists(value)
            )


    elif isinstance(obj, list):

        for item in obj:

            found.extend(
                find_asset_lists(item)
            )


    return found


# =========================================================
# SCRAPE ADOBE CONTRIBUTOR PAGE
# =========================================================

def scrape_contributor(
    contributor_id,
    sort_by="relevance",
    limit=100
):

    order_map = {

        "relevance": "relevance",

        "downloads": "nb_downloads",

        "newest": "creation"
    }


    order_value = order_map.get(
        sort_by,
        "relevance"
    )


    adobe_target = (
        f"{ADOBE_BASE_URL}"
        f"/contributor/"
        f"{urllib.parse.quote(contributor_id)}"
        f"?order={order_value}"
        f"&limit={limit}"
    )


    scraper_params = {

        "api_key": SCRAPER_API_KEY,

        "url": adobe_target,

        "render": "true",

        "country_code": "us",

        "device_type": "desktop",

        "keep_headers": "true"
    }


    try:

        response = requests.get(
            SCRAPER_URL,
            params=scraper_params,
            timeout=60
        )

    except requests.RequestException as e:

        raise HTTPException(
            status_code=502,
            detail=(
                "ScraperAPI connection failed: "
                + str(e)
            )
        )


    if response.status_code != 200:

        raise HTTPException(
            status_code=502,
            detail={
                "message":
                    "ScraperAPI returned an error.",

                "status_code":
                    response.status_code,

                "response":
                    response.text[:1000]
            }
        )


    return response.text


# =========================================================
# MAIN TRACK API
# =========================================================

@app.get("/api/track")
def track_adobe_stock(

    query: str,

    search_type: str = "contributor",

    sort_by: str = "relevance",

    media_type: str = "all",

    limit: int = 100
):


    # -----------------------------------------------------
    # CLEAN QUERY
    # -----------------------------------------------------

    clean_q = query.strip()


    if not clean_q:

        raise HTTPException(
            status_code=400,
            detail="Contributor ID is required."
        )


    # -----------------------------------------------------
    # CONTRIBUTOR ID VALIDATION
    # -----------------------------------------------------

    if search_type == "contributor":

        if not clean_q.isdigit():

            raise HTTPException(
                status_code=400,
                detail=(
                    "Contributor ID must contain "
                    "numbers only."
                )
            )


    # -----------------------------------------------------
    # LIMIT
    # -----------------------------------------------------

    limit = max(
        1,
        min(limit, 100)
    )


    # -----------------------------------------------------
    # SCRAPE
    # -----------------------------------------------------

    html = scrape_contributor(
        contributor_id=clean_q,
        sort_by=sort_by,
        limit=limit
    )


    items = []


    # =====================================================
    # METHOD 1
    # INITIAL STATE JSON
    # =====================================================

    states = extract_initial_state(
        html
    )


    for state in states:

        asset_lists = find_asset_lists(
            state
        )


        for asset_list in asset_lists:

            for file_data in asset_list:

                if not isinstance(
                    file_data,
                    dict
                ):
                    continue


                asset = build_asset(
                    file_data,
                    clean_q
                )


                if asset:

                    items.append(
                        asset
                    )


    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================

    unique_items = {}

    for item in items:

        asset_id = item["id"]

        unique_items[
            asset_id
        ] = item


    items = list(
        unique_items.values()
    )


    # =====================================================
    # METHOD 2
    # SEARCH COMMON EMBEDDED JSON
    # =====================================================

    if not items:

        # Look for obvious Adobe asset objects.
        #
        # This is only a fallback.
        # We do NOT invent download numbers.

        patterns = [

            r'"id"\s*:\s*(\d+).*?'
            r'"title"\s*:\s*"([^"]+)".*?'
            r'"thumbnail(?:_500)?_url"\s*:\s*"([^"]+)"',

            r'"id"\s*:\s*"(\d+)".*?'
            r'"title"\s*:\s*"([^"]+)".*?'
            r'"thumbnail(?:_500)?_url"\s*:\s*"([^"]+)"'
        ]


        for pattern in patterns:

            matches = re.findall(
                pattern,
                html,
                flags=re.DOTALL
            )


            for match in matches[:limit]:

                asset_id = match[0]

                title = match[1]

                thumbnail = (
                    match[2]
                    .replace("\\/", "/")
                    .replace("\\u002F", "/")
                )


                item = {

                    "id": str(asset_id),

                    "title": clean_text(
                        title
                    ),

                    "thumbnail": thumbnail,

                    "downloads": None,

                    "downloads_available": False,

                    "creator_id": clean_q,

                    "creator_name": "",

                    "category": (
                        "Vectors"
                        if media_type == "vector"
                        else "Graphic Resources"
                    ),

                    "content_type": "",

                    "media_type_id": None,

                    "vector_type": None,

                    "width": None,

                    "height": None,

                    "creation_date": "",

                    "date_formatted": "",

                    "time_ago": "",

                    "tags": (
                        f"{clean_q.lower()}, "
                        "stock, vector"
                    ),

                    "keywords": [],

                    "url": (
                        f"{ADOBE_BASE_URL}"
                        f"/{asset_id}"
                    )
                }


                unique_items[
                    str(asset_id)
                ] = item


        items = list(
            unique_items.values()
        )


    # =====================================================
    # MEDIA FILTER
    # =====================================================

    if media_type != "all":

        filtered = []

        for item in items:

            content_type = str(
                item.get(
                    "content_type",
                    ""
                )
            ).lower()


            category = str(
                item.get(
                    "category",
                    ""
                )
            ).lower()


            combined = (
                content_type
                + " "
                + category
            )


            if media_type.lower() in combined:

                filtered.append(
                    item
                )


        # Only replace list when
        # filter actually found something.
        if filtered:

            items = filtered


    # =====================================================
    # SORT RESULTS
    # =====================================================

    if sort_by == "downloads":

        # Only assets with known download
        # values are sorted numerically.
        items.sort(
            key=lambda x: (
                x["downloads"]
                if isinstance(
                    x.get("downloads"),
                    int
                )
                else -1
            ),
            reverse=True
        )


    elif sort_by == "newest":

        items.sort(
            key=lambda x:
                x.get(
                    "creation_date",
                    ""
                ),
            reverse=True
        )


    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return {

        "success": True,

        "source": "Adobe Stock via ScraperAPI",

        "query": clean_q,

        "search_type": search_type,

        "sort_by": sort_by,

        "media_type": media_type,

        "total_items": len(items),

        "returned_items": len(items),

        "results": items,

        "scraperapi_used": True,

        "message": (
            "Adobe Stock contributor page "
            "was requested through ScraperAPI."
        )
    }


# =========================================================
# DIRECT SCRAPER TEST
# =========================================================

@app.get("/api/test-scraper")
def test_scraper():

    test_url = (
        "https://stock.adobe.com/"
        "?k=nature"
    )


    params = {

        "api_key": SCRAPER_API_KEY,

        "url": test_url,

        "render": "true",

        "country_code": "us"
    }


    try:

        response = requests.get(
            SCRAPER_URL,
            params=params,
            timeout=60
        )


        return {

            "success":
                response.status_code == 200,

            "status_code":
                response.status_code,

            "content_length":
                len(response.text),

            "message": (
                "ScraperAPI is working."
                if response.status_code == 200
                else "ScraperAPI request failed."
            )
        }


    except Exception as e:

        return {

            "success": False,

            "error": str(e)
        }
