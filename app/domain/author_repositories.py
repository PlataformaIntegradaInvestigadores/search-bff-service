from abc import ABC, abstractmethod
from typing import Any


class IAuthorRepository(ABC):
    @abstractmethod
    async def most_relevant_authors(
        self,
        query: str,
        authors_number: int,
        affiliations: list[str] | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def find_authors_by_query(
        self,
        query: str,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_author_by_id(self, scopus_id: str) -> dict[str, Any]:
        pass
