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
from app.schemas.search import ERROR_RESPONSES


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await http_client.aclose()


app = FastAPI(
    title="Centinela Search MS",
    description="API intermediaria v2 — Strangler Pattern sobre v1",
    version="2.0.0",
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
app.include_router(search.router, prefix="/api-se/v2", responses=ERROR_RESPONSES)
app.include_router(authors.router, prefix="/api-se/v2", responses=ERROR_RESPONSES)
app.include_router(articles.router, prefix="/api-se/v2", responses=ERROR_RESPONSES)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


def custom_openapi():
    """Recorta el prefijo interno del spec y fija la ruta publica detras del
    gateway (nginx.conf: /api/search/v2/ -> /api-se/v2/), para que "Try it out"
    en Swagger UI pegue a la URL real."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    prefix = "/api-se/v2"
    schema["paths"] = {
        (path[len(prefix) :] if path.startswith(prefix) else path): item
        for path, item in schema.get("paths", {}).items()
    }
    schema["servers"] = [{"url": "/api/search/v2", "description": "Gateway"}]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
