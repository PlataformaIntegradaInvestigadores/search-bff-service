import uuid
import logging
import httpx
from urllib.parse import urlencode
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.schemas.authors import (
    AuthorsRequest,
    AuthorsSearchRequest,
    AuthorsSearchResponse,
    AuthorSearchItem,
    AuthorNode,
    RelevantAuthorsResponse,
)
from app.schemas.search import ErrorResponse, ErrorDetail
from app.application.usecases.relevant_authors_usecase import RelevantAuthorsUseCase
from app.application.usecases.authors_search_usecase import AuthorsSearchUseCase
from app.application.usecases.author_detail_usecase import AuthorDetailUseCase
from app.data.adapters.django_authors_adapter import DjangoAuthorsAdapter
from app.api.v2._validation import validate_query

router = APIRouter(tags=["Authors"])
logger = logging.getLogger(__name__)


def get_use_case() -> RelevantAuthorsUseCase:
    return RelevantAuthorsUseCase(repository=DjangoAuthorsAdapter())


def get_search_use_case() -> AuthorsSearchUseCase:
    return AuthorsSearchUseCase(repository=DjangoAuthorsAdapter())


def build_page_url(http_request: Request, query: str, page: int, page_size: int) -> str:
    base_url = str(http_request.base_url).rstrip("/")
    next_path = "/api-se/v2/authors/search"
    params = urlencode({"query": query, "page": page, "page_size": page_size})
    return f"{base_url}{next_path}?{params}"


async def execute_search(query: str, page: int, page_size: int, http_request: Request) -> AuthorsSearchResponse:
    use_case = get_search_use_case()
    response = await use_case.execute(
        query=query,
        page=page,
        page_size=page_size,
    )

    raw_items = response.get("data", [])
    items = [
        AuthorSearchItem(
            scopus_id=str(item.get("scopus_id", "")),
            name=item.get("name", ""),
            affiliations=int(item.get("affiliations", 0)),
            articles=int(item.get("articles", 0)),
            topics=int(item.get("topics", 0)),
            current_affiliation=item.get("current_affiliation"),
            citation_count=int(item.get("citation_count", 0)),
            updated=bool(item.get("updated", False)),
        )
        for item in raw_items
    ]

    next_page = None
    if response.get("next_page"):
        next_page = build_page_url(http_request, query, page + 1, page_size)

    previous_page = None
    if response.get("previous_page") and page > 1:
        previous_page = build_page_url(http_request, query, page - 1, page_size)

    return AuthorsSearchResponse(
        total=int(response.get("total", len(items))),
        next_page=next_page,
        previous_page=previous_page,
        data=items,
    )


def get_detail_use_case() -> AuthorDetailUseCase:
    return AuthorDetailUseCase(repository=DjangoAuthorsAdapter())


@router.post("/authors/relevant", response_model=RelevantAuthorsResponse)
async def relevant_authors(request: AuthorsRequest):
    trace_id = str(uuid.uuid4())

    if not request.query or not request.query.strip():
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(code="INVALID_INPUT", message="El campo 'query' es obligatorio y no puede estar vacio."),
                trace_id=trace_id
            ).model_dump()
        )

    # Slice 1: invariantes del agregado Consulta (HTTP 422) antes de delegar a v1.
    search_query, contract_error = validate_query(request.query, trace_id)
    if contract_error:
        return contract_error

    try:
        use_case = get_use_case()
        nodes, links, affiliations, total = await use_case.execute(
            query=search_query.value,
            page=request.page,
            page_size=request.page_size,
            affiliations=request.filters.affiliations if request.filters else None,
            mode=request.filters.mode if request.filters else None,
        )

        return RelevantAuthorsResponse(
            nodes=nodes,
            links=links,
            affiliations=affiliations,
            total_results=total,
            page=request.page,
            page_size=request.page_size,
        )

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.error(f"[{trace_id}] Bridge Django no disponible: {e}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(code="DEPENDENCY_UNAVAILABLE", message="El servicio de autores no esta disponible temporalmente."),
                trace_id=trace_id
            ).model_dump()
        )
    except httpx.HTTPStatusError as e:
        legacy_detail = ""
        try:
            legacy_detail = e.response.json().get("error", "")
        except Exception:
            legacy_detail = e.response.text

        logger.error(f"[{trace_id}] Legacy authors error: {legacy_detail}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="DEPENDENCY_UNAVAILABLE",
                    message=f"El servicio legacy de autores fallo: {legacy_detail}",
                ),
                trace_id=trace_id
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"[{trace_id}] Relevant authors error: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(code="INTERNAL_ERROR", message=str(e)),
                trace_id=trace_id
            ).model_dump()
        )


@router.post("/authors/search", response_model=AuthorsSearchResponse)
async def search_authors(payload: AuthorsSearchRequest, http_request: Request):
    trace_id = str(uuid.uuid4())

    if not payload.query or not payload.query.strip():
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(code="INVALID_INPUT", message="El campo 'query' es obligatorio y no puede estar vacio."),
                trace_id=trace_id
            ).model_dump()
        )

    # Slice 1: invariantes del agregado Consulta (HTTP 422) antes de delegar a v1.
    search_query, contract_error = validate_query(payload.query, trace_id)
    if contract_error:
        return contract_error

    try:
        return await execute_search(
            query=search_query.value,
            page=payload.page,
            page_size=payload.page_size,
            http_request=http_request,
        )

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.error(f"[{trace_id}] Bridge Django no disponible: {e}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(code="DEPENDENCY_UNAVAILABLE", message="El servicio de autores no esta disponible temporalmente."),
                trace_id=trace_id
            ).model_dump()
        )
    except httpx.HTTPStatusError as e:
        legacy_detail = ""
        try:
            legacy_detail = e.response.json().get("error", "")
        except Exception:
            legacy_detail = e.response.text

        logger.error(f"[{trace_id}] Legacy authors search error: {legacy_detail}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="DEPENDENCY_UNAVAILABLE",
                    message=f"El servicio legacy de autores fallo: {legacy_detail}",
                ),
                trace_id=trace_id
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"[{trace_id}] Authors search error: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(code="INTERNAL_ERROR", message=str(e)),
                trace_id=trace_id
            ).model_dump()
        )


@router.get("/authors/search", response_model=AuthorsSearchResponse)
async def search_authors_get(query: str, page: int = 1, page_size: int = 10, http_request: Request = None):
    trace_id = str(uuid.uuid4())

    if not query or not query.strip():
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(code="INVALID_INPUT", message="El campo 'query' es obligatorio y no puede estar vacio."),
                trace_id=trace_id
            ).model_dump()
        )

    try:
        return await execute_search(
            query=query,
            page=page,
            page_size=page_size,
            http_request=http_request,
        )

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.error(f"[{trace_id}] Bridge Django no disponible: {e}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(code="DEPENDENCY_UNAVAILABLE", message="El servicio de autores no esta disponible temporalmente."),
                trace_id=trace_id
            ).model_dump()
        )
    except httpx.HTTPStatusError as e:
        legacy_detail = ""
        try:
            legacy_detail = e.response.json().get("error", "")
        except Exception:
            legacy_detail = e.response.text

        logger.error(f"[{trace_id}] Legacy authors search error: {legacy_detail}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="DEPENDENCY_UNAVAILABLE",
                    message=f"El servicio legacy de autores fallo: {legacy_detail}",
                ),
                trace_id=trace_id
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"[{trace_id}] Authors search error: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(code="INTERNAL_ERROR", message=str(e)),
                trace_id=trace_id
            ).model_dump()
        )


@router.get("/authors/{scopus_id}", response_model=AuthorNode)
async def get_author(scopus_id: str):
    trace_id = str(uuid.uuid4())

    if not scopus_id.strip():
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(code="INVALID_INPUT", message="El campo 'scopus_id' es obligatorio."),
                trace_id=trace_id
            ).model_dump()
        )

    try:
        use_case = get_detail_use_case()
        response = await use_case.execute(scopus_id=scopus_id)
        response["scopus_id"] = str(response.get("scopus_id", ""))
        return AuthorNode(**response)

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.error(f"[{trace_id}] Bridge Django no disponible: {e}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(code="DEPENDENCY_UNAVAILABLE", message="El servicio de autores no esta disponible temporalmente."),
                trace_id=trace_id
            ).model_dump()
        )
    except httpx.HTTPStatusError as e:
        legacy_detail = ""
        try:
            legacy_detail = e.response.json().get("error", "")
        except Exception:
            legacy_detail = e.response.text

        logger.error(f"[{trace_id}] Legacy author detail error: {legacy_detail}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="DEPENDENCY_UNAVAILABLE",
                    message=f"El servicio legacy de autores fallo: {legacy_detail}",
                ),
                trace_id=trace_id
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"[{trace_id}] Author detail error: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(code="INTERNAL_ERROR", message=str(e)),
                trace_id=trace_id
            ).model_dump()
        )
