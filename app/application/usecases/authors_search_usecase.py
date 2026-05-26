from typing import Any, Dict

from app.domain.author_repositories import IAuthorRepository


class AuthorsSearchUseCase:
    def __init__(self, repository: IAuthorRepository):
        self.repository = repository

    async def execute(self, query: str, page: int, page_size: int) -> Dict[str, Any]:
        return await self.repository.find_authors_by_query(
            query=query,
            page=page,
            page_size=page_size,
        )
