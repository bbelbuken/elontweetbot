"""
Configuration management for the trading bot application.

This module handles environment variables and application settings.
"""

import os
from typing import List
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class TradingConfig(BaseModel):
    """Trading-specific configuration parameters."""
    signal_threshold: int = Field(ge=0, le=100, description="Minimum signal score to trigger trade (0-100)")
    position_size_percent: float = Field(gt=0, le=0.1, description="Position size as % of balance (0-0.1)")
    stop_loss_percent: float = Field(gt=0, le=0.2, description="Stop loss as % of entry price (0-0.2)")
    take_profit_percent: float = Field(gt=0, le=1.0, description="Take profit as % of entry price (0-1.0)")
    max_daily_drawdown: float = Field(gt=0, le=0.5, description="Max daily loss as % of balance (0-0.5)")
    max_open_positions: int = Field(ge=1, le=20, description="Maximum number of open positions (1-20)")
    manual_override: bool = False

    @field_validator('signal_threshold')
    @classmethod
    def validate_signal_threshold(cls, v):
        """Ensure signal threshold is reasonable."""
        if v < 50:
            print(f"⚠️  Warning: Signal threshold {v} is very low. Recommended: 70+")
        return v

    @field_validator('position_size_percent')
    @classmethod
    def validate_position_size(cls, v):
        """Ensure position size is reasonable."""
        if v > 0.05:
            print(f"⚠️  Warning: Position size {v*100}% is high. Recommended: 1-2%")
        return v


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    app_name: str = "Trading Bot"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database settings
    database_url: str = Field(description="PostgreSQL connection string")
    sql_debug: bool = False

    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379/0")

    # API credentials
    twitter_bearer_token: str = Field(description="Twitter API Bearer Token")
    binance_api_key: str = Field(description="Binance API Key")
    binance_api_secret: str = Field(description="Binance API Secret")

    # Frontend settings
    frontend_url: str = Field(default="http://localhost:3000")
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Trading configuration
    trading: TradingConfig = TradingConfig(
        signal_threshold=int(os.getenv("SIGNAL_THRESHOLD", "70")),
        position_size_percent=float(os.getenv("POSITION_SIZE_PERCENT", "0.01")),
        stop_loss_percent=float(os.getenv("STOP_LOSS_PERCENT", "0.02")),
        take_profit_percent=float(os.getenv("TAKE_PROFIT_PERCENT", "0.04")),
        max_daily_drawdown=float(os.getenv("MAX_DAILY_DRAWDOWN", "0.05")),
        max_open_positions=int(os.getenv("MAX_OPEN_POSITIONS", "5")),
        manual_override=os.getenv("MANUAL_OVERRIDE", "false").lower() == "true"
    )

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"

    def validate_config(self):
        """Validate configuration and print warnings."""
        print("\n" + "="*50)
        print("⚙️  Configuration Loaded")
        print("="*50)
        
        # Check for placeholder API keys
        if "your_" in self.twitter_bearer_token.lower():
            print("❌ Twitter API token not configured!")
            print("   Get it from: https://developer.twitter.com/")
            
        if "your_" in self.binance_api_key.lower():
            print("❌ Binance API key not configured!")
            print("   Get it from: https://testnet.binance.vision/")
        
        # Print trading config
        print(f"\n📊 Trading Config:")
        print(f"   Signal Threshold: {self.trading.signal_threshold}")
        print(f"   Position Size: {self.trading.position_size_percent*100}%")
        print(f"   Stop Loss: {self.trading.stop_loss_percent*100}%")
        print(f"   Take Profit: {self.trading.take_profit_percent*100}%")
        print(f"   Max Daily Drawdown: {self.trading.max_daily_drawdown*100}%")
        print(f"   Max Open Positions: {self.trading.max_open_positions}")
        print(f"   Manual Override: {'✓ Enabled' if self.trading.manual_override else '✗ Disabled'}")
        
        print("="*50 + "\n")
        
        return True


# Global settings instance
settings = Settings()

# Auto-validate on load
try:
    settings.validate_config()
except Exception as e:
    print(f"⚠️  Configuration validation warning: {e}")

