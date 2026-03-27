from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import config as cfg
 

 
 
# ─────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────
def get_collection(uri=cfg.MONGO_URI, db_name=cfg.DATABASE, col_name=cfg.COLLECTION):
    """Return a MongoDB collection object."""
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")          # quick connectivity check
    return client[db_name][col_name]

def count_documents(collection, query=None):
    """
    Count documents in the collection.

    Examples:
        count_documents(col)                        → count all
        count_documents(col, {"status": "active"})  → count with filter
    """
    query = query or {}
    result = collection.count_documents(query)
    print(f"Count ({query or 'all'}): {result}")
    return result

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

def print_table(data, title="Result"):                      #AI generated
    """
    Pretty-print any result returned by the functions below.
 
    Accepts:
        int        -> single count value
        dict       -> key/value table
        list[dict] -> table of documents
        list[str]  -> simple list
    """
    print(f"\n{'─' * 44}")
    print(f"  {title}")
    print(f"{'─' * 44}")
 
    if isinstance(data, int):
        print(f"  Count : {data}")
 
    elif isinstance(data, dict):
        for key, val in data.items():
            print(f"  {key:<12}: {val}")
 
    elif isinstance(data, list):
        if not data:
            print("  (no results)")
        elif isinstance(data[0], dict):
            for i, doc in enumerate(data, 1):
                print(f"\n  [{i}]")
                for key, val in doc.items():
                    print(f"    {key}: {val}")
        else:
            for item in data:
                print(f"  • {item}")
 
    else:
        print(f"  {data}")
 
    print(f"{'─' * 44}\n")
def main():
    # Establish connection once
    try:
        col = get_collection()
        print("✓ Connected to MongoDB")
    except ConnectionFailure as e:
        print(f"✗ Could not connect: {e}")
        return
    

    print_table(count_documents(col), "Total document count")
    print_table(count_passkeys_supported(col), "passkeys_supported breakdown")
    print_table(search_keyword_in_api_calls(col, "passkey"), "Documents with 'passkey' in API calls")

if __name__ == "__main__":
    main()