# azure-functions-parser

![PyPI](https://img.shields.io/pypi/v/azure-functions-parser)
![Tests](https://github.com/ryayoung/azure-functions-parser/actions/workflows/tests.yml/badge.svg)
![License](https://img.shields.io/github/license/ryayoung/azure-functions-parser)


A lightweight decorator that adds FastAPI-like request parsing and validation to Azure Functions HTTP triggers.

## Features

- Automatic parsing and validation of query parameters
- Automatic parsing and validation of JSON request bodies using Pydantic models
- Automatic response serialization for different return types (dict, Pydantic models, strings, etc.)
- Zero configuration required - just add the decorator
- Full type hints and async support

## Installation

```bash
pip install azure-functions-parser
```

## Usage

```python
import azure.functions as func
from azure.functions_parser import validate_request

@validate_request
def main(req: func.HttpRequest, some_query_param: int = 1):
    ...
```


## Quick Start

You have an API endpoint that takes user data in the request body, and an
optional query parameter.

**Before**

```python
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    try:
        name = body["name"]
        age = int(body["age"])
        format = req.params.get("format", "json")

        if format not in ["json", "csv"]:
            raise ValueError(f"Invalid argument for 'format': {format}")
    except Exception as e:
        return func.HttpResponse(str(e), status_code=400)

    return func.HttpResponse(
        json.dumps({"name": name, "age": age, "format": format}),
        status_code=200
    )
```

**After**

```python
from typing import Literal
from pydantic import BaseModel
import azure.functions as func
from azure.functions_parser import validate_request

class User(BaseModel):
    name: str
    age: int

@validate_request
def main(req: func.HttpRequest, user: User, format: Literal["json", "csv"] = "json"):
    return {"name": user.name, "age": user.age, "format": format}
```

The request body, `User`, and query parameter, `format`, will be parsed and
validated for incoming requests. If there's a validation error, a `400` response
will be issued automatically, with descriptive errors.

Suppose you get an incoming request with the following data:
- body: `{"age": 25.5}` ('name' is missing, and 'age' is a float)
- params: `?format=xml` (should be 'json' or 'csv')

The following error will be sent back to the client with a 400 code.

```json
{
  "errors": [
    {
      "param": "format",
      "reason": "Input should be 'json' or 'csv'",
      "type": "literal_error",
      "input": "xml"
    },
    {
      "param": "name",
      "reason": "Field required",
      "type": "missing"
    },
    {
      "param": "age",
      "reason": "Input should be a valid integer, got a number with a fractional part",
      "type": "int_from_float",
      "input": 25.5
    }
  ]
}
```

## Usage Guide

### Query Parameters

Query parameters are automatically parsed based on your function's parameters:

```python
@validate_request
def handler(req, name: str, age: int = 18, format: str = "json"):
    return {"name": name, "age": age, "format": format}
```

This will:
- Require `name` as a required query parameter
- Accept an optional `age` parameter that defaults to 18
- Accept an optional `format` parameter that defaults to "json"
- Automatically convert parameters to the correct type
- Return a 400 error with validation details if parameters are invalid or missing

### Request Body

Use a Pydantic model to parse and validate the JSON request body. Your function may
have at most one, and only one, parameter annotated as a Pydantic model.

```python
from pydantic import BaseModel, EmailStr

class UserProfile(BaseModel):
    name: str
    age: int
    email: EmailStr
    interests: list[str] | None = None

@validate_request
def create_user(req: func.HttpRequest, user: UserProfile):
    return {"name": user.name, "age": user.age}
```

### Response Handling

The decorator automatically handles different return types.

Any return value that is *not* a `func.HttpResponse` will be wrapped in a `200` OK
response, with your return value as the response body.

```python
@validate_request
def handler1(req: func.HttpRequest):
    return {"message": "OK"}  # Returns JSON response

@validate_request
def handler2(req: func.HttpRequest):
    return "Hello, World!"  # Returns plain text response

@validate_request
def handler3(req: func.HttpRequest):
    return UserProfile(...)  # Returns JSON-serialized Pydantic model

@validate_request
def handler4(req: func.HttpRequest):
    return func.HttpResponse(...)  # Returns custom HttpResponse directly
```

### Error Handling

Invalid requests return detailed 400 responses:

```json
{
  "errors": [
    {
      "param": "format",
      "reason": "Input should be 'json' or 'csv'",
      "type": "literal_error",
      "input": "xml"
    },
    {
      "param": "name",
      "reason": "Field required",
      "type": "missing"
    },
    {
      "param": "age",
      "reason": "Input should be a valid integer, got a number with a fractional part",
      "type": "int_from_float",
      "input": 25.5
    }
  ]
}
```

### Async Support

The decorator works with both sync and async handlers:

```python
@validate_request
async def handler(req: func.HttpRequest, user: UserProfile):
    # ... async operations ...
    return {"status": "success"}
```

## Contributing

Contributions are welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
