import time
from tracemalloc import start
from typing import List
from app.domain.entities import SearchQuery
from app.domain.repositories import ISearchRepository

class SemanticSearchUseCase:
    def __init__(self, repository: ISearchRepository):
        self.repository = repository

    async def execute(self, query: str, page: int, page_size: int,
                      filter_years=None):
        search_query = SearchQuery(
            query=query,
            page=page,
            page_size=page_size,
            filter_years=filter_years
        )

        start = time.time()
        results = await self.repository.search(search_query)
        elapsed_ms = (time.time() - start) * 1000

        # Filtros locales para el bridge v1 (no soporta filtros en la API)
        filtered = results
        if filter_years:
            filter_years_set = {str(year) for year in filter_years}
            filtered = [
                item for item in filtered
                if item.publication_date
                and item.publication_date.split("-")[0] in filter_years_set
            ]

        # Paginacion real sobre resultados filtrados
        start_idx = (page - 1) * page_size
        paginated = filtered[start_idx : start_idx + page_size]
        total = len(filtered)

        return paginated, elapsed_ms, total