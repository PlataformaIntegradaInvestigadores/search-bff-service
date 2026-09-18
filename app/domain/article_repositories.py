from abc import ABC, abstractmethod
from typing import Any


class IArticleRepository(ABC):
    @abstractmethod
    async def most_relevant_articles(
        self,
        query: str,
        page: int,
        page_size: int,
        years: list[int] | None = None,
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def find_articles_by_author(self, author_id: str) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def get_article_by_id(self, scopus_id: str) -> dict[str, Any]:
        pass
