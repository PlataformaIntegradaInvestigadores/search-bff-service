from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    years: list[int] | None = Field(
        default=None,
        description="Limita los resultados a artículos de estos años.",
        examples=[[2023, 2024]],
    )


class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Texto de la búsqueda semántica.",
        examples=["machine learning en salud"],
    )
    page: int = Field(default=1, ge=1, description="Número de página, desde 1.")
    page_size: int = Field(
        default=10, ge=1, le=100, description="Resultados por página (máximo 100)."
    )
    filters: SearchFilters | None = Field(
        default=None, description="Filtros opcionales."
    )


class ArticleResult(BaseModel):
    title: str = Field(..., description="Título del artículo.")
    abstract: str = Field(..., description="Resumen del artículo.")
    scopus_id: str = Field(..., description="ID del artículo en Scopus.")
    publication_date: str | None = Field(
        ..., description="Fecha de publicación (`AAAA-MM-DD`), si se conoce."
    )
    relevance: float = Field(
        ..., description="Puntaje de similitud semántica con la consulta."
    )


class SearchResponse(BaseModel):
    data: list[ArticleResult] = Field(..., description="Artículos de la página.")
    years: list[str] = Field(
        ...,
        description="Años presentes en los resultados, del más reciente al "
        "más antiguo.",
    )
    total: int = Field(..., description="Cantidad de artículos en esta página.")
    query_time_ms: float = Field(..., description="Tiempo de la búsqueda, en ms.")
    total_results: int = Field(
        ..., description="Total de artículos que coinciden, sin paginar."
    )
    search_type: str = Field(
        default="semantic", description="Tipo de búsqueda realizada."
    )


class FiltersResponse(BaseModel):
    years: list[int] = Field(
        ...,
        description="Años que realmente tienen artículos; sirven de filtro en la "
        "búsqueda. Si el servicio de búsqueda no responde se devuelve una lista fija.",
        examples=[[2019, 2020, 2021, 2022, 2023, 2024]],
    )


class CacheStats(BaseModel):
    current_size: int = Field(..., description="Entradas guardadas ahora.")
    max_size: int = Field(..., description="Capacidad máxima de la caché.")
    ttl: float = Field(..., description="Vida de cada entrada, en segundos.")
    hits: int = Field(..., description="Consultas respondidas desde la caché.")
    misses: int = Field(..., description="Consultas que no estaban en la caché.")


class CacheStatsResponse(BaseModel):
    articles: CacheStats = Field(..., description="Búsqueda de artículos.")
    authors_search: CacheStats = Field(..., description="Búsqueda de autores.")
    authors_relevant: CacheStats = Field(..., description="Autores relevantes.")
    article_detail: CacheStats = Field(..., description="Detalle de artículo.")
    articles_by_author: CacheStats = Field(..., description="Artículos de un autor.")
    author_detail: CacheStats = Field(..., description="Detalle de autor.")


class ErrorDetail(BaseModel):
    code: str = Field(
        ...,
        description="Código del error: `INVALID_INPUT`, `CONTRACT_VALIDATION`, "
        "`NOT_FOUND`, `DEPENDENCY_UNAVAILABLE` o `INTERNAL_ERROR`.",
        examples=["INVALID_INPUT"],
    )
    message: str = Field(..., description="Mensaje legible del error.")
    details: list | None = Field(
        default=None, description="Detalle por campo cuando la validación falla."
    )


class ErrorResponse(BaseModel):
    error: ErrorDetail = Field(..., description="Descripción del error.")
    trace_id: str = Field(
        ...,
        description="Identificador para rastrear la petición en los logs.",
    )


# Respuestas de error reutilizables: cada endpoint declara solo las que realmente
# puede devolver (antes se aplicaban 400/422/503 a todo el router, incluso a los
# endpoints que nunca los emiten).
BAD_REQUEST = {
    400: {
        "model": ErrorResponse,
        "description": "Petición inválida: falta un campo obligatorio, está vacío o "
        "tiene un formato incorrecto.",
    }
}
CONTRACT_ERROR = {
    422: {
        "model": ErrorResponse,
        "description": "La consulta incumple una regla del contrato "
        "(`CONTRACT_VALIDATION`).",
    }
}
NOT_FOUND = {404: {"model": ErrorResponse, "description": "Artículo no encontrado."}}
UNAVAILABLE = {
    503: {
        "model": ErrorResponse,
        "description": "El servicio de búsqueda (v1) no está disponible.",
    }
}
INTERNAL_ERROR = {
    500: {"model": ErrorResponse, "description": "Error interno inesperado."}
}
