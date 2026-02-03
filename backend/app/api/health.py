"""
Health check API endpoints.

This module contains all health-related endpoints:
- Comprehensive health check
- Readiness check for orchestration
- Liveness check for orchestration
"""

from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.services.health_checks import get_all_health_checks
from app.services.health_checks import check_redis_connection
from app.monitoring.metrics import api_request_duration, update_health_metrics
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
health_router = APIRouter(tags=["Health"])


def format_health_response(
    overall_status: str,
    checks: Dict[str, bool],
    app_version: str
) -> Dict[str, Any]:
    """
    Format a standardized health check response.

    Args:
        overall_status: Overall health status ("healthy" or "unhealthy")
        checks: Dictionary of service health checks
        app_version: Application version

    Returns:
        Formatted health response dictionary
    """
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks,
        "version": app_version
    }


@health_router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check endpoint for all services.

    Returns:
        Dict containing overall status and individual service checks
    """
    with api_request_duration.labels(endpoint='/health').time():
        logger.info("Health check requested")

        # Check all services
        checks = await get_all_health_checks()

        # Update Prometheus metrics
        update_health_metrics(checks)

        # Determine overall status
        overall_status = "healthy" if all(checks.values()) else "unhealthy"

        response = format_health_response(
            overall_status, checks, settings.app_version)

        if overall_status == "unhealthy":
            logger.warning("Health check failed", checks=checks)
            raise HTTPException(status_code=503, detail=response)

        logger.info("Health check passed", checks=checks)
        return response


@health_router.get("/health/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Readiness check endpoint for Kubernetes/container orchestration.

    Returns:
        Simple ready status
    """
    with api_request_duration.labels(endpoint='/health/ready').time():
        # Check critical services only (database and redis)
        from app.services.health_checks import check_database_connection_async
        db_healthy = await check_database_connection_async()
        redis_healthy = await check_redis_connection()

        if db_healthy and redis_healthy:
            return {"status": "ready"}
        else:
            raise HTTPException(status_code=503, detail={
                                "status": "not ready"})


@health_router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint for Kubernetes/container orchestration.

    Returns:
        Simple alive status
    """
    with api_request_duration.labels(endpoint='/health/live').time():
        return {"status": "alive"}
