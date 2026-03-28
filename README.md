# MongoDB Python Utilities

This project provides Python helper functions to retrieve and process data from a MongoDB database.

## Configuration

Create a `config.py` file in the root of the project with the following variables:

```python
MONGO_URI = "your_mongo_uri"
DATABASE = "your_database_name"
COLLECTION = "your_collection_name"
```

## Files

* `basic_database_function.py`
  Contains generic functions that can be used with any MongoDB database.

* `specific_database_function.py`
  Contains functions tailored to a specific database structure.

## Usage

Import the required functions in your script:

```python
from basic_database_function import your_function
```

or

```python
from specific_database_function import your_function
```

Then call the function with the appropriate parameters.

## Notes

* Make sure your MongoDB instance is running and accessible via `MONGO_URI`.
* The structure of your documents may affect how the functions behave, especially in `specific_database_function.py`.
