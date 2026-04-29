from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import config as cfg
import basic_database_function as basic_db
import specific_database_function as specific_db
import json

PASSKEY_ARRAY_LIST = ["passkey", "passkeys", "webauthn"]
OAUTH_ARRAY_LIST = ["login with", "sign in with", "oauth", "openid", "oidc", "sso"]
API_KEYWORD_LIST = ["Webauthn-rs", "SimpleWebAuthn", "@passwordless-id/webauthn", "yubico"] #https://passkeys.dev/docs/tools-libraries/libraries/
#setup connection to MongoDB
def get_collection(uri=cfg.MONGO_URI, db_name=cfg.DATABASE, col_name=cfg.COLLECTION):
    """Return a MongoDB collection object."""
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")          # quick connectivity check
    return client[db_name][col_name]
  

 

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

def write_data_to_file(data, output_path):
    """Write dict/list/scalar data to a file and return written item count."""
    with open(output_path, "w", encoding="utf-8") as f:
        if isinstance(data, dict):
            f.write(json.dumps(data, ensure_ascii=False, indent=2, default=str))
            item_count = len(data)
        elif isinstance(data, list) and data:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
            item_count = len(data)
        elif isinstance(data, list):
            item_count = 0
        else:
            f.write(str(data))
            item_count = 1

    return item_count

def main():
    # Establish connection once
    try:
        col = get_collection()
        print("Connected to MongoDB")
    except ConnectionFailure as e:
        print(f"x Could not connect: {e}")
        return
    """the database count function to every site or subsite in the dataset"""
    #print_table(basic_db.count_documents(col), "Total documents in collection")
    #print_table(basic_db.count_bool_values(col, "result.scripts.SearchPasskeys.data.login_page"), "Have login page breakdown")

    """count in the database every diffrent website it visit, it romove the one that comming form the login generator"""
    #count_website = basic_db.count_by_field_value(col, "command.origin", "UrlGenerator", {"result.scripts.SearchPasskeys.data.website_exists": True})
    #print(f"Count of documents with command.origin='UrlGenerator' and website_exists=True: {count_website}")
    """work with tapi_calles"""
    #test = specific_db.search_passkeys_api_calls(col, ["passkey", "fido", "webauthn"])
    #specific_db.debug_search_passkeys_api_calls(col, ["passkey", "fido", "webauthn"])
    #print(f"Found API calls with specified keywords: {test}")
    #write_data_to_file(test, "api_calls_with_keywords.json")
    #passkey_urls, oauth_urls = specific_db.search_html_for_keywords(col,passkeys_keywoord=["passkey", "fido", "webauthn"], oauth_keywords=["login with google", "login with apple", "login with github","login with facebook", "si"])
    #print_table(different_values_for_field, "Different values for command.origin")
    #print(different_values_for_field)
    #print(urls)
    # Store URLs to text file
    """if passkey_urls:
        item_count = write_data_to_file(passkey_urls, "urlsshort.json")
        print(f"✓ Stored {item_count} entries to urlsshort.json")
    if oauth_urls:
        item_count = write_data_to_file(oauth_urls, "oauth_urls.json")
        print(f"✓ Stored {item_count} entries to oauth_urls.json")"""
    #print_table(urls, "Found URLs with specified keywords") 
   #specific_db.debug_gridfs(col)
    '''api_results, passkey_urls, oauth_urls = pipeline_db.search_passkeys_and_html(
    col,
    api_keywords     = ["passkey", "fido", "webauthn"],
    passkey_keywords = PASSKEY_ARRAY_LIST,
    oauth_keywords   = OAUTH_ARRAY_LIST,
    limit            = 10000,
    )

    write_data_to_file(api_results,   "api_calls_with_keywords.json")
    write_data_to_file(passkey_urls,  "passkey_urls.json")
    write_data_to_file(oauth_urls,    "oauth_urls.json")'''

    api =specific_db.search_api_calls(col, API_KEYWORD_LIST)
    write_data_to_file(api, "api_calls_with_keywords.json")
    #results = specific_db.scan_html_keywords(col, PASSKEY_ARRAY_LIST, OAUTH_ARRAY_LIST)
    #write_data_to_file(results["passkey"], "passkey_urls.json")
    #write_data_to_file(results["oauth"], "oauth_urls.json")

if __name__ == "__main__":
    main()