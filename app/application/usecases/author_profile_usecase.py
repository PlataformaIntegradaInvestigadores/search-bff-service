"""Caso de uso de composicion del perfil de autor (Slice 2 / API Composition).

v2 actua como COMPOSITOR (rol citado en US6 / patron API Composition, S195):
ensambla en una sola respuesta el detalle del autor + topics + coautores + anios
+ articulos, orquestando varias llamadas a v1 EN PARALELO.

Politica de fallos: el detalle del autor es el nucleo (si falla, se propaga el
error y el endpoint responde 503/500). Las demas secciones son enriquecimientos
best-effort: si una falla, se devuelve vacia y el perfil sigue siendo util.
"""
import asyncio
import logging

logger = logging.getLogger(__name__)


class AuthorProfileUseCase:
    def __init__(self, authors_repository, articles_repository):
        self.authors = authors_repository
        self.articles = articles_repository

    async def execute(self, scopus_id: str) -> dict:
        author, coauthors, topics, years, articles = await asyncio.gather(
            self.authors.get_author_by_id(scopus_id),
            self.authors.get_coauthors(scopus_id),
            self.authors.get_author_topics(scopus_id),
            self.authors.get_author_years(scopus_id),
            self.articles.find_articles_by_author(scopus_id),
            return_exceptions=True,
        )

        # Nucleo obligatorio: el detalle del autor.
        if isinstance(author, Exception):
            raise author

        author["scopus_id"] = str(author.get("scopus_id", ""))

        def best_effort(value, default, label):
            if isinstance(value, Exception):
                logger.warning(f"[author_profile {scopus_id}] seccion '{label}' fallo: {value}")
                return default
            return value

        return {
            "author": author,
            "topics": best_effort(topics, [], "topics"),
            "coauthors": best_effort(coauthors, None, "coauthors"),
            "years": best_effort(years, [], "years"),
            "articles": best_effort(articles, [], "articles"),
        }
