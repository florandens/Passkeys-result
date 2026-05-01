import re
from typing import Collection



def _dig(doc, path):
    keys = path.replace("[", ".").replace("]", "").split(".")
    
    def walk(node, i):
        if node is None:
            return []

        if i == len(keys):
            return [node]

        key = keys[i]

        if isinstance(node, list):
            out = []
            for item in node:
                out.extend(walk(item, i))
            return out

        if isinstance(node, dict):
            return walk(node.get(key), i + 1)

        return []

    return walk(doc, 0)

def get_field_values(
    collection : Collection,
    field_path : str,
    query=None,
    protection=None,
) -> list:
    """
    Return the value at a nested field path for every matching document.

    Args:
        collection: PyMongo collection object.
        field_path: Dot-notation path to extract.
        query: Optional extra Mongo filter.
        values_only: If True, return raw values only.
        flatten: If True and the extracted value is a list, extend results with
            list items instead of appending the full list.

    Example:
        x = get_field_values(col, "command.entry.content")
        print_table(x, "command.entry.content")
    """
    query = query or {}

    mongo_query = {field_path: {"$exists": True}}
    if query:
        mongo_query.update(query)
    base_protection = {field_path: 1, "_id": 0}
    if protection:
        base_protection.update(protection)
    
        

    cursor = collection.find(
        mongo_query,
        projection=base_protection
    ).limit(10000)
    key_list = list(protection.keys())
    adding_data = key_list[0]
    results = {}
    
    for doc in cursor:
        value = doc
        for key in adding_data.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
        print(value)
        add_info = value
        value = doc
        for key in field_path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
        
        if value is None:
            continue
        results[add_info] = value
    return results

def get_field_values_fast(
    collection,
    field_path,
    query=None,
    ):
    query = query or {}

    mongo_query = {
        field_path: {"$exists": True},
        **query
    }

    pipeline = [
        {"$match": mongo_query},
        {"$project": {"_id": 0, "value": f"${field_path}"}}
    ]

    results = []

    for doc in collection.aggregate(pipeline):
        value = doc.get("value")

        if value is None:
            continue
        results.append(value)

    return results
def count_documents(collection : Collection, query=None) -> int:
    query = query or {}
    result = collection.count_documents(query)
    print(f"Count ({query or 'all'}): {result}")
    return result

def find_by_field_value(collection : Collection, filter_path : str, filter_value) -> list:
    """
    Query a MongoDB collection using dot-notation path filtering.
    
    Args:
        collection: PyMongo collection object
        filter_path (str): Dot-notation field path, e.g. "command.entry.content"
        filter_value: The value to match against
    
    Returns:
        list: All matching documents
    """
    query = {filter_path: filter_value}
    results = list(collection.find(query))
    return results


def get_fields_where(collection : Collection, filters : dict, projection=None) -> list:
    """
    Query documents using multiple field/value filters.
    You can add projection to specify which fields to return
    or leave it out to get the full documents.

    Args:
        collection: PyMongo collection object.
        filters (dict): Mapping of dot-notation field paths to required values.
            Example:
                {
                    "result.scripts.SearchPasskeys.data.login_page": True,
                    "command.entry.content": "https://ah.nl"
                }
        projection (dict | None): Optional Mongo projection, e.g. {"_id": 0}. 
                                    value of None returns full documents, otherwise specify which fields to include/exclude

    Returns:
        list: All matching documents.
    """
    if not isinstance(filters, dict):
        raise TypeError("filters must be a dict of {field_path: value}")
    if not filters:
        raise ValueError("filters cannot be empty")

    query = {key: value for key, value in filters.items()}

    if projection is None:
        return list(collection.find(query))
    return list(collection.find(query, projection))

def count_bool_values(collection : Collection, field_path : str):
    """Count how many documents have True, False, or missing for a boolean field."""
    return {
        "true"   : collection.count_documents({field_path: True}),
        "false"  : collection.count_documents({field_path: False}),
        "missing": collection.count_documents({field_path: {"$exists": False}}),
        "total"  : collection.count_documents({}),
    }


def count_by_field_value(collection : Collection, field_path : str, field_value, extra_filters=None) -> int:
    """Count docs matching one field/value plus optional extra filters. For example a other value must be on true"""
    query = {field_path: field_value}

    if extra_filters:
        if not isinstance(extra_filters, dict):
            raise TypeError("extra_filters must be a dict of {field_path: value}")
        query.update(extra_filters)

    return collection.count_documents(query)

def different_values_for_field(collection : Collection, field_path : str) -> list:
    """Get all different values for a field path, e.g. to see all different command.origin values."""
    return collection.distinct(field_path)