from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IArticleRepository(ABC):
    @abstractmethod
    async def most_relevant_articles(
        self,
        query: str,
        page: int,
        page_size: int,
        years: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def find_articles_by_author(self, author_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_article_by_id(self, scopus_id: str) -> Dict[str, Any]:
        pass
