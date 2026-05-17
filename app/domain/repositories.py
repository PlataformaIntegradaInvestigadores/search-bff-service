from abc import ABC, abstractmethod
from typing import List
from app.domain.entities import SearchResult, SearchQuery

class ISearchRepository(ABC):
    @abstractmethod
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        pass