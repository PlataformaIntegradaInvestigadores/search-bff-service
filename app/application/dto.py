from dataclasses import dataclass


@dataclass
class SearchResultDTO:
    title: str
    abstract: str
    scopus_id: str
    publication_date: str | None
    relevance: float
