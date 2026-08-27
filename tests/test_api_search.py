"""Unitarias del router /api-se/v2/search (endpoints de app/api/v2/search.py)."""

from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.core.cache import filters_cache
from app.domain.entities import SearchResult
from app.main import app

client = TestClient(app)


class TestSemanticSearch:
    def test_query_vacio_retorna_400(self):
        r = client.post("/api-se/v2/search", json={"query": ""})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "INVALID_INPUT"

    def test_query_sin_sentido_retorna_422(self):
        r = client.post("/api-se/v2/search", json={"query": "###"})
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "CONTRACT_VALIDATION"

    def test_query_valida_retorna_200_con_resultados(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = (
            [
                SearchResult(
                    title="X",
                    abstract="Y",
                    scopus_id="1",
                    publication_date="2023-05-01",
                    relevance=0.9,
                )
            ],
            12.3,
            1,
        )
        with patch("app.api.v2.search.get_use_case", return_value=mock_use_case):
            r = client.post("/api-se/v2/search", json={"query": "machine learning"})
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["years"] == ["2023"]

    def test_bridge_caido_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = httpx.ConnectError("down")
        with patch("app.api.v2.search.get_use_case", return_value=mock_use_case):
            r = client.post("/api-se/v2/search", json={"query": "machine learning"})
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"

    def test_error_inesperado_retorna_500(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("boom")
        with patch("app.api.v2.search.get_use_case", return_value=mock_use_case):
            r = client.post("/api-se/v2/search", json={"query": "machine learning"})
        assert r.status_code == 500
        assert r.json()["error"]["code"] == "INTERNAL_ERROR"


class TestSearchFilters:
    def setup_method(self):
        filters_cache.clear()

    def teardown_method(self):
        filters_cache.clear()

    def test_cache_hit_no_llama_a_v1(self):
        filters_cache["years"] = [2023, 2024]
        r = client.get("/api-se/v2/search/filters")
        assert r.status_code == 200
        assert r.json() == {"years": [2023, 2024]}

    def test_cache_miss_calcula_anios_desde_v1(self):
        payload = [
            {"year": 2022, "article": 5},
            {"year": 2023, "article": 0},  # sin articulos -> excluido
        ]
        mock_resp = AsyncMock()
        mock_resp.raise_for_status = lambda: None
        mock_resp.json = lambda: payload
        mock_get = AsyncMock(return_value=mock_resp)
        with patch("app.api.v2.search.resilient_get", new=mock_get):
            r = client.get("/api-se/v2/search/filters")
        assert r.status_code == 200
        assert r.json() == {"years": [2022]}

    def test_cache_miss_y_v1_falla_usa_fallback_estatico(self):
        mock_get = AsyncMock(side_effect=httpx.ConnectError("down"))
        with patch("app.api.v2.search.resilient_get", new=mock_get):
            r = client.get("/api-se/v2/search/filters")
        assert r.status_code == 200
        assert r.json()["years"] == list(range(2019, 2027))


class TestHealth:
    def test_v1_responde_sano(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200

        class _FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def get(self, *a, **kw):
                return mock_resp

        with patch("app.api.v2.search.httpx.AsyncClient", return_value=_FakeClient()):
            r = client.get("/api-se/v2/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_v1_no_responde_retorna_503(self):
        class _FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def get(self, *a, **kw):
                raise httpx.ConnectError("down")

        with patch("app.api.v2.search.httpx.AsyncClient", return_value=_FakeClient()):
            r = client.get("/api-se/v2/health")
        assert r.status_code == 503


class TestCacheStats:
    def test_devuelve_las_seis_caches(self):
        r = client.get("/api-se/v2/cache/stats")
        assert r.status_code == 200
        body = r.json()
        assert set(body.keys()) == {
            "articles",
            "authors_search",
            "authors_relevant",
            "article_detail",
            "articles_by_author",
            "author_detail",
        }
