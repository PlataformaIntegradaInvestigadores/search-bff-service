"""Unitarias de los 3 metodos de DjangoAuthorsAdapter no cubiertos por
test_authors_cache.py: most_relevant_authors, find_authors_by_query,
get_author_by_id (cache hit/miss + payload enviado a v1)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.cache import (
    author_detail_cache,
    authors_relevant_cache,
    authors_search_cache,
)
from app.data.adapters.django_authors_adapter import DjangoAuthorsAdapter


def _fake_response(payload):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    return resp


@pytest.fixture(autouse=True)
def _clear_caches():
    for c in (authors_relevant_cache, authors_search_cache, author_detail_cache):
        c.clear()
    yield
    for c in (authors_relevant_cache, authors_search_cache, author_detail_cache):
        c.clear()


class TestMostRelevantAuthors:
    def test_segunda_llamada_con_mismos_params_es_cache_hit(self):
        adapter = DjangoAuthorsAdapter()
        mock_post = AsyncMock(return_value=_fake_response({"nodes": []}))
        with patch(
            "app.data.adapters.django_authors_adapter.resilient_post", new=mock_post
        ):
            asyncio.run(adapter.most_relevant_authors("ml", 10))
            asyncio.run(adapter.most_relevant_authors("ml", 10))
        assert mock_post.await_count == 1

    def test_incluye_type_solo_si_hay_afiliaciones_y_modo(self):
        adapter = DjangoAuthorsAdapter()
        mock_post = AsyncMock(return_value=_fake_response({"nodes": []}))
        with patch(
            "app.data.adapters.django_authors_adapter.resilient_post", new=mock_post
        ):
            asyncio.run(
                adapter.most_relevant_authors(
                    "ml", 10, affiliations=["UCE"], mode="include"
                )
            )
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["affiliations"] == ["UCE"]
        assert kwargs["json"]["type"] == "include"


class TestFindAuthorsByQuery:
    def test_segunda_llamada_con_misma_pagina_es_cache_hit(self):
        adapter = DjangoAuthorsAdapter()
        mock_get = AsyncMock(return_value=_fake_response({"data": []}))
        with patch(
            "app.data.adapters.django_authors_adapter.resilient_get", new=mock_get
        ):
            asyncio.run(adapter.find_authors_by_query("ai", 1, 10))
            asyncio.run(adapter.find_authors_by_query("ai", 1, 10))
        assert mock_get.await_count == 1

    def test_paginas_distintas_no_comparten_cache(self):
        adapter = DjangoAuthorsAdapter()
        mock_get = AsyncMock(return_value=_fake_response({"data": []}))
        with patch(
            "app.data.adapters.django_authors_adapter.resilient_get", new=mock_get
        ):
            asyncio.run(adapter.find_authors_by_query("ai", 1, 10))
            asyncio.run(adapter.find_authors_by_query("ai", 2, 10))
        assert mock_get.await_count == 2


class TestGetAuthorById:
    def test_segunda_llamada_con_mismo_scopus_id_es_cache_hit(self):
        adapter = DjangoAuthorsAdapter()
        mock_get = AsyncMock(return_value=_fake_response({"scopus_id": "1"}))
        with patch(
            "app.data.adapters.django_authors_adapter.resilient_get", new=mock_get
        ):
            asyncio.run(adapter.get_author_by_id("1"))
            asyncio.run(adapter.get_author_by_id("1"))
        assert mock_get.await_count == 1
