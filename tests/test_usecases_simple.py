"""Unitarias de los usecases delegadores simples (una linea al repositorio)."""

import asyncio
from unittest.mock import AsyncMock

from app.application.usecases.article_detail_usecase import ArticleDetailUseCase
from app.application.usecases.articles_by_author_usecase import (
    ArticlesByAuthorUseCase,
)
from app.application.usecases.author_detail_usecase import AuthorDetailUseCase
from app.application.usecases.authors_search_usecase import AuthorsSearchUseCase
from app.application.usecases.relevant_articles_usecase import (
    RelevantArticlesUseCase,
)


class TestArticleDetailUseCase:
    def test_delega_al_repositorio_con_el_scopus_id(self):
        repo = AsyncMock()
        repo.get_article_by_id.return_value = {"scopus_id": "1", "title": "X"}
        result = asyncio.run(ArticleDetailUseCase(repo).execute("1"))
        repo.get_article_by_id.assert_awaited_once_with("1")
        assert result["title"] == "X"


class TestArticlesByAuthorUseCase:
    def test_delega_al_repositorio_con_author_id(self):
        repo = AsyncMock()
        repo.find_articles_by_author.return_value = [{"title": "Y"}]
        result = asyncio.run(ArticlesByAuthorUseCase(repo).execute("57193901649"))
        repo.find_articles_by_author.assert_awaited_once_with(author_id="57193901649")
        assert result == [{"title": "Y"}]


class TestRelevantArticlesUseCase:
    def test_delega_al_repositorio_con_filtros(self):
        repo = AsyncMock()
        repo.most_relevant_articles.return_value = {"data": [], "total": 0}
        result = asyncio.run(
            RelevantArticlesUseCase(repo).execute(
                query="ml", page=2, page_size=10, years=[2023, 2024]
            )
        )
        repo.most_relevant_articles.assert_awaited_once_with(
            query="ml", page=2, page_size=10, years=[2023, 2024]
        )
        assert result == {"data": [], "total": 0}


class TestAuthorDetailUseCase:
    def test_delega_al_repositorio_con_scopus_id(self):
        repo = AsyncMock()
        repo.get_author_by_id.return_value = {"scopus_id": "1"}
        result = asyncio.run(AuthorDetailUseCase(repo).execute("1"))
        repo.get_author_by_id.assert_awaited_once_with(scopus_id="1")
        assert result == {"scopus_id": "1"}


class TestAuthorsSearchUseCase:
    def test_delega_al_repositorio_con_paginacion(self):
        repo = AsyncMock()
        repo.find_authors_by_query.return_value = {"data": [], "total": 0}
        result = asyncio.run(
            AuthorsSearchUseCase(repo).execute(query="ai", page=1, page_size=10)
        )
        repo.find_authors_by_query.assert_awaited_once_with(
            query="ai", page=1, page_size=10
        )
        assert result == {"data": [], "total": 0}
