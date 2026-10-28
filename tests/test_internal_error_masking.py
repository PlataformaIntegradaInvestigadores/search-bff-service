from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)

SECRET = "db-internal:5432 secret-token"

# (método, ruta, cuerpo/params, función que construye el caso de uso)
ROUTES = [
    ("post", "/api-se/v2/search", {"json": {"query": "ml"}}, "search.get_use_case"),
    (
        "post",
        "/api-se/v2/authors/relevant",
        {"json": {"query": "ml"}},
        "authors.get_use_case",
    ),
    (
        "post",
        "/api-se/v2/authors/search",
        {"json": {"query": "ml"}},
        "authors.get_search_use_case",
    ),
    (
        "get",
        "/api-se/v2/authors/search",
        {"params": {"query": "ml"}},
        "authors.get_search_use_case",
    ),
    ("get", "/api-se/v2/authors/123/profile", {}, "authors.get_profile_use_case"),
    ("get", "/api-se/v2/authors/123", {}, "authors.get_detail_use_case"),
    (
        "post",
        "/api-se/v2/articles/relevant",
        {"json": {"query": "ml"}},
        "articles.get_relevant_use_case",
    ),
    (
        "get",
        "/api-se/v2/articles/by-author",
        {"params": {"author_id": "123"}},
        "articles.get_by_author_use_case",
    ),
    ("get", "/api-se/v2/articles/123", {}, "articles.get_detail_use_case"),
]


@pytest.mark.parametrize("method,path,kwargs,factory", ROUTES)
def test_unexpected_error_does_not_leak_the_exception_message(
    method, path, kwargs, factory
):
    use_case = AsyncMock()
    use_case.execute.side_effect = RuntimeError(SECRET)
    with patch(f"app.api.v2.{factory}", return_value=use_case):
        response = getattr(client, method)(path, **kwargs)

    assert response.status_code == 500, path
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["message"] == "Error interno inesperado."
    assert SECRET not in response.text
    assert body["trace_id"]
