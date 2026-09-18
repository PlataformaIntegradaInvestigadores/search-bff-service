"""Unitarias de DjangoSearchAdapter (bridge v1 de busqueda semantica, ADR-05)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.data.adapters.django_adapter import DjangoSearchAdapter
from app.domain.entities import SearchQuery


def _fake_response(payload):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    return resp


class TestDjangoSearchAdapter:
    def test_mapea_los_resultados_de_v1_a_search_result(self):
        payload = {
            "data": [
                {
                    "title": "X",
                    "abstract": "Y",
                    "scopus_id": 123,
                    "publication_date": "2023-01-01",
                    "relevance": 0.87,
                }
            ]
        }
        mock_post = AsyncMock(return_value=_fake_response(payload))
        with patch("app.data.adapters.django_adapter.resilient_post", new=mock_post):
            results = asyncio.run(
                DjangoSearchAdapter().search(
                    SearchQuery(query="ml", page=1, page_size=10)
                )
            )
        assert len(results) == 1
        assert results[0].scopus_id == "123"  # coercion a str
        assert results[0].relevance == 0.87

    def test_envia_top_k_como_page_size_por_tres(self):
        mock_post = AsyncMock(return_value=_fake_response({"data": []}))
        with patch("app.data.adapters.django_adapter.resilient_post", new=mock_post):
            asyncio.run(
                DjangoSearchAdapter().search(
                    SearchQuery(query="ml", page=1, page_size=5)
                )
            )
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["top_k"] == 15

    def test_propaga_http_status_error_de_v1(self):
        resp = MagicMock()
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock(status_code=500)
        )
        mock_post = AsyncMock(return_value=resp)
        with patch("app.data.adapters.django_adapter.resilient_post", new=mock_post):
            with pytest.raises(httpx.HTTPStatusError):
                asyncio.run(
                    DjangoSearchAdapter().search(
                        SearchQuery(query="ml", page=1, page_size=10)
                    )
                )
