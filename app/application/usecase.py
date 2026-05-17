import time
from tracemalloc import start
from typing import List
from app.domain.entities import SearchQuery
from app.domain.repositories import ISearchRepository

class SemanticSearchUseCase:
    def __init__(self, repository: ISearchRepository):
        self.repository = repository

    async def execute(self, query: str, page: int, page_size: int,
                      filter_years=None, filter_type=None):
        search_query = SearchQuery(
            query=query,
            page=page,
            page_size=page_size,
            filter_years=filter_years,
            filter_type=filter_type
        )

        start = time.time()
        results = await self.repository.search(search_query)
        elapsed_ms = (time.time() - start) * 1000

        # Paginacion real sobre resultados del bridge
        start_idx = (page - 1) * page_size
        paginated = results[start_idx : start_idx + page_size]
        total = len(results)

        return paginated, elapsed_ms, total