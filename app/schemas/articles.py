from pydantic import BaseModel, Field


class ArticleFilters(BaseModel):
    years: list[int] | None = Field(
        default=None,
        description="Limita los resultados a artículos de estos años.",
        examples=[[2023, 2024]],
    )


class RelevantArticlesRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Texto de la búsqueda de artículos.",
        examples=["energías renovables"],
    )
    page: int = Field(default=1, ge=1, description="Número de página, desde 1.")
    page_size: int = Field(
        default=10, ge=1, le=100, description="Resultados por página (máximo 100)."
    )
    filters: ArticleFilters | None = Field(
        default=None, description="Filtros opcionales."
    )


class RelevantArticleItem(BaseModel):
    title: str = Field(..., description="Título del artículo.")
    author_count: int = Field(..., description="Cantidad de autores.")
    affiliation_count: int = Field(..., description="Cantidad de afiliaciones.")
    publication_date: str = Field(..., description="Fecha de publicación.")
    scopus_id: str = Field(..., description="ID del artículo en Scopus.")
    relevance: float = Field(
        ..., description="Puntaje de relevancia respecto a la consulta."
    )
    abstract: str | None = Field(
        default=None, description="Resumen del artículo, si está disponible."
    )
    authors: list[str] | None = Field(
        default=None, description="Nombres de los autores."
    )
    affiliations: list[str] | None = Field(
        default=None, description="Afiliaciones de los autores."
    )


class RelevantArticlesResponse(BaseModel):
    data: list[RelevantArticleItem] = Field(..., description="Artículos de la página.")
    years: list[int | str] = Field(
        default=[], description="Años presentes en los resultados."
    )
    total: int = Field(..., description="Cantidad de artículos en esta página.")
    total_results: int | None = Field(
        default=None, description="Total de artículos que coinciden, sin paginar."
    )


class ArticleAuthorItem(BaseModel):
    name: str = Field(..., description="Nombre del autor.")
    scopus_id: str | None = Field(
        default=None, description="ID del autor en Scopus, si se conoce."
    )


class ArticleDetailResponse(BaseModel):
    title: str = Field(..., description="Título del artículo.")
    abstract: str = Field(..., description="Resumen del artículo.")
    doi: str = Field(..., description="DOI del artículo.")
    publication_date: str = Field(..., description="Fecha de publicación.")
    author_count: int = Field(..., description="Cantidad de autores.")
    affiliation_count: int = Field(..., description="Cantidad de afiliaciones.")
    corpus: str | None = Field(
        default=None, description="Corpus del que proviene el artículo."
    )
    affiliations: list[str] | None = Field(
        default=None, description="Afiliaciones de los autores."
    )
    topics: list[str] | None = Field(default=None, description="Tópicos del artículo.")
    scopus_id: str = Field(..., description="ID del artículo en Scopus.")
    authors: list[ArticleAuthorItem] | None = Field(
        default=None, description="Autores del artículo."
    )


class ArticlesByAuthorItem(BaseModel):
    title: str = Field(..., description="Título del artículo.")
    publication_date: str = Field(..., description="Fecha de publicación.")
    scopus_id: str = Field(..., description="ID del artículo en Scopus.")
