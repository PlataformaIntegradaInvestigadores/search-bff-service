import httpx
import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
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
        payload: Dict[str, Any] = {
            "topic": query,
            "authors_number": authors_number,
        }

        if affiliations:
            payload["affiliations"] = affiliations
            if mode:
                payload["type"] = mode

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.V1_AUTHORS_URL, json=payload)
            response.raise_for_status()
            return response.json()

    async def find_authors_by_query(
        self,
        query: str,
        page: int,
        page_size: int,
    ) -> Dict[str, Any]:
        params = {
            "query": query,
            "page": page,
            "page_size": page_size,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(settings.V1_AUTHORS_FIND_URL, params=params)
            response.raise_for_status()
            return response.json()

    async def get_author_by_id(self, scopus_id: str) -> Dict[str, Any]:
        base_url = settings.V1_AUTHORS_DETAIL_URL.rstrip("/")
        url = f"{base_url}/{scopus_id}/"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
