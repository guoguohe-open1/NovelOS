from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from novelos.infrastructure.config import Settings
from novelos.infrastructure.database import create_database_engine, database_is_ready


class HealthResponse(BaseModel):
    status: Literal["ok", "ready", "not_ready"]


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings if settings is not None else Settings()
    engine = create_database_engine(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="NovelOS", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
    )

    @app.get("/health/live", response_model=HealthResponse, tags=["health"])
    def live() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get(
        "/health/ready",
        response_model=HealthResponse,
        responses={503: {"model": HealthResponse}},
        tags=["health"],
    )
    def ready() -> HealthResponse | JSONResponse:
        if database_is_ready(engine):
            return HealthResponse(status="ready")
        return JSONResponse(status_code=503, content={"status": "not_ready"})

    return app
