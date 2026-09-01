"""FastAPI application entry point: startup, routers and error handling."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.ai.base import AiAnalysisError
from app.db import bootstrap
from app.routers import tasks
from app.services.task_service import TaskNotFoundError


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create the schema and seed it before the app starts serving."""
    bootstrap()
    yield


app = FastAPI(title="Odin Task Review API", version="0.1.0", lifespan=lifespan)
app.include_router(tasks.router)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return a predictable body for rejected input.

    The status code stays 422. That is a deliberate choice: the request is
    syntactically valid JSON whose *content* is unacceptable, which is exactly what
    422 means, and it keeps every validation failure in the API consistent rather
    than special-casing one field. FastAPI's default body is a nested array that is
    awkward to consume, so it is flattened here into a documented shape.
    """
    details: list[dict[str, Any]] = [
        {
            "field": ".".join(str(part) for part in error["loc"][1:]) or "body",
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "The request was rejected by validation.",
            "details": details,
        },
    )


@app.exception_handler(TaskNotFoundError)
async def handle_task_not_found(_request: Request, exc: TaskNotFoundError) -> JSONResponse:
    """Translate the domain error into a 404 sharing the same error envelope."""
    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "message": str(exc)},
    )


@app.exception_handler(AiAnalysisError)
async def handle_ai_analysis_error(_request: Request, exc: AiAnalysisError) -> JSONResponse:
    """Report an AI failure as 502 Bad Gateway.

    502 says an upstream dependency failed, which is what happened: the API itself
    is healthy. The message is the analyser's own caller-safe text, never the
    provider's raw error, so nothing about the key or the request leaks outward.
    """
    return JSONResponse(
        status_code=502,
        content={"error": "ai_unavailable", "message": str(exc)},
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe, used to confirm the dev server is wired up correctly."""
    return {"status": "ok"}
