import re



def get_field(collection, field_path, query=None):
    """
    Return the value at a nested field path for every document.

    Example:
        x = get_field(col, "command.entry.content")
        print_table(x, "command.entry.content")
    """
    query = query or {}

    cursor = collection.find(
        {field_path: {"$exists": True}},
        {field_path: 1, "_id": 0}
    )

    results = []

    for doc in cursor:
        # Walk the dot-separated path into the nested dict
        value = doc
        for key in field_path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break

        if value is not None:
            results.append({field_path: value})

    return results

def count_documents(collection, query=None):
    query = query or {}
    result = collection.count_documents(query)
    print(f"Count ({query or 'all'}): {result}")
    return result

def get_field(collection, filter_path, filter_value):
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
