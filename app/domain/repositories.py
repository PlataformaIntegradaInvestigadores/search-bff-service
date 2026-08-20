from abc import ABC, abstractmethod

from app.domain.entities import SearchQuery, SearchResult


class ISearchRepository(ABC):
    @abstractmethod
    async def search(self, query: SearchQuery) -> list[SearchResult]:
        pass
