"""
FastAPI main application for the tweet-driven crypto trading bot.

This module sets up the FastAPI server with:
- Health check endpoints for all services
- Prometheus metrics collection
- CORS configuration for frontend integration
- Basic application configuration
"""

from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.api.health import health_router
from app.api.metrics import metrics_router
from app.config import settings
from app.utils.logging import configure_logging, get_logger
from app.monitoring.metrics import initialize_health_metrics

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting FastAPI application")

    # Initialize metrics
    initialize_health_metrics()

    yield

    # Shutdown
    logger.info("Shutting down FastAPI application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name + " API",
    description="REST API for the tweet-driven crypto trading bot",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=settings.debug
)

# CORS configuration for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins + [settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)
app.include_router(health_router)
app.include_router(metrics_router)


@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """
    Root endpoint providing basic API information.

    Returns:
        API information
    """
    return {
        "message": f"{settings.app_name} API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error("Unhandled exception",
                 error=str(exc),
                 path=request.url.path,
                 method=request.method)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    # Development server configuration
    uvicorn.run(
        app,  # Pass the app object directly instead of string reference
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
        access_log=True

    )
