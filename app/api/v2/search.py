import uuid
import logging
import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.schemas.search import (
    SearchRequest, SearchResponse, ArticleResult,
    ErrorResponse, ErrorDetail
)
from app.application.usecases.usecase import SemanticSearchUseCase
from app.data.adapters.django_adapter import DjangoSearchAdapter
from app.api.v2._validation import validate_query
from app.core.config import settings
from app.core.resilience import resilient_get
from app.core.cache import (
    articles_cache,
    authors_search_cache,
    authors_relevant_cache,
    article_detail_cache,
    articles_by_author_cache,
    author_detail_cache,
    filters_cache,
)

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

    # Slice 1: el agregado Consulta hace cumplir sus invariantes de contrato (HTTP 422)
    # antes de delegar al bridge v1. v2 es dueno de esta validacion; v1 no la tiene.
    search_query, contract_error = validate_query(request.query, trace_id)
    if contract_error:
        return contract_error

    try:
        use_case = get_use_case()
        results, elapsed_ms, total_count = await use_case.execute(
            query=search_query.value,
            page=request.page,
            page_size=request.page_size,
            filter_years=request.filters.years if request.filters else None
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
    # Slice 3-A: facetas de anio DINAMICAS. v2 calcula los anios realmente presentes
    # en los datos (via v1 get_last_years) en vez de una lista estatica que ofrecia
    # anios sin articulos (p.ej. 2018). Cacheado; con fallback estatico si v1 no
    # responde (degradacion elegante, ver Slice 3-B).
    cached = filters_cache.get("years")
    if cached is not None:
        return {"years": cached}

    static_fallback = list(range(2019, 2027))
    try:
        url = f"{settings.BASE_URL.rstrip('/')}/api-se/v1/dashboard/country/get_last_years/"
        response = await resilient_get(url)
        response.raise_for_status()
        data = response.json()
        years = sorted({
            int(item["year"])
            for item in data
            if isinstance(item, dict)
            and item.get("year") is not None
            and int(item.get("article", 0)) > 0
        })
        if not years:
            years = static_fallback
    except Exception as e:
        logger.warning(f"[search/filters] no se pudieron calcular anios reales; fallback estatico: {e}")
        years = static_fallback

    filters_cache["years"] = years
    return {"years": years}


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


@router.get("/cache/stats")
async def cache_stats():
    def get_stats(cache_instance):
        return {
            "current_size": len(cache_instance),
            "max_size": cache_instance.maxsize,
            "ttl": cache_instance.ttl,
            "hits": getattr(cache_instance, "hits", 0),
            "misses": getattr(cache_instance, "misses", 0)
        }

    return {
        "articles": get_stats(articles_cache),
        "authors_search": get_stats(authors_search_cache),
        "authors_relevant": get_stats(authors_relevant_cache),
        "article_detail": get_stats(article_detail_cache),
        "articles_by_author": get_stats(articles_by_author_cache),
        "author_detail": get_stats(author_detail_cache),
    }