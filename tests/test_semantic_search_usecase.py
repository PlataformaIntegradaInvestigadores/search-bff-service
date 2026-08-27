"""Unitarias de SemanticSearchUseCase: filtro local por anio (v1 no lo soporta) +
paginacion real sobre los resultados ya filtrados."""

import asyncio
from unittest.mock import AsyncMock

from app.application.usecases.usecase import SemanticSearchUseCase
from app.domain.entities import SearchResult


def _result(scopus_id, date):
    return SearchResult(
        title=f"Articulo {scopus_id}",
        abstract="...",
        scopus_id=scopus_id,
        publication_date=date,
        relevance=0.9,
    )


class TestSemanticSearchUseCase:
    def test_sin_filtro_de_anio_pagina_todos_los_resultados(self):
        repo = AsyncMock()
        repo.search.return_value = [_result(str(i), "2023-01-01") for i in range(5)]
        paginated, elapsed_ms, total = asyncio.run(
            SemanticSearchUseCase(repo).execute(query="ml", page=1, page_size=2)
        )
        assert len(paginated) == 2
        assert total == 5
        assert elapsed_ms >= 0

    def test_filtra_por_anio_antes_de_paginar(self):
        repo = AsyncMock()
        repo.search.return_value = [
            _result("1", "2022-01-01"),
            _result("2", "2023-06-01"),
            _result("3", "2023-12-01"),
        ]
        paginated, _, total = asyncio.run(
            SemanticSearchUseCase(repo).execute(
                query="ml", page=1, page_size=10, filter_years=[2023]
            )
        )
        assert total == 2
        assert {r.scopus_id for r in paginated} == {"2", "3"}

    def test_resultado_sin_fecha_se_excluye_si_hay_filtro_de_anio(self):
        repo = AsyncMock()
        repo.search.return_value = [_result("1", None), _result("2", "2023-01-01")]
        paginated, _, total = asyncio.run(
            SemanticSearchUseCase(repo).execute(
                query="ml", page=1, page_size=10, filter_years=[2023]
            )
        )
        assert total == 1
        assert paginated[0].scopus_id == "2"

    def test_segunda_pagina_respeta_page_size(self):
        repo = AsyncMock()
        repo.search.return_value = [_result(str(i), "2023-01-01") for i in range(5)]
        paginated, _, total = asyncio.run(
            SemanticSearchUseCase(repo).execute(query="ml", page=2, page_size=2)
        )
        assert [r.scopus_id for r in paginated] == ["2", "3"]
        assert total == 5
