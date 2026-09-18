"""Unitarias del router /api-se/v2/authors (endpoints de app/api/v2/authors.py)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _http_status_error(body):
    resp = MagicMock()
    resp.json.return_value = body
    resp.text = str(body)
    return httpx.HTTPStatusError("500", request=MagicMock(), response=resp)


class TestRelevantAuthors:
    def test_query_vacio_retorna_400(self):
        r = client.post("/api-se/v2/authors/relevant", json={"query": ""})
        assert r.status_code == 400

    def test_query_sin_sentido_retorna_422(self):
        r = client.post("/api-se/v2/authors/relevant", json={"query": "###"})
        assert r.status_code == 422

    def test_query_valida_retorna_200(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = ([], [], [], 0)
        with patch("app.api.v2.authors.get_use_case", return_value=mock_use_case):
            r = client.post(
                "/api-se/v2/authors/relevant", json={"query": "machine learning"}
            )
        assert r.status_code == 200
        assert r.json()["total_results"] == 0

    def test_bridge_caido_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = httpx.ConnectError("down")
        with patch("app.api.v2.authors.get_use_case", return_value=mock_use_case):
            r = client.post(
                "/api-se/v2/authors/relevant", json={"query": "machine learning"}
            )
        assert r.status_code == 503

    def test_legacy_http_status_error_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = _http_status_error({"error": "boom"})
        with patch("app.api.v2.authors.get_use_case", return_value=mock_use_case):
            r = client.post(
                "/api-se/v2/authors/relevant", json={"query": "machine learning"}
            )
        assert r.status_code == 503

    def test_error_inesperado_retorna_500(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("boom")
        with patch("app.api.v2.authors.get_use_case", return_value=mock_use_case):
            r = client.post(
                "/api-se/v2/authors/relevant", json={"query": "machine learning"}
            )
        assert r.status_code == 500


class TestSearchAuthorsPost:
    def test_query_vacio_retorna_400(self):
        r = client.post("/api-se/v2/authors/search", json={"query": ""})
        assert r.status_code == 400

    def test_query_sin_sentido_retorna_422(self):
        r = client.post("/api-se/v2/authors/search", json={"query": "###"})
        assert r.status_code == 422

    def test_query_valida_retorna_200_con_next_page(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = {
            "data": [
                {
                    "scopus_id": 1,
                    "name": "Perez J.",
                    "affiliations": 1,
                    "articles": 5,
                    "topics": 2,
                    "citation_count": 10,
                    "updated": True,
                }
            ],
            "total": 1,
            "next_page": True,
        }
        with patch(
            "app.api.v2.authors.get_search_use_case", return_value=mock_use_case
        ):
            r = client.post(
                "/api-se/v2/authors/search",
                json={"query": "machine learning", "page": 1, "page_size": 10},
            )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["next_page"] is not None

    def test_bridge_caido_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = httpx.ConnectError("down")
        with patch(
            "app.api.v2.authors.get_search_use_case", return_value=mock_use_case
        ):
            r = client.post(
                "/api-se/v2/authors/search", json={"query": "machine learning"}
            )
        assert r.status_code == 503

    def test_legacy_http_status_error_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = _http_status_error({"error": "boom"})
        with patch(
            "app.api.v2.authors.get_search_use_case", return_value=mock_use_case
        ):
            r = client.post(
                "/api-se/v2/authors/search", json={"query": "machine learning"}
            )
        assert r.status_code == 503

    def test_error_inesperado_retorna_500(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("boom")
        with patch(
            "app.api.v2.authors.get_search_use_case", return_value=mock_use_case
        ):
            r = client.post(
                "/api-se/v2/authors/search", json={"query": "machine learning"}
            )
        assert r.status_code == 500


class TestSearchAuthorsGet:
    def test_query_vacio_retorna_400(self):
        r = client.get("/api-se/v2/authors/search", params={"query": ""})
        assert r.status_code == 400

    def test_query_valida_retorna_200_con_previous_page(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = {
            "data": [],
            "total": 0,
            "previous_page": True,
        }
        with patch(
            "app.api.v2.authors.get_search_use_case", return_value=mock_use_case
        ):
            r = client.get(
                "/api-se/v2/authors/search",
                params={"query": "ml", "page": 2, "page_size": 10},
            )
        assert r.status_code == 200
        assert r.json()["previous_page"] is not None

    def test_bridge_caido_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = httpx.ConnectError("down")
        with patch(
            "app.api.v2.authors.get_search_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/authors/search", params={"query": "ml"})
        assert r.status_code == 503

    def test_legacy_http_status_error_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = _http_status_error({"error": "boom"})
        with patch(
            "app.api.v2.authors.get_search_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/authors/search", params={"query": "ml"})
        assert r.status_code == 503

    def test_error_inesperado_retorna_500(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("boom")
        with patch(
            "app.api.v2.authors.get_search_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/authors/search", params={"query": "ml"})
        assert r.status_code == 500


class TestAuthorProfile:
    def test_scopus_id_vacio_retorna_400(self):
        r = client.get("/api-se/v2/authors/%20/profile")
        assert r.status_code == 400

    def test_scopus_id_valido_retorna_200(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = {
            "author": {
                "scopus_id": "1",
                "first_name": "Juan",
                "last_name": "Perez",
                "auth_name": "Perez J.",
                "initials": "J.",
            },
            "topics": [],
            "coauthors": None,
            "years": [],
            "articles": [],
            "degraded": [],
        }
        with patch(
            "app.api.v2.authors.get_profile_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/authors/1/profile")
        assert r.status_code == 200
        assert r.json()["author"]["scopus_id"] == "1"

    def test_bridge_caido_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = httpx.ConnectError("down")
        with patch(
            "app.api.v2.authors.get_profile_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/authors/1/profile")
        assert r.status_code == 503

    def test_legacy_http_status_error_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = _http_status_error({"error": "boom"})
        with patch(
            "app.api.v2.authors.get_profile_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/authors/1/profile")
        assert r.status_code == 503

    def test_error_inesperado_retorna_500(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("boom")
        with patch(
            "app.api.v2.authors.get_profile_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/authors/1/profile")
        assert r.status_code == 500


class TestGetAuthor:
    def test_scopus_id_vacio_retorna_400(self):
        r = client.get("/api-se/v2/authors/%20")
        assert r.status_code == 400

    def test_scopus_id_valido_retorna_200(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = {
            "scopus_id": 1,
            "first_name": "Juan",
            "last_name": "Perez",
            "auth_name": "Perez J.",
            "initials": "J.",
        }
        with patch(
            "app.api.v2.authors.get_detail_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/authors/1")
        assert r.status_code == 200
        assert r.json()["scopus_id"] == "1"

    def test_bridge_caido_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = httpx.ConnectError("down")
        with patch(
            "app.api.v2.authors.get_detail_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/authors/1")
        assert r.status_code == 503

    def test_legacy_http_status_error_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = _http_status_error({"error": "boom"})
        with patch(
            "app.api.v2.authors.get_detail_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/authors/1")
        assert r.status_code == 503

    def test_error_inesperado_retorna_500(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("boom")
        with patch(
            "app.api.v2.authors.get_detail_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/authors/1")
        assert r.status_code == 500


class TestBuildPageUrl:
    def test_construye_url_absoluta_con_query_params(self):
        from app.api.v2.authors import build_page_url

        mock_request = MagicMock()
        mock_request.base_url = "http://testserver/"
        url = build_page_url(mock_request, "machine learning", 2, 10)
        assert url.startswith("http://testserver/api-se/v2/authors/search?")
        assert "page=2" in url
        assert "page_size=10" in url
