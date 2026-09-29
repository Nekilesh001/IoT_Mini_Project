"""
Main FastAPI Application for Smart Factory Machine Monitoring & Predictive Maintenance.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import APIConfig
from api.dependencies import get_api_config, get_db_engine
from api.routes import health, factory, machines, telemetry, realtime, alerts, scenarios, ml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("smart_factory.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_api_config()
    logger.info("Initializing Smart Factory FastAPI Backend...")
    try:
        engine = get_db_engine()
        logger.info(f"Connected to database: {cfg.database_url.split('@')[-1]}")
    except Exception as e:
        logger.warning(f"Database pre-initialization notice: {e}")
    yield
    logger.info("Shutting down Smart Factory FastAPI Backend...")


def create_app() -> FastAPI:
    cfg = get_api_config()
    app = FastAPI(
        title="Smart Factory Machine Monitoring API",
        description="REST and Realtime APIs for 12 heterogeneous industrial machines, multi-protocol telemetry, operational state, and predictive maintenance ML inference.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # CORS configuration for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Generic global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error processing {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error occurred while processing the request."}
        )

    # Mount Route modules
    app.include_router(health.router)
    app.include_router(factory.router)
    app.include_router(machines.router)
    app.include_router(telemetry.router)
    app.include_router(realtime.router)
    app.include_router(alerts.router)
    app.include_router(scenarios.router)
    app.include_router(scenarios.demo_router)
    app.include_router(ml.router)

    return app


app = create_app()
