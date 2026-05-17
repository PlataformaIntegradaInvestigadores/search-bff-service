from fastapi import FastAPI
from fastapi import Request
import uuid
from fastapi.exceptions import RequestValidationError
from app.api.v2 import search
from app.core.exceptions import validation_exception_handler

app = FastAPI(
    title="Centinela Search MS",
    description="API intermediaria v2 — Strangler Pattern sobre v1",
    version="2.0.0"
)

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response

app.include_router(search.router, prefix="/api-se/v2")
app.add_exception_handler(RequestValidationError, validation_exception_handler)