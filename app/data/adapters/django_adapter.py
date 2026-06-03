import logging
from typing import List
from app.domain.entities import SearchResult, SearchQuery
from app.domain.repositories import ISearchRepository
from app.core.config import settings
from app.core.http_client import http_client

logger = logging.getLogger(__name__)

class DjangoSearchAdapter(ISearchRepository):
    """Bridge temporal al endpoint v1 de Django (ADR-05)."""

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        payload = {
            "query": query.query,
            "top_k": query.page_size * 3
        }

        response = await http_client.post(settings.V1_SEARCH_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("data", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                abstract=item.get("abstract", ""),
                scopus_id=str(item.get("scopus_id", "")),
                publication_date=item.get("publication_date"),
                relevance=float(item.get("relevance", 0.0))
            ))
        return results