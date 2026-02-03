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
    manual_override: bool = False


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
    trading: TradingConfig = TradingConfig(
        signal_threshold=int(os.getenv("SIGNAL_THRESHOLD", "70")),
        position_size_percent=float(
            os.getenv("POSITION_SIZE_PERCENT", "0.01")),
        stop_loss_percent=float(os.getenv("STOP_LOSS_PERCENT", "0.02")),
        take_profit_percent=float(os.getenv("TAKE_PROFIT_PERCENT", "0.04")),
        max_daily_drawdown=float(os.getenv("MAX_DAILY_DRAWDOWN", "0.05")),
        max_open_positions=int(os.getenv("MAX_OPEN_POSITIONS", "5")),
        manual_override=os.getenv("MANUAL_OVERRIDE", "false").lower() == "true"
    )

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


# Global settings instance
settings = Settings()
