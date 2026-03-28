def count_passkeys_supported(collection):
    PASSKEY_FIELD = "result.scripts.SearchPasskeys.data.passkeys_supported"
    return {
        "true"   : collection.count_documents({PASSKEY_FIELD: True}),
        "false"  : collection.count_documents({PASSKEY_FIELD: False}),
        "missing": collection.count_documents({PASSKEY_FIELD: {"$exists": False}}),
        "total"  : collection.count_documents({}),
    }

def search_keyword_in_api_calls(collection, keyword):
    API_FIELD = "result.scripts.SearchPasskeys.data.all_api_call"
    URL_FIELD = "result.scripts.SearchPasskeys.data.url"
 
    # Only fetch documents that actually have the api_call array
    cursor = collection.find(
        {API_FIELD: {"$exists": True, "$ne": []}},
        {API_FIELD: 1, URL_FIELD: 1, "_id": 0}
    )
 
    results = []
    keyword_lower = keyword.lower()
 
    for doc in cursor:
        data       = doc.get("result", {}).get("scripts", {}).get("SearchPasskeys", {}).get("data", {})
        api_calls  = data.get("all_api_call", [])
        url        = data.get("url", "unknown")
 
        for call in api_calls:
            if isinstance(call, str) and keyword_lower in call.lower():
                results.append({"url": url, "match": call})
                break   # one match per document, then move to the next
 
    return results
