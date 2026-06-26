from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import uuid
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from app.api.v2 import search
from app.api.v2 import authors
from app.api.v2 import articles
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
    lifespan=lifespan
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

app.include_router(search.router, prefix="/api-se/v2", responses=ERROR_RESPONSES)
app.include_router(authors.router, prefix="/api-se/v2", responses=ERROR_RESPONSES)
app.include_router(articles.router, prefix="/api-se/v2", responses=ERROR_RESPONSES)
app.add_exception_handler(RequestValidationError, validation_exception_handler)