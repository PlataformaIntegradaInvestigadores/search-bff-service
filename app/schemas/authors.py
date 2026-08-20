from typing import Any

from pydantic import BaseModel, Field


class AuthorsFilters(BaseModel):
    affiliations: list[str] | None = None
    mode: str | None = None


class AuthorsRequest(BaseModel):
    query: str = Field(..., min_length=1)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=200)
    filters: AuthorsFilters | None = None


class AuthorsSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class AuthorNode(BaseModel):
    scopus_id: str
    first_name: str
    last_name: str
    auth_name: str
    initials: str
    affiliations: list[str] = []
    articles: int = 0
    co_authors: list[str] = []
    topics: list[str] = []
    citation_count: int = 0
    current_affiliation: str | None = None


class AuthorLink(BaseModel):
    source: str
    target: str
    collabStrength: float


class AffiliationItem(BaseModel):
    scopus_id: str
    name: str


class RelevantAuthorsResponse(BaseModel):
    nodes: list[AuthorNode]
    links: list[AuthorLink]
    affiliations: list[AffiliationItem]
    total_results: int
    page: int
    page_size: int


class AuthorSearchItem(BaseModel):
    scopus_id: str
    name: str
    affiliations: int
    articles: int
    topics: int
    current_affiliation: str | None = None
    citation_count: int
    updated: bool


class AuthorsSearchResponse(BaseModel):
    total: int
    next_page: str | None = None
    previous_page: str | None = None
    data: list[AuthorSearchItem]


class AuthorProfileResponse(BaseModel):
    """Respuesta compuesta del perfil de autor (Slice 2). 'author' es el nucleo
    tipado; el resto se pasa tal cual viene de v1 (tolerante a su forma)."""

    author: AuthorNode
    topics: list[Any] = []
    coauthors: Any = None
    years: list[Any] = []
    articles: list[Any] = []
    degraded: list[str] = []
