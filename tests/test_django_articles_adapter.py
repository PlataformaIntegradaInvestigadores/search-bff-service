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
        mock_post = AsyncMock(
            return_value=_fake_response(
                {
                    "data": [
                        {
                            "title": "T",
                            "author_count": 1,
                            "affiliation_count": 1,
                            "publication_date": "2024-01-01",
                            "scopus_id": "1",
                            "relevance": 0.9,
                        }
                    ],
                    "total": 1,
                }
            )
        )
        with patch(
            "app.data.adapters.django_articles_adapter.resilient_post", new=mock_post
        ):
            asyncio.run(adapter.most_relevant_articles("ml", 1, 10))
            asyncio.run(adapter.most_relevant_articles("ml", 1, 10))
        assert mock_post.await_count == 1

    def test_incluye_years_en_el_payload_cuando_se_filtra(self):
        adapter = DjangoArticlesAdapter()
        mock_post = AsyncMock(
            return_value=_fake_response(
                {
                    "data": [
                        {
                            "title": "T",
                            "author_count": 1,
                            "affiliation_count": 1,
                            "publication_date": "2023-01-01",
                            "scopus_id": "1",
                            "relevance": 0.5,
                        }
                    ],
                    "total": 1,
                }
            )
        )
        with patch(
            "app.data.adapters.django_articles_adapter.resilient_post", new=mock_post
        ):
            asyncio.run(adapter.most_relevant_articles("ml", 1, 10, years=[2023]))
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["type"] == "include"
        assert kwargs["json"]["years"] == ["2023"]

    def test_fallback_a_semantic_cuando_tfidf_vacio(self):
        adapter = DjangoArticlesAdapter()

        async def _side_effect(url, *args, **kwargs):
            if "most-relevant" in str(url):
                return _fake_response({"data": [], "total": 0})
            return _fake_response(
                {
                    "data": [
                        {
                            "title": "Hybrid Search",
                            "abstract": "math IR abstract",
                            "author_count": 2,
                            "affiliation_count": 1,
                            "publication_date": "2023-02-14",
                            "scopus_id": "MOCK-ART-7",
                            "relevance": 0.8,
                            "authors": ["Ana"],
                            "affiliations": ["Uni"],
                        }
                    ],
                    "years": ["2023"],
                    "total": 1,
                }
            )

        mock_post = AsyncMock(side_effect=_side_effect)
        with patch(
            "app.data.adapters.django_articles_adapter.resilient_post", new=mock_post
        ):
            result = asyncio.run(adapter.most_relevant_articles("Hybrid Search", 1, 10))

        assert mock_post.await_count == 2
        assert result["total"] == 1
        assert result["data"][0]["scopus_id"] == "MOCK-ART-7"
        assert result["data"][0]["abstract"] == "math IR abstract"


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
