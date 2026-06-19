import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.cache import (
    authors_relevant_cache,
    authors_search_cache,
    author_detail_cache,
    author_coauthors_cache,
    author_topics_cache,
    author_years_cache,
    make_key,
)
from app.core.resilience import resilient_get, resilient_post
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

        response = await resilient_post(settings.V1_AUTHORS_URL, json=payload)
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

        response = await resilient_get(settings.V1_AUTHORS_FIND_URL, params=params)
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

        response = await resilient_get(url)
        response.raise_for_status()
        data = response.json()

        author_detail_cache[cache_key] = data
        return data

    # --- Fuentes adicionales para la composicion del perfil (Slice 2 / API Composition).
    # Se derivan de BASE_URL; antes el frontend las consumia DIRECTO de v1, violando
    # la regla TO-BE de US5 ("Angular consume solo /api-se/v2/").

    async def get_coauthors(self, scopus_id: str) -> Any:
        cache_key = make_key("author_coauthors", scopus_id)

        cached = author_coauthors_cache.get(cache_key)
        if cached is not None:
            logger.info(f"[CACHE HIT] author_coauthors | key={cache_key}")
            return cached

        logger.info(f"[CACHE MISS] author_coauthors | key={cache_key}")

        url = f"{settings.BASE_URL.rstrip('/')}/api-se/v1/coauthors/coauthors/{scopus_id}/coauthors_by_id/"
        response = await resilient_get(url)
        response.raise_for_status()
        data = response.json()

        author_coauthors_cache[cache_key] = data
        return data

    async def get_author_topics(self, scopus_id: str) -> Any:
        cache_key = make_key("author_topics", scopus_id)

        cached = author_topics_cache.get(cache_key)
        if cached is not None:
            logger.info(f"[CACHE HIT] author_topics | key={cache_key}")
            return cached

        logger.info(f"[CACHE MISS] author_topics | key={cache_key}")

        url = f"{settings.BASE_URL.rstrip('/')}/api-se/v1/dashboard/author/get_topics/"
        response = await resilient_get(url, params={"scopus_id": scopus_id})
        response.raise_for_status()
        data = response.json()

        author_topics_cache[cache_key] = data
        return data

    async def get_author_years(self, scopus_id: str) -> Any:
        cache_key = make_key("author_years", scopus_id)

        cached = author_years_cache.get(cache_key)
        if cached is not None:
            logger.info(f"[CACHE HIT] author_years | key={cache_key}")
            return cached

        logger.info(f"[CACHE MISS] author_years | key={cache_key}")

        url = f"{settings.BASE_URL.rstrip('/')}/api-se/v1/dashboard/author/get_author_years/"
        response = await resilient_get(url, params={"scopus_id": scopus_id})
        response.raise_for_status()
        data = response.json()

        author_years_cache[cache_key] = data
        return data
