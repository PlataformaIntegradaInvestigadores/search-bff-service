from typing import Any

from app.domain.article_repositories import IArticleRepository


class ArticlesByAuthorUseCase:
    def __init__(self, repository: IArticleRepository):
        self.repository = repository

    async def execute(self, author_id: str) -> list[dict[str, Any]]:
        return await self.repository.find_articles_by_author(author_id=author_id)
