"""Unitarias del router /api-se/v2/articles (endpoints de app/api/v2/articles.py)."""

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


class TestRelevantArticles:
    def test_query_vacio_retorna_400(self):
        r = client.post("/api-se/v2/articles/relevant", json={"query": ""})
        assert r.status_code == 400

    def test_query_sin_sentido_retorna_422(self):
        r = client.post("/api-se/v2/articles/relevant", json={"query": "###"})
        assert r.status_code == 422

    def test_query_valida_retorna_200(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = {
            "data": [
                {
                    "title": "X",
                    "author_count": 2,
                    "affiliation_count": 1,
                    "publication_date": "2023-01-01",
                    "scopus_id": 1,
                    "relevance": 0.5,
                }
            ],
            "years": [2023],
            "total": 1,
        }
        with patch(
            "app.api.v2.articles.get_relevant_use_case", return_value=mock_use_case
        ):
            r = client.post(
                "/api-se/v2/articles/relevant", json={"query": "machine learning"}
            )
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_bridge_caido_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = httpx.ConnectError("down")
        with patch(
            "app.api.v2.articles.get_relevant_use_case", return_value=mock_use_case
        ):
            r = client.post(
                "/api-se/v2/articles/relevant", json={"query": "machine learning"}
            )
        assert r.status_code == 503

    def test_legacy_http_status_error_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = _http_status_error({"error": "boom"})
        with patch(
            "app.api.v2.articles.get_relevant_use_case", return_value=mock_use_case
        ):
            r = client.post(
                "/api-se/v2/articles/relevant", json={"query": "machine learning"}
            )
        assert r.status_code == 503
        assert "boom" in r.json()["error"]["message"]

    def test_error_inesperado_retorna_500(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("boom")
        with patch(
            "app.api.v2.articles.get_relevant_use_case", return_value=mock_use_case
        ):
            r = client.post(
                "/api-se/v2/articles/relevant", json={"query": "machine learning"}
            )
        assert r.status_code == 500


class TestArticlesByAuthor:
    def test_author_id_vacio_retorna_400(self):
        r = client.get("/api-se/v2/articles/by-author", params={"author_id": ""})
        assert r.status_code == 400

    def test_author_id_valido_retorna_200(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = [
            {"title": "X", "publication_date": "2023-01-01", "scopus_id": "1"}
        ]
        with patch(
            "app.api.v2.articles.get_by_author_use_case", return_value=mock_use_case
        ):
            r = client.get(
                "/api-se/v2/articles/by-author", params={"author_id": "57193901649"}
            )
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_legacy_http_status_error_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = _http_status_error({"error": "boom"})
        with patch(
            "app.api.v2.articles.get_by_author_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/articles/by-author", params={"author_id": "1"})
        assert r.status_code == 503

    def test_error_inesperado_retorna_500(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("boom")
        with patch(
            "app.api.v2.articles.get_by_author_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/articles/by-author", params={"author_id": "1"})
        assert r.status_code == 500


class TestArticleDetail:
    def test_scopus_id_vacio_retorna_400(self):
        r = client.get("/api-se/v2/articles/%20")  # espacio codificado
        assert r.status_code == 400

    def test_articulo_inexistente_retorna_404(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = {}
        with patch(
            "app.api.v2.articles.get_detail_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/articles/99999")
        assert r.status_code == 404

    def test_articulo_existente_retorna_200_con_autores_normalizados(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = {
            "scopus_id": "1",
            "title": "X",
            "abstract": "Y",
            "doi": "10.1/x",
            "publication_date": "2023-01-01",
            "author_count": 1,
            "affiliation_count": 1,
            "authors": [{"name": "Perez J.", "scopusId": 42}],
            "affiliations": [{"name": "UCE"}],
            "topics": ["ml"],
        }
        with patch(
            "app.api.v2.articles.get_detail_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/articles/1")
        assert r.status_code == 200
        body = r.json()
        assert body["authors"][0]["scopus_id"] == "42"
        assert body["affiliations"] == ["UCE"]

    def test_legacy_http_status_error_retorna_503(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = _http_status_error({"error": "boom"})
        with patch(
            "app.api.v2.articles.get_detail_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/articles/1")
        assert r.status_code == 503

    def test_error_inesperado_retorna_500(self):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("boom")
        with patch(
            "app.api.v2.articles.get_detail_use_case", return_value=mock_use_case
        ):
            r = client.get("/api-se/v2/articles/1")
        assert r.status_code == 500
