"""Verifica que las factory functions de cada router arman el usecase correcto
con el adapter esperado (las llamadas reales quedan mockeadas en los tests de
endpoints, asi que estas lineas no se ejercitan ahi)."""

from app.api.v2 import articles, authors, search
from app.application.usecases.article_detail_usecase import ArticleDetailUseCase
from app.application.usecases.articles_by_author_usecase import (
    ArticlesByAuthorUseCase,
)
from app.application.usecases.author_detail_usecase import AuthorDetailUseCase
from app.application.usecases.author_profile_usecase import AuthorProfileUseCase
from app.application.usecases.authors_search_usecase import AuthorsSearchUseCase
from app.application.usecases.relevant_articles_usecase import (
    RelevantArticlesUseCase,
)
from app.application.usecases.relevant_authors_usecase import RelevantAuthorsUseCase
from app.application.usecases.usecase import SemanticSearchUseCase


class TestSearchFactory:
    def test_get_use_case_arma_semantic_search_use_case(self):
        assert isinstance(search.get_use_case(), SemanticSearchUseCase)


class TestArticlesFactories:
    def test_get_relevant_use_case(self):
        assert isinstance(articles.get_relevant_use_case(), RelevantArticlesUseCase)

    def test_get_by_author_use_case(self):
        assert isinstance(articles.get_by_author_use_case(), ArticlesByAuthorUseCase)

    def test_get_detail_use_case(self):
        assert isinstance(articles.get_detail_use_case(), ArticleDetailUseCase)


class TestAuthorsFactories:
    def test_get_use_case(self):
        assert isinstance(authors.get_use_case(), RelevantAuthorsUseCase)

    def test_get_search_use_case(self):
        assert isinstance(authors.get_search_use_case(), AuthorsSearchUseCase)

    def test_get_detail_use_case(self):
        assert isinstance(authors.get_detail_use_case(), AuthorDetailUseCase)

    def test_get_profile_use_case(self):
        assert isinstance(authors.get_profile_use_case(), AuthorProfileUseCase)
