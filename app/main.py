import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.v2 import articles, authors, search
from app.core.exceptions import validation_exception_handler
from app.core.http_client import http_client

# INFO para ver CACHE HIT/MISS y el fallback TF-IDF → semantic en docker logs.
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await http_client.aclose()


API_DESCRIPTION = """
API de **búsqueda de la plataforma Centinela** sobre el corpus científico de Scopus.
Es una capa intermedia (v2) que valida las consultas, normaliza las respuestas del
servicio de búsqueda (v1) y compone en una sola llamada lo que antes eran varias.

### Qué ofrece

* **Búsqueda**: búsqueda semántica de artículos y los años disponibles como filtro.
* **Autores**: búsqueda por nombre, autores relevantes para una consulta (como red de
  colaboración) y perfil completo de un autor.
* **Artículos**: artículos relevantes, detalle de un artículo y artículos de un autor.

### Errores

Todos los errores usan el mismo formato: `{"error": {"code", "message", "details"},
"trace_id"}`. El `trace_id` también viaja en la cabecera `X-Trace-ID`.

* `400`: la petición es inválida o falta un campo obligatorio.
* `404`: el recurso pedido no existe (solo en el detalle de un artículo).
* `422`: la consulta incumple una regla del contrato.
* `500`: error interno inesperado; el mensaje es genérico y el `trace_id` permite
  encontrar la causa en los logs.
* `503`: el servicio de búsqueda (v1) no está disponible.

Detrás del gateway todas las rutas cuelgan de `/api/search/v2`.
"""

OPENAPI_TAGS = [
    {
        "name": "Búsqueda",
        "description": "Búsqueda semántica de artículos y filtros disponibles.",
    },
    {
        "name": "Autores",
        "description": "Búsqueda de autores, red de autores relevantes y perfiles.",
    },
    {
        "name": "Artículos",
        "description": "Artículos relevantes, detalle y artículos por autor.",
    },
    {
        "name": "Operación",
        "description": "Diagnóstico del servicio; no forma parte del flujo de usuario.",
    },
]

app = FastAPI(
    title="Centinela Search: búsqueda de artículos y autores",
    summary="Búsqueda semántica sobre el corpus científico de Scopus.",
    description=API_DESCRIPTION,
    version="2.0.0",
    openapi_tags=OPENAPI_TAGS,
    generate_unique_id_function=lambda route: route.name,
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8082",
        "http://host.docker.internal:8082",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response


app.include_router(search.health_router)
app.include_router(search.router, prefix="/api-se/v2")
app.include_router(search.ops_router, prefix="/api-se/v2")
app.include_router(authors.router, prefix="/api-se/v2")
app.include_router(articles.router, prefix="/api-se/v2")
app.add_exception_handler(RequestValidationError, validation_exception_handler)


_DEFAULT_RESPONSE_TEXT = {
    "Successful Response": "Respuesta exitosa.",
    "Validation Error": "Error de validación en los parámetros o el cuerpo de la "
    "petición.",
}


def _localize(schema: dict) -> None:
    """Traduce los textos por defecto de FastAPI y quita los `title`
    autogenerados de propiedades y parámetros (repiten el nombre del campo)."""
    for item in schema.get("paths", {}).values():
        for operation in item.values():
            responses = operation.get("responses", {})
            # validation_exception_handler convierte los errores de FastAPI en 400
            # con ErrorResponse; el 422 autogenerado nunca se devuelve.
            default_422 = responses.get("422", {}).get("content", {})
            if "HTTPValidationError" in str(default_422):
                responses.pop("422")
            for response in responses.values():
                text = response.get("description")
                response["description"] = _DEFAULT_RESPONSE_TEXT.get(text, text)
                for media in response.get("content", {}).values():
                    media.get("schema", {}).pop("title", None)
            for parameter in operation.get("parameters", []):
                parameter.get("schema", {}).pop("title", None)
    schemas = schema.get("components", {}).get("schemas", {})
    for unused in ("HTTPValidationError", "ValidationError"):
        schemas.pop(unused, None)
    for definition in schemas.values():
        for prop in definition.get("properties", {}).values():
            prop.pop("title", None)


def custom_openapi():
    """Recorta el prefijo interno del spec y fija la ruta publica detras del
    gateway (nginx.conf: /api/search/v2/ -> /api-se/v2/), para que "Try it out"
    en Swagger UI pegue a la URL real."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        summary=app.summary,
        description=app.description,
        tags=app.openapi_tags,
        routes=app.routes,
    )
    prefix = "/api-se/v2"
    schema["paths"] = {
        (path[len(prefix) :] if path.startswith(prefix) else path): item
        for path, item in schema.get("paths", {}).items()
    }
    schema["servers"] = [{"url": "/api/search/v2", "description": "Gateway"}]
    _localize(schema)
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
