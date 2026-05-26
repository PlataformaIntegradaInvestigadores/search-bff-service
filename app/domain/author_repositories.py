from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IAuthorRepository(ABC):
    @abstractmethod
    async def most_relevant_authors(
        self,
        query: str,
        authors_number: int,
        affiliations: Optional[List[str]] = None,
        mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def find_authors_by_query(
        self,
        query: str,
        page: int,
        page_size: int,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_author_by_id(self, scopus_id: str) -> Dict[str, Any]:
        pass
