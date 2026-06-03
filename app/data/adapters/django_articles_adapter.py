import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.cache import (
    articles_cache,
    articles_by_author_cache,
    article_detail_cache,
    make_key,
)
from app.core.http_client import http_client
from app.domain.article_repositories import IArticleRepository

logger = logging.getLogger(__name__)


class DjangoArticlesAdapter(IArticleRepository):
    """Bridge temporal al endpoint v1 de articles en Django (ADR-05)."""

    async def most_relevant_articles(
        self,
        query: str,
        page: int,
        page_size: int,
        years: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        years_key = str(sorted(years)) if years else "none"
        cache_key = make_key("articles_relevant", query, page, page_size, years_key)

        cached = articles_cache.get(cache_key)
        if cached is not None:
            logger.info(f"[CACHE HIT] articles_relevant | key={cache_key}")
            return cached

        logger.info(f"[CACHE MISS] articles_relevant | key={cache_key}")

        payload: Dict[str, Any] = {
            "query": query,
            "page": page,
            "size": page_size,
        }

        if years:
            payload["years"] = [str(year) for year in years]

        response = await http_client.post(settings.V1_ARTICLES_RELEVANT_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        articles_cache[cache_key] = data
        return data

    async def find_articles_by_author(self, author_id: str) -> List[Dict[str, Any]]:
        cache_key = make_key("articles_by_author", author_id)

        cached = articles_by_author_cache.get(cache_key)
        if cached is not None:
            logger.info(f"[CACHE HIT] articles_by_author | key={cache_key}")
            return cached

        logger.info(f"[CACHE MISS] articles_by_author | key={cache_key}")

        params = {"author_id": author_id}

        response = await http_client.get(settings.V1_ARTICLES_BY_AUTHOR_URL, params=params)
        response.raise_for_status()
        data = response.json()

        articles_by_author_cache[cache_key] = data
        return data

    async def get_article_by_id(self, scopus_id: str) -> Dict[str, Any]:
        cache_key = make_key("article_detail", scopus_id)

        cached = article_detail_cache.get(cache_key)
        if cached is not None:
            logger.info(f"[CACHE HIT] article_detail | key={cache_key}")
            return cached

        logger.info(f"[CACHE MISS] article_detail | key={cache_key}")

        url = f"{settings.V1_ARTICLES_DETAIL_URL}{scopus_id}/"

        response = await http_client.get(url)
        response.raise_for_status()
        data = response.json()

        article_detail_cache[cache_key] = data
        return data
