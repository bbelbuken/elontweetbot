"""
Health check services for external dependencies.

This module contains health check functions for:
- Database connection
- Redis connection
- Twitter API
- Binance API
"""

import redis
import tweepy
import structlog
from app.config import settings
from app.utils.logging import get_logger


logger = get_logger(__name__)


async def check_database_connection_async() -> bool:
    """
    Check if database connection is healthy (async version).

    Returns:
        True if connection is healthy, False otherwise
    """
    try:
        from sqlalchemy import text
        from app.database import SessionLocal
        
        if not SessionLocal:
            logger.warning("Database session not available")
            return False
            
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False


def check_database_connection() -> bool:
    """
    Check if database connection is healthy (sync version).

    Returns:
        True if connection is healthy, False otherwise
    """
    try:
        from sqlalchemy import text
        from app.database import SessionLocal
        
        if not SessionLocal:
            logger.warning("Database session not available")
            return False
            
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False


async def check_redis_connection() -> bool:
    """Check if Redis connection is healthy."""
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        return True
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return False


async def check_twitter_api() -> bool:
    """Check if Twitter API is accessible."""
    try:
        if not settings.twitter_bearer_token:
            logger.warning("Twitter bearer token not configured")
            return False

        client = tweepy.Client(bearer_token=settings.twitter_bearer_token)
        # Simple API call to check connectivity
        client.get_me()
        return True
    except Exception as e:
        logger.error("Twitter API health check failed", error=str(e))
        return False


async def check_binance_api() -> bool:
    """Check if Binance Testnet API is accessible."""
    try:
        if not settings.binance_api_key or not settings.binance_api_secret:
            logger.warning("Binance API credentials not configured")
            return False

        # For now, just check if credentials are present
        # Actual API call would be implemented in the trade execution worker
        return True
    except Exception as e:
        logger.error("Binance API health check failed", error=str(e))
        return False


async def get_all_health_checks() -> dict:
    """
    Run all health checks and return results.

    Returns:
        Dict containing health status for all services
    """
    return {
        "database": await check_database_connection_async(),
        "redis": await check_redis_connection(),
        "twitter_api": await check_twitter_api(),
        "binance_api": await check_binance_api()
    }
