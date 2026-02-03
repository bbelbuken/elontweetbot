"""
Metrics API endpoints.

This module contains all metrics-related endpoints:
- Prometheus metrics collection endpoint
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest

from app.utils.logging import get_logger

logger = get_logger(__name__)
metrics_router = APIRouter(tags=["Monitoring"])


@metrics_router.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    """
    Prometheus metrics endpoint.

    Returns:
        Prometheus-formatted metrics in text format for Prometheus scraping
    """
    logger.debug("Metrics requested")
    return generate_latest()
