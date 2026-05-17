from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

class SearchFilters(BaseModel):
    years: Optional[List[int]] = None
    type: Optional[str] = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    filters: Optional[SearchFilters] = None

class ArticleResult(BaseModel):
    title: str
    abstract: str
    scopus_id: str
    publication_date: Optional[str]
    relevance: float

class SearchResponse(BaseModel):
    data: List[ArticleResult]
    years: List[str]
    total: int
    query_time_ms: float
    total_results: int
    search_type: str = "semantic"

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[list] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
    trace_id: str