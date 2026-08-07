"""AI Interview Agent — FastAPI application entry point.

Run locally::

    uvicorn main:app --reload --port 8000

The application loads the three datasets (curriculum.json, candidate.json,
technical-spec.md) at startup, never modifying them.  If a dataset is
missing the server still boots and reports the problem via /api/health and
clear error payloads on /api/interview.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.deps import Container
from api.routes import router
from config import settings
from utils.errors import AppError
from utils.logging import configure_logging, get_logger

configure_logging(settings)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup: build the container, load datasets, wire state."""
    container = Container(settings)
    container.load_datasets()
    app.state.services = container.as_dict()
    logger.info(
        "Startup complete — curriculum days=%d candidates=%d spec=%s llm=%s",
        container.curriculum_retriever.day_count,
        len(container.candidate_loader.all()),
        container.spec_loader.is_available,
        "configured" if container.llm.configured else "NOT configured",
    )
    yield
    await container.shutdown()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Conversational AI interviewer driven by curriculum.json, "
        "candidate.json and technical-spec.md."
    ),
    lifespan=lifespan,
)

# --- CORS (enabled per requirements) ---------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# --- exception handlers -----------------------------------------------------

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Map domain errors to proper HTTP codes with a uniform payload."""
    logger.warning("%s: %s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.to_payload()},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a clean 400 for malformed request bodies."""
    logger.info("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=400,
        content={
            "detail": {
                "code": "malformed_request",
                "message": "The request body failed validation.",
                "detail": jsonable_encoder(exc.errors()),
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all 500 handler with a safe payload (no internals leaked)."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "code": "internal_error",
                "message": "An unexpected error occurred. Please try again.",
            }
        },
    )


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "endpoints": ["/api/interview", "/api/health", "/api/candidates"],
    }


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
