#!/usr/bin/env python3
"""Database initialization script."""

import sys
from pathlib import Path

# Add the backend folder to Python path
backend_dir = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(backend_dir))

# Now import
from app.database import init_database
from app.services.health_checks import check_database_connection
import structlog
import os

logger = structlog.get_logger(__name__)

def main():
    """Initialize the database."""
    print("🔧 Initializing database...")

    # Check database connection
    print("📡 Checking database connection...")
    if not check_database_connection():
        print("❌ Database connection failed!")
        print("Make sure PostgreSQL is running and DATABASE_URL is correct.")
        sys.exit(1)

    print("✅ Database connection successful!")

    # Initialize database
    print("🏗️  Creating database tables...")
    if init_database():
        print("✅ Database initialized successfully!")
        print("📊 Tables created: tweets, trades, positions")
    else:
        print("❌ Database initialization failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
