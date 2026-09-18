import uuid

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "INVALID_INPUT",
                "message": str(exc.errors()[0]["msg"]),
                "details": exc.errors(),
            },
            "trace_id": str(uuid.uuid4()),
        },
    )
