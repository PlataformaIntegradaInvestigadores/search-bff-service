import uuid
import logging
import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.schemas.search import (
    SearchRequest, SearchResponse, ArticleResult,
    ErrorResponse, ErrorDetail
)
from app.application.usecase import SemanticSearchUseCase
from app.data.django_adapter import DjangoSearchAdapter
from app.core.config import settings

router = APIRouter(tags=["Search"])
logger = logging.getLogger(__name__)

def get_use_case() -> SemanticSearchUseCase:
    return SemanticSearchUseCase(repository=DjangoSearchAdapter())


@router.post("/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    trace_id = str(uuid.uuid4())
    
    if not request.query or not request.query.strip():
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(code="INVALID_INPUT", message="El campo 'query' es obligatorio y no puede estar vacio."),
                trace_id=trace_id
            ).model_dump()
        )

    try:
        use_case = get_use_case()
        results, elapsed_ms, total_count = await use_case.execute(
            query=request.query,
            page=request.page,
            page_size=request.page_size,
            filter_years=request.filters.years if request.filters else None,
            filter_type=request.filters.type if request.filters else None
        )

        years = list(set(
            r.publication_date.split("-")[0]
            for r in results if r.publication_date
        ))

        return SearchResponse(
            data=[ArticleResult(**r.__dict__) for r in results],
            years=sorted(years, reverse=True),
            total=len(results),
            query_time_ms=round(elapsed_ms, 2),
            total_results=total_count,
            search_type="semantic"
        )

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.error(f"[{trace_id}] Bridge Django no disponible: {e}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(code="DEPENDENCY_UNAVAILABLE", message="El servicio de busqueda no esta disponible temporalmente."),
                trace_id=trace_id
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"[{trace_id}] Search error: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(code="INTERNAL_ERROR", message=str(e)),
                trace_id=trace_id
            ).model_dump()
        )


@router.get("/search/filters")
async def get_filters():
    return {"years": list(range(2018, 2027)), "types": ["article", "review"]}


@router.get("/health")
async def health():
    trace_id = str(uuid.uuid4())
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(settings.BASE_URL + "/api-se/v1/llm-search/semantic-search/")
            if response.status_code < 500:
                return {"status": "healthy", "version": "2.0.0"}
    except (httpx.ConnectError, httpx.TimeoutException):
        pass

    return JSONResponse(
        status_code=503,
        content=ErrorResponse(
            error=ErrorDetail(code="DEPENDENCY_UNAVAILABLE", message="El bridge Django no responde."),
            trace_id=trace_id
        ).model_dump()
    )