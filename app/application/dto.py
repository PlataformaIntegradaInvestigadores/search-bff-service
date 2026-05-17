from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SearchResultDTO:
    title: str
    abstract: str
    scopus_id: str
    publication_date: Optional[str]
    relevance: float