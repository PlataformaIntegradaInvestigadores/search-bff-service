import logging

from app.core.config import settings
from app.core.resilience import resilient_post
from app.domain.entities import SearchQuery, SearchResult
from app.domain.repositories import ISearchRepository

logger = logging.getLogger(__name__)


class DjangoSearchAdapter(ISearchRepository):
    """Bridge temporal al endpoint v1 de Django (ADR-05)."""

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        payload = {"query": query.query, "top_k": query.page_size * 3}

        response = await resilient_post(settings.V1_SEARCH_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("data", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    abstract=item.get("abstract", ""),
                    scopus_id=str(item.get("scopus_id", "")),
                    publication_date=item.get("publication_date"),
                    relevance=float(item.get("relevance", 0.0)),
                )
            )
        return results
