"""Helper de capa API: traduce la invariante del agregado Consulta a HTTP 422.

Mantiene el dominio puro (value_objects no conoce FastAPI) y evita repetir el
bloque de validacion en cada endpoint que recibe una consulta de busqueda.
"""
from fastapi.responses import JSONResponse

from app.domain.value_objects import SearchQuery, ContractValidationError
from app.schemas.search import ErrorDetail, ErrorResponse


def validate_query(raw, trace_id):
    """Valida el texto de la consulta contra las invariantes del agregado Consulta.

    Retorna (search_query, None) si es valida, o (None, JSONResponse 422) si
    viola una regla de contrato (CONTRACT_VALIDATION).
    """
    try:
        return SearchQuery(raw), None
    except ContractValidationError as e:
        error = JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=ErrorDetail(code="CONTRACT_VALIDATION", message=e.message, details=e.details),
                trace_id=trace_id,
            ).model_dump(),
        )
        return None, error
