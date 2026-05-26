import httpx
import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
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
        payload: Dict[str, Any] = {
            "query": query,
            "page": page,
            "size": page_size,
        }

        if years:
            payload["years"] = [str(year) for year in years]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.V1_ARTICLES_RELEVANT_URL, json=payload)
            response.raise_for_status()
            return response.json()

    async def find_articles_by_author(self, author_id: str) -> List[Dict[str, Any]]:
        params = {"author_id": author_id}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(settings.V1_ARTICLES_BY_AUTHOR_URL, params=params)
            response.raise_for_status()
            return response.json()

    async def get_article_by_id(self, scopus_id: str) -> Dict[str, Any]:
        url = f"{settings.V1_ARTICLES_DETAIL_URL}{scopus_id}/"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
