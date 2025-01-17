import pytest
from azure.functions import HttpRequest, HttpResponse
from pydantic import BaseModel
from typing import Optional
import json
from azure.functions_parser import validate_request


def create_http_request(
    method: str = "POST",
    url: str = "http://example.com/api",
    headers: dict | None = None,
    params: dict | None = None,
    body: dict | None = None,
) -> HttpRequest:
    body_bytes = json.dumps(body).encode() if body is not None else b""
    return HttpRequest(
        method=method,
        url=url,
        headers=headers or {},
        params=params or {},
        body=body_bytes,
    )


class UserBody(BaseModel):
    name: str
    age: int
    email: Optional[str] = None


def test_simple_handler_no_params():
    """Test a simple handler with no parameters beyond the request"""

    @validate_request
    def handler(req: HttpRequest):
        return {"status": "ok"}

    request = create_http_request()
    response = handler(request)

    assert isinstance(response, HttpResponse)
    assert response.status_code == 200
    assert json.loads(response.get_body()) == {"status": "ok"}


def test_query_params_validation():
    """Test query parameter validation"""

    @validate_request
    def handler(req: HttpRequest, name: str, age: int = 18):
        return {"name": name, "age": age}

    # Test valid params
    request = create_http_request(method="GET", params={"name": "Alice", "age": "25"})
    response = handler(request)

    assert response.status_code == 200
    assert json.loads(response.get_body()) == {"name": "Alice", "age": 25}

    # Test missing required param
    request = create_http_request(method="GET", params={"age": "25"})
    response = handler(request)

    assert response.status_code == 400
    error_data = json.loads(response.get_body())
    assert "errors" in error_data


def test_body_validation():
    """Test request body validation"""

    @validate_request
    def handler(req: HttpRequest, user: UserBody):
        return {"user": user.model_dump()}

    # Test valid body
    valid_body = {"name": "Alice", "age": 25, "email": "alice@example.com"}
    request = create_http_request(body=valid_body)
    response = handler(request)

    assert response.status_code == 200
    assert json.loads(response.get_body())["user"] == valid_body

    # Test invalid body
    invalid_body = {
        "name": "Alice",
        "email": "not-an-email",  # Missing required 'age' field
    }
    request = create_http_request(body=invalid_body)
    response = handler(request)

    assert response.status_code == 400
    error_data = json.loads(response.get_body())
    assert "errors" in error_data


def test_combined_body_and_query():
    """Test handler with both body and query parameters"""

    @validate_request
    def handler(req: HttpRequest, user: UserBody, format: str = "json"):
        return {"user": user.model_dump(), "format": format}

    valid_body = {"name": "Alice", "age": 25, "email": "alice@example.com"}
    request = create_http_request(body=valid_body, params={"format": "xml"})
    response = handler(request)

    assert response.status_code == 200
    response_data = json.loads(response.get_body())
    assert response_data["user"] == valid_body
    assert response_data["format"] == "xml"


def test_different_return_types():
    """Test handling of different return types"""

    @validate_request
    def handler_str(req: HttpRequest):
        return "Hello, World!"

    @validate_request
    def handler_bytes(req: HttpRequest):
        return b"Hello, World!"

    @validate_request
    def handler_none(req: HttpRequest):
        return None

    @validate_request
    def handler_model(req: HttpRequest):
        return UserBody(name="Alice", age=25)

    request = create_http_request()

    # Test string return
    response = handler_str(request)
    assert response.status_code == 200
    assert response.get_body() == b"Hello, World!"

    # Test bytes return
    response = handler_bytes(request)
    assert response.status_code == 200
    assert response.get_body() == b"Hello, World!"

    # Test None return
    response = handler_none(request)
    assert response.status_code == 200
    assert response.get_body() == b"Operation successful"

    # Test Pydantic model return
    response = handler_model(request)
    assert response.status_code == 200
    assert json.loads(response.get_body()) == {
        "name": "Alice",
        "age": 25,
        "email": None,
    }
