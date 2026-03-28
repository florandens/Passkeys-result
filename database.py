from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import config as cfg
import basic_database_function as basic_db
import specific_database_function as specific_db
import re 

# ─────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────
def get_collection(uri=cfg.MONGO_URI, db_name=cfg.DATABASE, col_name=cfg.COLLECTION):
    """Return a MongoDB collection object."""
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")          # quick connectivity check
    return client[db_name][col_name]

# ─────────────────────────────────────────────
# DATABASE helper functions
# ─────────────────────────────────────────────
def extract_field(documents, extract_path):
    """Extract a nested field from a list of documents using dot-notation path."""
    def _dig(doc, keys):
        for key in keys:
            if not isinstance(doc, dict):
                return None
            doc = doc.get(key)
        return doc

    keys = extract_path.split(".")
    results = [_dig(doc, keys) for doc in documents]
    results = [r for r in results if r is not None]

    if not results:
        return None
    if len(results) == 1:
        return results[0]      
    return results     

def find_with_regex(data_list, pattern):
    """
    data_list: list of strings
    pattern: regex pattern (string)
    """
    regex = re.compile(pattern, re.IGNORECASE)
    return [item for item in data_list if isinstance(item, str) and regex.search(item)]        

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
    

    #print_table(basic_db.count_documents(col), "Total document count")
    #print_table(specific_db.count_passkeys_supported(col), "passkeys_supported breakdown")
    #print_table(specific_db.search_keyword_in_api_calls(col, "passkey"), "Documents with 'passkey' in API calls")
    #print_table(basic_db.get_field(col, "command.entry.content"), "All URLs with SearchPasskeys data")
    #print_table(basic_db.get_field_where(col, 'command.entry.content', "https://ah.nl", "result.scripts.SearchPasskeys.data.all_api_call"))
    #doc = col.find_one({'command.entry.content': {"$exists": True}})
    #print(doc["command"]["entry"])
    databasehit = basic_db.get_field(
        col,
        "command.entry.content",
        "https://ah.nl")
    #print(databasehit)
    b = extract_field(databasehit, "result.scripts.SearchPasskeys.data.all_api_calls")
    print(b)
if __name__ == "__main__":
    main()