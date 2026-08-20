from typing import Any

from app.data.normalization import normalize_affiliation
from app.domain.author_repositories import IAuthorRepository


class RelevantAuthorsUseCase:
    def __init__(self, repository: IAuthorRepository):
        self.repository = repository

    async def execute(
        self,
        query: str,
        page: int,
        page_size: int,
        affiliations: list[str] | None = None,
        mode: str | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], int]:
        authors_number = max(page * page_size, page_size)
        response = await self.repository.most_relevant_authors(
            query=query,
            authors_number=authors_number,
            affiliations=affiliations,
            mode=mode,
        )

        nodes = response.get("nodes", [])
        links = response.get("links", [])
        # ACL (Slice 3-C): traduce el camelCase 'scopusId' de v1 al
        # canonico 'scopus_id'.
        affiliations_resp = [
            normalize_affiliation(a) for a in response.get("affiliations", [])
        ]
        total = int(response.get("size_nodes", len(nodes)))

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_nodes = nodes[start_idx:end_idx]

        node_ids = {str(node.get("scopus_id")) for node in paginated_nodes}
        filtered_links = [
            link
            for link in links
            if str(link.get("source")) in node_ids
            and str(link.get("target")) in node_ids
        ]

        return paginated_nodes, filtered_links, affiliations_resp, total
