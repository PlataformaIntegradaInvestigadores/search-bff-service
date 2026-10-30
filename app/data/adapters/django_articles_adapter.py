import logging
from typing import Any

from app.core.cache import (
    article_detail_cache,
    articles_by_author_cache,
    articles_cache,
    make_key,
)
from app.core.config import settings
from app.core.resilience import resilient_get, resilient_post
from app.domain.article_repositories import IArticleRepository

logger = logging.getLogger(__name__)

def _normalize_relevant_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Ensure the shape expected by RelevantArticlesResponse."""
    items = data.get("data") or []
    total = int(data.get("total") or len(items))
    return {
        "data": items,
        "years": data.get("years") or [],
        "total": total,
        "total_results": data.get("total_results", total),
    }

def _map_semantic_to_relevant(
    semantic: dict[str, Any],
    *,
    page: int,
    page_size: int,
    years: list[int] | None,
) -> dict[str, Any]:
    """Adapt llm-search semantic hits into the articles/relevant contract."""
    items = semantic.get("data") or []
    if years:
        year_set = {str(y) for y in years}
        items = [
            item
            for item in items
            if str(item.get("publication_date", "")).split("-")[0] in year_set
        ]

    start = max(page - 1, 0) * page_size
    page_items = items[start : start + page_size]
    mapped = []
    for item in page_items:
        authors = item.get("authors") or []
        if authors and isinstance(authors[0], dict):
            authors = [
                a.get("name") or a.get("auth_name") or "" for a in authors if a
            ]
        affiliations = item.get("affiliations") or []
        if affiliations and isinstance(affiliations[0], dict):
            affiliations = [a.get("name") or "" for a in affiliations if a]

        mapped.append(
            {
                "title": item.get("title") or "",
                "abstract": item.get("abstract") or "",
                "author_count": int(item.get("author_count") or 0),
                "affiliation_count": int(item.get("affiliation_count") or 0),
                "publication_date": item.get("publication_date") or "",
                "scopus_id": str(item.get("scopus_id") or ""),
                "relevance": float(item.get("relevance") or 0.0),
                "authors": authors or None,
                "affiliations": affiliations or None,
            }
        )

    years_out = semantic.get("years") or []
    return _normalize_relevant_payload(
        {
            "data": mapped,
            "years": years_out,
            "total": len(mapped),
            "total_results": len(items),
        }
    )

class DjangoArticlesAdapter(IArticleRepository):
    """Bridge temporal al endpoint v1 de articles en Django (ADR-05)."""

    async def most_relevant_articles(
        self,
        query: str,
        page: int,
        page_size: int,
        years: list[int] | None = None,
    ) -> dict[str, Any]:
        years_key = str(sorted(years)) if years else "none"
        cache_key = make_key("articles_relevant", query, page, page_size, years_key)

        cached = articles_cache.get(cache_key)
        if cached is not None:
            logger.info(f"[CACHE HIT] articles_relevant | key={cache_key}")
            return cached

        logger.info(f"[CACHE MISS] articles_relevant | key={cache_key}")

        payload: dict[str, Any] = {
            "query": query,
            "page": page,
            "size": page_size,
        }

        if years:
            payload["type"] = "include"
            payload["years"] = [str(year) for year in years]

        response = await resilient_post(settings.V1_ARTICLES_RELEVANT_URL, json=payload)
        response.raise_for_status()
        data = _normalize_relevant_payload(response.json())

        # TF-IDF pickle no incluye artículos mock de Neo4j. Si viene vacío,
        # degradamos a búsqueda semántica (llm-search) para entornos locales.
        if not data.get("data"):
            logger.info(
                "[articles_relevant] TF-IDF vacío; fallback a semantic-search"
            )
            semantic_payload = {
                "query": query,
                "top_k": max(page * page_size, page_size),
            }
            semantic_resp = await resilient_post(
                settings.V1_SEARCH_URL, json=semantic_payload
            )
            semantic_resp.raise_for_status()
            data = _map_semantic_to_relevant(
                semantic_resp.json(),
                page=page,
                page_size=page_size,
                years=years,
            )


        articles_cache[cache_key] = data
        return data

    async def find_articles_by_author(self, author_id: str) -> list[dict[str, Any]]:
        cache_key = make_key("articles_by_author", author_id)

        cached = articles_by_author_cache.get(cache_key)
        if cached is not None:
            logger.info(f"[CACHE HIT] articles_by_author | key={cache_key}")
            return cached

        logger.info(f"[CACHE MISS] articles_by_author | key={cache_key}")

        params = {"author_id": author_id}

        response = await resilient_get(
            settings.V1_ARTICLES_BY_AUTHOR_URL, params=params
        )
        response.raise_for_status()
        data = response.json()

        articles_by_author_cache[cache_key] = data
        return data

    async def get_article_by_id(self, scopus_id: str) -> dict[str, Any]:
        cache_key = make_key("article_detail", scopus_id)

        cached = article_detail_cache.get(cache_key)
        if cached is not None:
            logger.info(f"[CACHE HIT] article_detail | key={cache_key}")
            return cached

        logger.info(f"[CACHE MISS] article_detail | key={cache_key}")

        url = f"{settings.V1_ARTICLES_DETAIL_URL}{scopus_id}/"

        response = await resilient_get(url)
        response.raise_for_status()
        data = response.json()

        article_detail_cache[cache_key] = data
        return data
