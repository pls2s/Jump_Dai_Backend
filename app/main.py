"""FastAPI application entry point."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(title="SkillSync AI API", version="0.1.0")
app.include_router(api_router, prefix=settings.api_prefix)


@app.exception_handler(HTTPException)
async def http_error_response(_: Request, exc: HTTPException) -> JSONResponse:
    """Return route errors in the API documentation's shared error envelope."""
    if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
        error = exc.detail
    else:
        error = {"code": "HTTP_ERROR", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"success": False, "error": error})


@app.exception_handler(RequestValidationError)
async def validation_error_response(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Keep invalid frontend requests in the same error envelope as route errors."""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": jsonable_encoder(exc.errors()),
            },
        },
    )


@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    """Return a simple service status response."""
    return {"message": "SkillSync AI API", "status": "running"}
