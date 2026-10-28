from typing import Any

from pydantic import BaseModel, Field


class AuthorsFilters(BaseModel):
    affiliations: list[str] | None = Field(
        default=None, description="Limita el resultado a estas afiliaciones."
    )
    mode: str | None = Field(
        default=None,
        description="Modo de relación entre los filtros de afiliación.",
    )


class AuthorsRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Texto de la búsqueda de autores relevantes.",
        examples=["inteligencia artificial"],
    )
    page: int = Field(default=1, ge=1, description="Número de página, desde 1.")
    page_size: int = Field(
        default=10, ge=1, le=200, description="Resultados por página (máximo 200)."
    )
    filters: AuthorsFilters | None = Field(
        default=None, description="Filtros opcionales."
    )


class AuthorsSearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Nombre o parte del nombre del autor.",
        examples=["Pérez"],
    )
    page: int = Field(default=1, ge=1, description="Número de página, desde 1.")
    page_size: int = Field(
        default=10, ge=1, le=100, description="Resultados por página (máximo 100)."
    )


class AuthorNode(BaseModel):
    scopus_id: str = Field(..., description="ID del autor en Scopus.")
    first_name: str = Field(..., description="Nombres.")
    last_name: str = Field(..., description="Apellidos.")
    auth_name: str = Field(..., description="Nombre con el que firma, estilo Scopus.")
    initials: str = Field(..., description="Iniciales.")
    affiliations: list[str] = Field(default=[], description="Afiliaciones del autor.")
    articles: int = Field(default=0, description="Cantidad de artículos.")
    co_authors: list[str] = Field(
        default=[], description="IDs de Scopus de sus coautores."
    )
    topics: list[str] = Field(default=[], description="Tópicos en los que publica.")
    citation_count: int = Field(default=0, description="Citas acumuladas.")
    current_affiliation: str | None = Field(
        default=None, description="Afiliación actual, si se conoce."
    )


class AuthorLink(BaseModel):
    source: str = Field(..., description="ID de Scopus del autor de origen.")
    target: str = Field(..., description="ID de Scopus del autor de destino.")
    collabStrength: float = Field(
        ..., description="Fuerza de la colaboración entre ambos autores."
    )


class AffiliationItem(BaseModel):
    scopus_id: str = Field(..., description="ID de la afiliación en Scopus.")
    name: str = Field(..., description="Nombre de la afiliación.")


class RelevantAuthorsResponse(BaseModel):
    nodes: list[AuthorNode] = Field(..., description="Autores relevantes (nodos).")
    links: list[AuthorLink] = Field(
        ..., description="Colaboraciones entre los autores (aristas)."
    )
    affiliations: list[AffiliationItem] = Field(
        ..., description="Afiliaciones presentes en el resultado."
    )
    total_results: int = Field(..., description="Total de autores, sin paginar.")
    page: int = Field(..., description="Página devuelta.")
    page_size: int = Field(..., description="Tamaño de página usado.")


class AuthorSearchItem(BaseModel):
    scopus_id: str = Field(..., description="ID del autor en Scopus.")
    name: str = Field(..., description="Nombre del autor.")
    affiliations: int = Field(..., description="Cantidad de afiliaciones.")
    articles: int = Field(..., description="Cantidad de artículos.")
    topics: int = Field(..., description="Cantidad de tópicos.")
    current_affiliation: str | None = Field(
        default=None, description="Afiliación actual, si se conoce."
    )
    citation_count: int = Field(..., description="Citas acumuladas.")
    updated: bool = Field(
        ..., description="Si los datos del autor ya fueron actualizados desde Scopus."
    )


class AuthorsSearchResponse(BaseModel):
    total: int = Field(..., description="Total de autores que coinciden.")
    next_page: str | None = Field(
        default=None, description="URL de la página siguiente; nula en la última."
    )
    previous_page: str | None = Field(
        default=None, description="URL de la página anterior; nula en la primera."
    )
    data: list[AuthorSearchItem] = Field(..., description="Autores de la página.")


class AuthorProfileResponse(BaseModel):
    """Respuesta compuesta del perfil de autor (Slice 2). 'author' es el nucleo
    tipado; el resto se pasa tal cual viene de v1 (tolerante a su forma)."""

    author: AuthorNode = Field(..., description="Datos principales del autor.")
    topics: list[Any] = Field(
        default=[], description="Tópicos del autor, tal como los entrega v1."
    )
    coauthors: Any = Field(
        default=None, description="Red de coautores, tal como la entrega v1."
    )
    years: list[Any] = Field(
        default=[], description="Publicaciones por año, tal como las entrega v1."
    )
    articles: list[Any] = Field(
        default=[], description="Artículos del autor, tal como los entrega v1."
    )
    degraded: list[str] = Field(
        default=[],
        description="Secciones que no se pudieron obtener y quedaron vacías porque "
        "el servicio de búsqueda falló parcialmente.",
    )
