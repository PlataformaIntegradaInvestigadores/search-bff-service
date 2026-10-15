"""Suite C — Unitarias de la cache de subsecciones del perfil (refinamiento Slice 2).

Verifica que get_coauthors / get_author_topics / get_author_years memoizan en v2:
la 2a llamada con el mismo scopus_id NO vuelve a pegar a v1 (CACHE HIT), y que
ids distintos usan claves distintas (no se contaminan).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.cache import (
    author_coauthors_cache,
    author_topics_cache,
    author_years_cache,
)
from app.data.adapters.django_authors_adapter import DjangoAuthorsAdapter


def _fake_response(payload):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    return resp


@pytest.fixture(autouse=True)
def _clear_caches():
    for c in (author_coauthors_cache, author_topics_cache, author_years_cache):
        c.clear()
    yield
    for c in (author_coauthors_cache, author_topics_cache, author_years_cache):
        c.clear()


class TestCoauthorsUrl:
    def test_get_coauthors_pega_a_la_ruta_registrada_sin_segmento_duplicado(self):
        # Regresion: la URL tenia "coauthors/coauthors/" duplicado (el
        # prefijo del router "coauthors/" montado en root_urls.py mas otro
        # "coauthors/" agregado a mano aca), asi que siempre pegaba 404 y
        # get_coauthors() se degradaba en silencio a coauthors: null en
        # cada author_profile -- el frontend se colgaba en el spinner de
        # carga (ver coauthors-graph.component.ts) sin ningun error visible.
        adapter = DjangoAuthorsAdapter()
        mock_get = AsyncMock(return_value=_fake_response({"data": {"nodes": [], "links": []}}))
        with patch(
            "app.data.adapters.django_authors_adapter.resilient_get", new=mock_get
        ):
            asyncio.run(adapter.get_coauthors("57193901649"))

        called_url = mock_get.await_args.args[0]
        assert called_url == "http://localhost:8001/api-se/v1/coauthors/57193901649/coauthors_by_id/"


class TestCacheSubseccionesPerfil:
    def test_coauthors_segunda_llamada_es_hit(self):
        adapter = DjangoAuthorsAdapter()
        mock_get = AsyncMock(return_value=_fake_response({"data": [1, 2]}))
        with patch(
            "app.data.adapters.django_authors_adapter.resilient_get", new=mock_get
        ):
            first = asyncio.run(adapter.get_coauthors("57193901649"))
            second = asyncio.run(adapter.get_coauthors("57193901649"))
        assert first == second == {"data": [1, 2]}
        assert mock_get.await_count == 1  # la 2a se sirvio desde cache, no pego a v1

    def test_topics_segunda_llamada_es_hit(self):
        adapter = DjangoAuthorsAdapter()
        mock_get = AsyncMock(return_value=_fake_response([{"text": "ml", "size": 3}]))
        with patch(
            "app.data.adapters.django_authors_adapter.resilient_get", new=mock_get
        ):
            asyncio.run(adapter.get_author_topics("1"))
            asyncio.run(adapter.get_author_topics("1"))
        assert mock_get.await_count == 1

    def test_years_segunda_llamada_es_hit(self):
        adapter = DjangoAuthorsAdapter()
        mock_get = AsyncMock(
            return_value=_fake_response([{"year": 2024, "total_articles": 5}])
        )
        with patch(
            "app.data.adapters.django_authors_adapter.resilient_get", new=mock_get
        ):
            asyncio.run(adapter.get_author_years("1"))
            asyncio.run(adapter.get_author_years("1"))
        assert mock_get.await_count == 1

    def test_ids_distintos_no_comparten_cache(self):
        adapter = DjangoAuthorsAdapter()
        mock_get = AsyncMock(return_value=_fake_response({"data": []}))
        with patch(
            "app.data.adapters.django_authors_adapter.resilient_get", new=mock_get
        ):
            asyncio.run(adapter.get_coauthors("1"))
            asyncio.run(
                adapter.get_coauthors("2")
            )  # otro autor -> MISS, clave distinta
        assert mock_get.await_count == 2
