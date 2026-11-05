"""Unitarias del router /api-se/v2/search (endpoints de app/api/v2/search.py)."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
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
            r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["global_status"] == "Online"
        assert body["groups"][0]["services"][0] == {
            "name": "search-engine-api",
            "status": "ok",
        }

    def test_v1_no_responde_retorna_503(self):
        class _FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def get(self, *a, **kw):
                raise httpx.ConnectError("down")

        with patch("app.api.v2.search.httpx.AsyncClient", return_value=_FakeClient()):
            r = client.get("/health")
        assert r.status_code == 503


class _FakeUpstream:
    """Stands in for httpx.AsyncClient and records the URL that was requested."""

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.urls = []

    def __call__(self, *a, **kw):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url, *a, **kw):
        self.urls.append(url)
        if self.error:
            raise self.error
        return self.response


def _response(status, body=None, json_error=False):
    from unittest.mock import MagicMock

    resp = MagicMock()
    resp.status_code = status
    if json_error:
        resp.json.side_effect = ValueError("not json")
    else:
        resp.json.return_value = body or {}
    return resp


class TestHealthUsesUpstreamHealth:
    def _get(self, upstream):
        with patch("app.api.v2.search.httpx.AsyncClient", upstream):
            return client.get("/health")

    def test_pregunta_al_health_de_search_service_y_no_a_semantic_search(self):
        upstream = _FakeUpstream(_response(200))

        self._get(upstream)

        assert len(upstream.urls) == 1
        assert upstream.urls[0].endswith("/health/")
        assert "semantic-search" not in upstream.urls[0]

    def test_upstream_sano(self):
        r = self._get(_FakeUpstream(_response(200)))

        assert r.status_code == 200
        assert r.json()["global_status"] == "Online"
        assert r.json()["groups"][0]["group_status"] == "Operativo"

    def test_upstream_con_una_base_caida_se_reporta_degradado(self):
        body = {"global_status": "Degraded"}

        r = self._get(_FakeUpstream(_response(503, body)))

        assert r.status_code == 503
        payload = r.json()
        assert payload["global_status"] == "Degraded"
        assert payload["groups"][0]["group_status"] == "Degradado"
        assert payload["groups"][0]["services"][0]["status"] == "error"

    def test_upstream_con_las_bases_caidas_se_reporta_caido(self):
        body = {"global_status": "Offline"}

        r = self._get(_FakeUpstream(_response(503, body)))

        assert r.status_code == 503
        assert r.json()["global_status"] == "Offline"
        assert r.json()["groups"][0]["group_status"] == "Caído"

    def test_503_con_cuerpo_ilegible_se_reporta_caido(self):
        r = self._get(_FakeUpstream(_response(503, json_error=True)))

        assert r.status_code == 503
        assert r.json()["global_status"] == "Offline"

    @pytest.mark.parametrize("status", [404, 405, 500, 502])
    def test_otros_codigos_del_upstream_se_reportan_caidos(self, status):
        r = self._get(_FakeUpstream(_response(status)))

        assert r.status_code == 503
        assert r.json()["global_status"] == "Offline"

    @pytest.mark.parametrize(
        "error",
        [
            httpx.ConnectError("down"),
            httpx.ReadTimeout("slow"),
            httpx.RemoteProtocolError("bad"),
        ],
    )
    def test_errores_de_red_se_reportan_caidos(self, error):
        r = self._get(_FakeUpstream(error=error))

        assert r.status_code == 503
        assert r.json()["global_status"] == "Offline"


class TestOpenAPI:
    def test_schema_uses_gateway_prefix(self):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert schema["servers"] == [
            {"url": "/api/search/v2", "description": "Gateway"}
        ]
        assert "/health" not in schema["paths"]
        assert all(not path.startswith("/api-se/v2") for path in schema["paths"])


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
