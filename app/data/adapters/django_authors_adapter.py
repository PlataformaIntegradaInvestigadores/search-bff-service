import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.cache import (
    authors_relevant_cache,
    authors_search_cache,
    author_detail_cache,
    make_key,
)
from app.core.http_client import http_client
from app.domain.author_repositories import IAuthorRepository

logger = logging.getLogger(__name__)


class DjangoAuthorsAdapter(IAuthorRepository):
    """Bridge temporal al endpoint v1 de authors en Django (ADR-05)."""

    async def most_relevant_authors(
        self,
        query: str,
        authors_number: int,
        affiliations: Optional[List[str]] = None,
        mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        aff_key = str(sorted(affiliations)) if affiliations else "none"
        mode_key = mode or "none"
        cache_key = make_key("authors_relevant", query, authors_number, aff_key, mode_key)

        cached = authors_relevant_cache.get(cache_key)
        if cached is not None:
            logger.info(f"[CACHE HIT] authors_relevant | key={cache_key}")
            return cached

        logger.info(f"[CACHE MISS] authors_relevant | key={cache_key}")

        payload: Dict[str, Any] = {
            "topic": query,
            "authors_number": authors_number,
        }

        if affiliations:
            payload["affiliations"] = affiliations
            if mode:
                payload["type"] = mode

        response = await http_client.post(settings.V1_AUTHORS_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        authors_relevant_cache[cache_key] = data
        return data

    async def find_authors_by_query(
        self,
        query: str,
        page: int,
        page_size: int,
    ) -> Dict[str, Any]:
        cache_key = make_key("authors_search", query, page, page_size)

        cached = authors_search_cache.get(cache_key)
        if cached is not None:
            logger.info(f"[CACHE HIT] authors_search | key={cache_key}")
            return cached

        logger.info(f"[CACHE MISS] authors_search | key={cache_key}")

        params = {
            "query": query,
            "page": page,
            "page_size": page_size,
        }

        response = await http_client.get(settings.V1_AUTHORS_FIND_URL, params=params)
        response.raise_for_status()
        data = response.json()

        authors_search_cache[cache_key] = data
        return data

    async def get_author_by_id(self, scopus_id: str) -> Dict[str, Any]:
        cache_key = make_key("author_detail", scopus_id)

        cached = author_detail_cache.get(cache_key)
        if cached is not None:
            logger.info(f"[CACHE HIT] author_detail | key={cache_key}")
            return cached

        logger.info(f"[CACHE MISS] author_detail | key={cache_key}")

        base_url = settings.V1_AUTHORS_DETAIL_URL.rstrip("/")
        url = f"{base_url}/{scopus_id}/"

        response = await http_client.get(url)
        response.raise_for_status()
        data = response.json()

        author_detail_cache[cache_key] = data
        return data
