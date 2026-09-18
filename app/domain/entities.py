from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    abstract: str
    scopus_id: str
    publication_date: str | None
    relevance: float


@dataclass
class SearchQuery:
    query: str
    page: int
    page_size: int
    filter_years: list[int] | None = None
