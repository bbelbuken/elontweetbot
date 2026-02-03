"""
Configuration management for the trading bot application.

This module handles environment variables and application settings.
"""

import os
from typing import List
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class TradingConfig(BaseModel):
    """Trading-specific configuration parameters."""
    signal_threshold: int
    position_size_percent: float
    stop_loss_percent: float
    take_profit_percent: float
    max_daily_drawdown: float
    max_open_positions: int


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    app_name: str
    app_version: str
    debug: bool

    # Database settings
    database_url: str
    sql_debug: bool

    # Redis settings
    redis_url: str

    # API credentials
    twitter_bearer_token: str
    binance_api_key: str
    binance_api_secret: str

    # Frontend settings
    frontend_url: str
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # Server settings
    host: str
    port: int

    # Trading configuration
    trading: TradingConfig

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


# Global settings instance
settings = Settings()
