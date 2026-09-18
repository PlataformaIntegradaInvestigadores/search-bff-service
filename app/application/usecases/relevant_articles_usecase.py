from typing import Any

from app.domain.article_repositories import IArticleRepository


class RelevantArticlesUseCase:
    def __init__(self, repository: IArticleRepository):
        self.repository = repository

    async def execute(
        self,
        query: str,
        page: int,
        page_size: int,
        years: list[int] | None = None,
    ) -> dict[str, Any]:
        return await self.repository.most_relevant_articles(
            query=query,
            page=page,
            page_size=page_size,
            years=years,
        )
