from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SearchResult:
    title: str
    abstract: str
    scopus_id: str
    publication_date: Optional[str]
    relevance: float

@dataclass
class SearchQuery:
    query: str
    page: int
    page_size: int
    filter_years: Optional[List[int]] = None
    filter_type: Optional[str] = None