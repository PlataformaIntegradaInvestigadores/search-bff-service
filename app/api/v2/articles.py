import logging
import uuid
from typing import List

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.application.usecases.relevant_articles_usecase import RelevantArticlesUseCase
from app.application.usecases.article_detail_usecase import ArticleDetailUseCase
from app.application.usecases.articles_by_author_usecase import ArticlesByAuthorUseCase
from app.data.adapters.django_articles_adapter import DjangoArticlesAdapter
from app.schemas.articles import (
    ArticleDetailResponse,
    ArticlesByAuthorItem,
    RelevantArticleItem,
    RelevantArticlesRequest,
    RelevantArticlesResponse,
)
from app.schemas.search import ErrorDetail, ErrorResponse

router = APIRouter(tags=["Articles"])
logger = logging.getLogger(__name__)


def get_relevant_use_case() -> RelevantArticlesUseCase:
    return RelevantArticlesUseCase(repository=DjangoArticlesAdapter())


def get_by_author_use_case() -> ArticlesByAuthorUseCase:
    return ArticlesByAuthorUseCase(repository=DjangoArticlesAdapter())


def get_detail_use_case() -> ArticleDetailUseCase:
    return ArticleDetailUseCase(repository=DjangoArticlesAdapter())


@router.post("/articles/relevant", response_model=RelevantArticlesResponse)
async def relevant_articles(request: RelevantArticlesRequest):
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
        use_case = get_relevant_use_case()
        response = await use_case.execute(
            query=request.query,
            page=request.page,
            page_size=request.page_size,
            years=request.filters.years if request.filters else None,
        )

        raw_items = response.get("data", [])
        items = [
            RelevantArticleItem(
                title=item.get("title", ""),
                author_count=int(item.get("author_count", 0)),
                affiliation_count=int(item.get("affiliation_count", 0)),
                publication_date=item.get("publication_date", ""),
                scopus_id=str(item.get("scopus_id", "")),
                relevance=float(item.get("relevance", 0.0)),
                authors=item.get("authors"),
                affiliations=item.get("affiliations"),
            )
            for item in raw_items
        ]

        years = list(response.get("years", []))
        total = int(response.get("total", len(items)))

        return RelevantArticlesResponse(
            data=items,
            years=years,
            total=total,
            total_results=int(response.get("total", total)),
        )

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.error(f"[{trace_id}] Bridge Django no disponible: {e}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(code="DEPENDENCY_UNAVAILABLE", message="El servicio de articulos no esta disponible temporalmente."),
                trace_id=trace_id
            ).model_dump()
        )
    except httpx.HTTPStatusError as e:
        legacy_detail = ""
        try:
            legacy_detail = e.response.json().get("error", "")
        except Exception:
            legacy_detail = e.response.text

        logger.error(f"[{trace_id}] Legacy articles error: {legacy_detail}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="DEPENDENCY_UNAVAILABLE",
                    message=f"El servicio legacy de articulos fallo: {legacy_detail}",
                ),
                trace_id=trace_id
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"[{trace_id}] Relevant articles error: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(code="INTERNAL_ERROR", message=str(e)),
                trace_id=trace_id
            ).model_dump()
        )


@router.get("/articles/by-author", response_model=List[ArticlesByAuthorItem])
async def articles_by_author(author_id: str):
    trace_id = str(uuid.uuid4())

    if not author_id or not author_id.strip():
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(code="INVALID_INPUT", message="El parametro 'author_id' es obligatorio."),
                trace_id=trace_id
            ).model_dump()
        )

    try:
        use_case = get_by_author_use_case()
        response = await use_case.execute(author_id=author_id)
        items = [
            ArticlesByAuthorItem(
                title=item.get("title", ""),
                publication_date=item.get("publication_date", ""),
                scopus_id=str(item.get("scopus_id", "")),
            )
            for item in response
        ]
        return items

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.error(f"[{trace_id}] Bridge Django no disponible: {e}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(code="DEPENDENCY_UNAVAILABLE", message="El servicio de articulos no esta disponible temporalmente."),
                trace_id=trace_id
            ).model_dump()
        )
    except httpx.HTTPStatusError as e:
        legacy_detail = ""
        try:
            legacy_detail = e.response.json().get("error", "")
        except Exception:
            legacy_detail = e.response.text

        logger.error(f"[{trace_id}] Legacy articles error: {legacy_detail}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="DEPENDENCY_UNAVAILABLE",
                    message=f"El servicio legacy de articulos fallo: {legacy_detail}",
                ),
                trace_id=trace_id
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"[{trace_id}] Articles by author error: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(code="INTERNAL_ERROR", message=str(e)),
                trace_id=trace_id
            ).model_dump()
        )


@router.get("/articles/{scopus_id}", response_model=ArticleDetailResponse)
async def article_detail(scopus_id: str):
    trace_id = str(uuid.uuid4())

    def ensure_str(value) -> str:
        return "" if value is None else str(value)

    def normalize_list(values, key: str) -> List[str] | None:
        if values is None:
            return None
        normalized = []
        for item in values:
            if isinstance(item, dict):
                normalized.append(ensure_str(item.get(key, "")))
            else:
                normalized.append(ensure_str(item))
        return normalized

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

        return ArticleDetailResponse(
            title=ensure_str(response.get("title", "")),
            abstract=ensure_str(response.get("abstract", "")),
            doi=ensure_str(response.get("doi", "")),
            publication_date=ensure_str(response.get("publication_date", "")),
            author_count=int(response.get("author_count", 0)),
            affiliation_count=int(response.get("affiliation_count", 0)),
            corpus=ensure_str(response.get("corpus")) if response.get("corpus") is not None else None,
            affiliations=normalize_list(response.get("affiliations"), "name"),
            topics=normalize_list(response.get("topics"), "name"),
            scopus_id=ensure_str(response.get("scopus_id", "")),
            authors=normalize_list(response.get("authors"), "name"),
        )

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.error(f"[{trace_id}] Bridge Django no disponible: {e}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(code="DEPENDENCY_UNAVAILABLE", message="El servicio de articulos no esta disponible temporalmente."),
                trace_id=trace_id
            ).model_dump()
        )
    except httpx.HTTPStatusError as e:
        legacy_detail = ""
        try:
            legacy_detail = e.response.json().get("error", "")
        except Exception:
            legacy_detail = e.response.text

        logger.error(f"[{trace_id}] Legacy article detail error: {legacy_detail}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="DEPENDENCY_UNAVAILABLE",
                    message=f"El servicio legacy de articulos fallo: {legacy_detail}",
                ),
                trace_id=trace_id
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"[{trace_id}] Article detail error: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(code="INTERNAL_ERROR", message=str(e)),
                trace_id=trace_id
            ).model_dump()
        )
