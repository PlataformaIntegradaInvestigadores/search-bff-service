from pydantic import BaseModel, Field


class ArticleFilters(BaseModel):
    years: list[int] | None = None


class RelevantArticlesRequest(BaseModel):
    query: str = Field(..., min_length=1)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    filters: ArticleFilters | None = None


class RelevantArticleItem(BaseModel):
    title: str
    author_count: int
    affiliation_count: int
    publication_date: str
    scopus_id: str
    relevance: float
    authors: list[str] | None = None
    affiliations: list[str] | None = None


class RelevantArticlesResponse(BaseModel):
    data: list[RelevantArticleItem]
    years: list[int | str] = []
    total: int
    total_results: int | None = None


class ArticleAuthorItem(BaseModel):
    name: str
    scopus_id: str | None = None


class ArticleDetailResponse(BaseModel):
    title: str
    abstract: str
    doi: str
    publication_date: str
    author_count: int
    affiliation_count: int
    corpus: str | None = None
    affiliations: list[str] | None = None
    topics: list[str] | None = None
    scopus_id: str
    authors: list[ArticleAuthorItem] | None = None


class ArticlesByAuthorItem(BaseModel):
    title: str
    publication_date: str
    scopus_id: str
