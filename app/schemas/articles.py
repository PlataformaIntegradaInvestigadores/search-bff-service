from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any


class ArticleFilters(BaseModel):
    years: Optional[List[int]] = None


class RelevantArticlesRequest(BaseModel):
    query: str = Field(..., min_length=1)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    filters: Optional[ArticleFilters] = None


class RelevantArticleItem(BaseModel):
    title: str
    author_count: int
    affiliation_count: int
    publication_date: str
    scopus_id: str
    relevance: float
    authors: Optional[List[str]] = None
    affiliations: Optional[List[str]] = None


class RelevantArticlesResponse(BaseModel):
    data: List[RelevantArticleItem]
    years: List[Union[int, str]] = []
    total: int
    total_results: Optional[int] = None


class ArticleAuthorItem(BaseModel):
    name: str
    scopusId: Optional[str] = None


class ArticleDetailResponse(BaseModel):
    title: str
    abstract: str
    doi: str
    publication_date: str
    author_count: int
    affiliation_count: int
    corpus: Optional[str] = None
    affiliations: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    scopus_id: str
    authors: Optional[List[ArticleAuthorItem]] = None


class ArticlesByAuthorItem(BaseModel):
    title: str
    publication_date: str
    scopus_id: str
