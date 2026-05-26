from typing import Any, Dict

from app.domain.article_repositories import IArticleRepository


class ArticleDetailUseCase:
    def __init__(self, repository: IArticleRepository):
        self.repository = repository

    async def execute(self, scopus_id: str) -> Dict[str, Any]:
        return await self.repository.get_article_by_id(scopus_id)
