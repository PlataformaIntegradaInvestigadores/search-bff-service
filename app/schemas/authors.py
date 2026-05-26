from pydantic import BaseModel, Field
from typing import List, Optional


class AuthorsFilters(BaseModel):
    affiliations: Optional[List[str]] = None
    mode: Optional[str] = None


class AuthorsRequest(BaseModel):
    query: str = Field(..., min_length=1)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=200)
    filters: Optional[AuthorsFilters] = None


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
    affiliations: List[str] = []
    articles: int = 0
    co_authors: List[str] = []
    topics: List[str] = []
    citation_count: int = 0
    current_affiliation: Optional[str] = None


class AuthorLink(BaseModel):
    source: str
    target: str
    collabStrength: float


class AffiliationItem(BaseModel):
    scopusId: str
    name: str


class RelevantAuthorsResponse(BaseModel):
    nodes: List[AuthorNode]
    links: List[AuthorLink]
    affiliations: List[AffiliationItem]
    total_results: int
    page: int
    page_size: int


class AuthorSearchItem(BaseModel):
    scopus_id: str
    name: str
    affiliations: int
    articles: int
    topics: int
    current_affiliation: Optional[str] = None
    citation_count: int
    updated: bool


class AuthorsSearchResponse(BaseModel):
    total: int
    next_page: Optional[str] = None
    previous_page: Optional[str] = None
    data: List[AuthorSearchItem]
