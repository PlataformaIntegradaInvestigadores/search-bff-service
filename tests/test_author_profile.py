"""Suite C — Unitarias de la composicion (Slice 2: AuthorProfileUseCase).

Mockea los repositorios (Neo4j/Mongo/Elsevier via v1) para probar la orquestacion
en aislamiento.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from app.application.usecases.author_profile_usecase import AuthorProfileUseCase


def _build(authors, articles):
    return AuthorProfileUseCase(
        authors_repository=authors, articles_repository=articles
    )


def _authors_ok():
    m = AsyncMock()
    m.get_author_by_id.return_value = {"scopus_id": 1, "auth_name": "Recalde L."}
    m.get_coauthors.return_value = {"data": []}
    m.get_author_topics.return_value = [{"text": "ml", "size": 3}]
    m.get_author_years.return_value = [{"year": 2024, "total_articles": 5}]
    return m


def _articles_ok():
    m = AsyncMock()
    m.find_articles_by_author.return_value = [{"title": "X"}]
    return m


class TestComposicion:
    def test_ensambla_las_cinco_secciones(self):
        result = asyncio.run(_build(_authors_ok(), _articles_ok()).execute("1"))
        assert result["author"]["scopus_id"] == "1"  # coercion a str
        assert result["degraded"] == []
        assert len(result["topics"]) == 1
        assert len(result["years"]) == 1
        assert len(result["articles"]) == 1

    def test_degradacion_parcial_marca_degraded(self):
        authors = _authors_ok()
        authors.get_coauthors.side_effect = Exception("v1 down")
        authors.get_author_topics.side_effect = Exception("v1 down")
        result = asyncio.run(_build(authors, _articles_ok()).execute("1"))
        assert set(result["degraded"]) == {"coauthors", "topics"}
        assert result["coauthors"] is None
        assert result["topics"] == []
        # las secciones sanas siguen presentes
        assert result["author"]["auth_name"] == "Recalde L."
        assert len(result["articles"]) == 1

    def test_fallo_del_nucleo_propaga_error(self):
        authors = _authors_ok()
        authors.get_author_by_id.side_effect = RuntimeError("author not found")
        with pytest.raises(RuntimeError):
            asyncio.run(_build(authors, _articles_ok()).execute("1"))
