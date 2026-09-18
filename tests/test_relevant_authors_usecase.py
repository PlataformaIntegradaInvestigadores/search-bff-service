"""Unitarias de RelevantAuthorsUseCase: paginacion local de nodos + filtrado de
enlaces cuyos extremos caen fuera de la pagina, y normalizacion de afiliaciones."""

import asyncio
from unittest.mock import AsyncMock

from app.application.usecases.relevant_authors_usecase import RelevantAuthorsUseCase


def _node(scopus_id):
    return {"scopus_id": scopus_id, "auth_name": f"Autor {scopus_id}"}


class TestRelevantAuthorsUseCase:
    def test_pagina_los_nodos_y_filtra_links_fuera_de_pagina(self):
        repo = AsyncMock()
        repo.most_relevant_authors.return_value = {
            "nodes": [_node("1"), _node("2"), _node("3")],
            "links": [
                {"source": "1", "target": "2", "collabStrength": 0.5},
                {"source": "2", "target": "3", "collabStrength": 0.3},
            ],
            "affiliations": [{"scopusId": "aff1", "name": "UCE"}],
            "size_nodes": 3,
        }

        nodes, links, affiliations, total = asyncio.run(
            RelevantAuthorsUseCase(repo).execute(query="ml", page=1, page_size=2)
        )

        assert [n["scopus_id"] for n in nodes] == ["1", "2"]
        # el link 2->3 queda fuera porque "3" no esta en la pagina
        assert links == [{"source": "1", "target": "2", "collabStrength": 0.5}]
        assert total == 3
        assert affiliations[0]["scopus_id"] == "aff1"  # ACL camelCase -> snake_case

    def test_calcula_authors_number_como_page_por_page_size(self):
        repo = AsyncMock()
        repo.most_relevant_authors.return_value = {
            "nodes": [],
            "links": [],
            "affiliations": [],
        }
        asyncio.run(
            RelevantAuthorsUseCase(repo).execute(
                query="ml", page=3, page_size=10, affiliations=["UCE"], mode="include"
            )
        )
        repo.most_relevant_authors.assert_awaited_once_with(
            query="ml",
            authors_number=30,
            affiliations=["UCE"],
            mode="include",
        )

    def test_total_cae_a_len_nodes_si_falta_size_nodes(self):
        repo = AsyncMock()
        repo.most_relevant_authors.return_value = {
            "nodes": [_node("1")],
            "links": [],
            "affiliations": [],
        }
        _, _, _, total = asyncio.run(
            RelevantAuthorsUseCase(repo).execute(query="ml", page=1, page_size=10)
        )
        assert total == 1
