from typing import Any

from app.domain.author_repositories import IAuthorRepository


class AuthorDetailUseCase:
    def __init__(self, repository: IAuthorRepository):
        self.repository = repository

    async def execute(self, scopus_id: str) -> dict[str, Any]:
        return await self.repository.get_author_by_id(scopus_id=scopus_id)
