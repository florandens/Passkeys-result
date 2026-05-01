from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import re
import threading
from typing import Collection
import gridfs
from bson import ObjectId
from urllib.parse import urlparse
import basic_database_function as basic_db

PASSKEY_FIELD = "result.scripts.SearchPasskeys.data.passkeys_supported"
BASE_URL_FIELD = "command.entry.content"
LOGIN_PAGE_FIELD = "result.scripts.SearchPasskeys.data.login_page"
HTML_STORE_FIELD = "result.scripts.StoreHTML.data.file_id"
GET_REQUEST_FIELD = "result.scripts.GetRequests.data"
GRIDFS_BUCKET = "_files"


# api calls scanner
def search_api_calls(collection : Collection, api_keywords : list) -> dict:
    if not api_keywords:
        return {}
    #mongo_filter = {LOGIN_PAGE_FIELD: True, GET_REQUEST_FIELD: {"$exists": True}}
    mongo_filter = {}
    pattern = "|".join(api_keywords)

    api_keyword_filter = {
        "$or": [
            # {"url": {"$regex": pattern, "$options": "i"}},
            {"requests.url": {"$regex": pattern, "$options": "i"}},
            {"requests.response.url": {"$regex": pattern, "$options": "i"}},
            {"requests.response.response_headers_extra.set-cookie": {"$regex": pattern, "$options": "i"}},
        ]
    }

    pipeline = [
        {"$match": mongo_filter},
        {"$project": {
            "_id": 0,
            "base_url": f"${BASE_URL_FIELD}",
            "requests": f"${GET_REQUEST_FIELD}",
        }},
        {"$unwind": "$requests"},
        {"$unwind": "$requests"},
        {"$addFields": {"req": "$requests"}},
        {"$match": api_keyword_filter},
        {"$project": {
            "base_url": 1,
            "url": "$req.url",
            "resp_url": "$req.response.url",
            "set_cookie": "$req.response.response_headers_extra.set-cookie",
        }},
        {"$group": {
            "_id": "$base_url",
            "matches": {"$push": "$$ROOT"},
        }},
    ]

    results = {}

    for doc in collection.aggregate(pipeline, allowDiskUse=True):
        base_url = doc["_id"]
        hits = []

        for m in doc["matches"]:
            for kw in api_keywords:
                if m.get("url") and kw in m["url"]:
                    hits.append({"url": m["url"]})
                if m.get("resp_url") and kw in m["resp_url"]:
                    hits.append({"response.url": m["resp_url"]})
                if m.get("set_cookie") and kw in m["set_cookie"]:
                    hits.append({"set-cookie": m["set_cookie"]})

        if hits:
            results[base_url] = hits

    return results


# html scan
def scan_html_keywords(collection : Collection, passkey_keywords : list, oauth_keywords : list, encoding="utf-8") -> dict:
    mongo_filter = {
        LOGIN_PAGE_FIELD: True,
        HTML_STORE_FIELD: {"$exists": True, "$ne": None},
    }
    db = collection.database
    fs = gridfs.GridFS(db, collection=GRIDFS_BUCKET)

    passkey_re = re.compile("|".join(passkey_keywords), re.I) if passkey_keywords else None
    oauth_re   = re.compile("|".join(oauth_keywords),   re.I) if oauth_keywords   else None

    task_queue = queue.Queue(maxsize=200)
    SENTINEL = object()

    # prodcuer scans documents and enqueues file_ids for workers to process
    def producer():
        seen_domains = set()
        for doc in collection.find(
            mongo_filter,
            projection={BASE_URL_FIELD: 1, HTML_STORE_FIELD: 1, "_id": 0},
        ):
            
            raw_ids  = basic_db._dig(doc, HTML_STORE_FIELD) or []
            base_url = basic_db._dig(doc, BASE_URL_FIELD)
            base_url = base_url[0] if isinstance(base_url, list) else base_url
            if not base_url:
                continue

            domain = urlparse(base_url).netloc.replace("www.", "")
            if domain in seen_domains:
                continue
            seen_domains.add(domain)

            for raw_id in raw_ids:
                file_id = raw_id
                if isinstance(file_id, str):
                    try:
                        file_id = ObjectId(file_id)
                    except Exception:
                        continue
                if isinstance(file_id, ObjectId):
                    # Pass domain along so workers can record which site matched
                    task_queue.put((file_id, base_url))

        task_queue.put(SENTINEL)

    # worker threads consume file_ids, fetch HTML from GridFS, and scan for keywords
    def worker():
        p_local = 0
        o_local = 0
        passkey_domains = []
        oauth_domains   = []

        while True:
            item = task_queue.get()
            if item is SENTINEL:
                task_queue.put(SENTINEL)
                break

            file_id, domain = item
            try:
                html = fs.get(file_id).read().decode(encoding, errors="replace")
            except gridfs.errors.NoFile:
                continue

            if passkey_re and passkey_re.search(html):
                p_local += 1
                passkey_domains.append(domain)

            if oauth_re and oauth_re.search(html):
                o_local += 1
                oauth_domains.append(domain)

        return p_local, o_local, passkey_domains, oauth_domains

    # launch producer and workers
    producer_thread = threading.Thread(target=producer, daemon=True)
    producer_thread.start()

    passkey_count = oauth_count = 0
    all_passkey_domains = []
    all_oauth_domains   = []

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(worker) for _ in range(50)]
        for f in as_completed(futures):
            p, o, p_domains, o_domains = f.result()
            passkey_count += p
            oauth_count   += o
            all_passkey_domains.extend(p_domains)
            all_oauth_domains.extend(o_domains)

    producer_thread.join()

    return {
        "passkey": {
            "count":   passkey_count,
            "domains": sorted(set(all_passkey_domains)),
        },
        "oauth": {
            "count":   oauth_count,
            "domains": sorted(set(all_oauth_domains)),
        },
    }