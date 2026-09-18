"""Unitarias de DjangoArticlesAdapter: cache hit/miss por metodo (bridge v1, ADR-05)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.cache import (
    article_detail_cache,
    articles_by_author_cache,
    articles_cache,
)
from app.data.adapters.django_articles_adapter import DjangoArticlesAdapter


def _fake_response(payload):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    return resp


@pytest.fixture(autouse=True)
def _clear_caches():
    for c in (articles_cache, articles_by_author_cache, article_detail_cache):
        c.clear()
    yield
    for c in (articles_cache, articles_by_author_cache, article_detail_cache):
        c.clear()


class TestMostRelevantArticles:
    def test_segunda_llamada_con_mismos_params_es_cache_hit(self):
        adapter = DjangoArticlesAdapter()
        mock_post = AsyncMock(return_value=_fake_response({"data": [], "total": 0}))
        with patch(
            "app.data.adapters.django_articles_adapter.resilient_post", new=mock_post
        ):
            asyncio.run(adapter.most_relevant_articles("ml", 1, 10))
            asyncio.run(adapter.most_relevant_articles("ml", 1, 10))
        assert mock_post.await_count == 1

    def test_incluye_years_en_el_payload_cuando_se_filtra(self):
        adapter = DjangoArticlesAdapter()
        mock_post = AsyncMock(return_value=_fake_response({"data": []}))
        with patch(
            "app.data.adapters.django_articles_adapter.resilient_post", new=mock_post
        ):
            asyncio.run(adapter.most_relevant_articles("ml", 1, 10, years=[2023]))
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["type"] == "include"
        assert kwargs["json"]["years"] == ["2023"]


class TestFindArticlesByAuthor:
    def test_segunda_llamada_con_mismo_author_id_es_cache_hit(self):
        adapter = DjangoArticlesAdapter()
        mock_get = AsyncMock(return_value=_fake_response([{"title": "X"}]))
        with patch(
            "app.data.adapters.django_articles_adapter.resilient_get", new=mock_get
        ):
            first = asyncio.run(adapter.find_articles_by_author("57193901649"))
            second = asyncio.run(adapter.find_articles_by_author("57193901649"))
        assert first == second == [{"title": "X"}]
        assert mock_get.await_count == 1


class TestGetArticleById:
    def test_segunda_llamada_con_mismo_scopus_id_es_cache_hit(self):
        adapter = DjangoArticlesAdapter()
        mock_get = AsyncMock(return_value=_fake_response({"scopus_id": "1"}))
        with patch(
            "app.data.adapters.django_articles_adapter.resilient_get", new=mock_get
        ):
            asyncio.run(adapter.get_article_by_id("1"))
            asyncio.run(adapter.get_article_by_id("1"))
        assert mock_get.await_count == 1
