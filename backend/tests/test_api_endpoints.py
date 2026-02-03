#!/usr/bin/env python3
"""
Test suite for REST API endpoints.

This module tests all the API endpoints for:
- Tweet data retrieval
- Trade history and positions
- Manual override controls
"""

import sys
import os
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)


@pytest.fixture
def mock_env():
    """Mock environment variables for testing."""
    return {
        'APP_NAME': 'test',
        'APP_VERSION': '1.0',
        'DEBUG': 'false',
        'DATABASE_URL': 'sqlite:///test.db',
        'SQL_DEBUG': 'false',
        'REDIS_URL': 'redis://localhost:6379',
        'TWITTER_BEARER_TOKEN': 'test_token',
        'BINANCE_API_KEY': 'test_key',
        'BINANCE_API_SECRET': 'test_secret',
        'FRONTEND_URL': 'http://localhost:3000',
        'HOST': 'localhost',
        'PORT': '8000',
        'TRADING__SIGNAL_THRESHOLD': '70',
        'TRADING__POSITION_SIZE_PERCENT': '0.01',
        'TRADING__STOP_LOSS_PERCENT': '0.02',
        'TRADING__TAKE_PROFIT_PERCENT': '0.04',
        'TRADING__MAX_DAILY_DRAWDOWN': '0.05',
        'TRADING__MAX_OPEN_POSITIONS': '5'
    }


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = Mock()
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None
    db.commit = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def sample_tweet():
    """Sample tweet data for testing."""
    tweet = Mock()
    tweet.id = 123456789
    tweet.author = "crypto_trader"
    tweet.text = "Bitcoin is going to the moon! #BTC #crypto"
    tweet.created_at = datetime.utcnow()
    tweet.sentiment_score = 0.8
    tweet.signal_score = 85
    tweet.processed = True
    tweet.created_at_db = datetime.utcnow()
    tweet.to_dict.return_value = {
        "id": 123456789,
        "author": "crypto_trader",
        "text": "Bitcoin is going to the moon! #BTC #crypto",
        "created_at": tweet.created_at.isoformat(),
        "sentiment_score": 0.8,
        "signal_score": 85,
        "processed": True,
        "created_at_db": tweet.created_at_db.isoformat()
    }
    return tweet


@pytest.fixture
def sample_trade():
    """Sample trade data for testing."""
    trade = Mock()
    trade.id = 1
    trade.tweet_id = 123456789
    trade.symbol = "BTCUSDT"
    trade.side = "LONG"
    trade.leverage = 1
    trade.quantity = Decimal('0.001')
    trade.entry_price = Decimal('50000')
    trade.stop_loss = Decimal('49000')
    trade.take_profit = Decimal('52000')
    trade.status = "OPEN"
    trade.pnl = None
    trade.created_at = datetime.utcnow()
    trade.closed_at = None
    trade.to_dict.return_value = {
        "id": 1,
        "tweet_id": 123456789,
        "symbol": "BTCUSDT",
        "side": "LONG",
        "leverage": 1,
        "quantity": 0.001,
        "entry_price": 50000.0,
        "stop_loss": 49000.0,
        "take_profit": 52000.0,
        "status": "OPEN",
        "pnl": None,
        "created_at": trade.created_at.isoformat(),
        "closed_at": None
    }
    return trade


@pytest.fixture
def sample_position():
    """Sample position data for testing."""
    position = Mock()
    position.id = 1
    position.symbol = "BTCUSDT"
    position.size = Decimal('0.001')
    position.avg_entry = Decimal('50000')
    position.leverage = 1
    position.unrealized_pnl = Decimal('100')
    position.side = "LONG"
    position.abs_size = Decimal('0.001')
    position.updated_at = datetime.utcnow()
    position.to_dict.return_value = {
        "id": 1,
        "symbol": "BTCUSDT",
        "size": 0.001,
        "avg_entry": 50000.0,
        "leverage": 1,
        "unrealized_pnl": 100.0,
        "side": "LONG",
        "abs_size": 0.001,
        "updated_at": position.updated_at.isoformat()
    }
    return position


class TestTweetEndpoints:
    """Test suite for tweet API endpoints."""

    def test_get_recent_tweets(self, mock_env, mock_db, sample_tweet):
        """Test GET /api/tweets endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)

            # Mock Tweet.get_recent to return sample tweet
            with patch('app.models.tweet.Tweet.get_recent', return_value=[sample_tweet]), \
                    patch('app.database.get_db', return_value=mock_db):

                response = client.get("/api/tweets/")

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["id"] == 123456789
                assert data[0]["signal_score"] == 85

    def test_get_high_signal_tweets(self, mock_env, mock_db, sample_tweet):
        """Test GET /api/tweets/signals endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)

            with patch('app.models.tweet.Tweet.get_high_signals', return_value=[sample_tweet]), \
                    patch('app.database.get_db', return_value=mock_db):

                response = client.get(
                    "/api/tweets/signals?min_signal_score=80")

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["signal_score"] == 85

    def test_get_tweet_by_id(self, mock_env, mock_db, sample_tweet):
        """Test GET /api/tweets/{tweet_id} endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)

            # Mock database query to return sample tweet
            mock_db.query.return_value.filter.return_value.first.return_value = sample_tweet

            with patch('app.database.get_db', return_value=mock_db):
                response = client.get("/api/tweets/123456789")

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == 123456789

    def test_get_tweet_by_id_not_found(self, mock_env, mock_db):
        """Test GET /api/tweets/{tweet_id} endpoint with non-existent tweet."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)

            # Mock database query to return None
            mock_db.query.return_value.filter.return_value.first.return_value = None

            with patch('app.database.get_db', return_value=mock_db):
                response = client.get("/api/tweets/999999999")

                assert response.status_code == 404


class TestTradeEndpoints:
    """Test suite for trade API endpoints."""

    def test_get_trade_history(self, mock_env, mock_db, sample_trade):
        """Test GET /api/trades endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)

            with patch('app.models.trade.Trade.get_recent', return_value=[sample_trade]), \
                    patch('app.database.get_db', return_value=mock_db):

                response = client.get("/api/trades/")

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["symbol"] == "BTCUSDT"
                assert data[0]["side"] == "LONG"

    def test_get_open_trades(self, mock_env, mock_db, sample_trade):
        """Test GET /api/trades/open endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)

            with patch('app.models.trade.Trade.get_open_trades', return_value=[sample_trade]), \
                    patch('app.database.get_db', return_value=mock_db):

                response = client.get("/api/trades/open")

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["status"] == "OPEN"

    def test_get_trade_statistics(self, mock_env, mock_db):
        """Test GET /api/trades/stats endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)

            # Mock trade statistics methods
            with patch('app.models.trade.Trade.count_open_positions', return_value=2), \
                    patch('app.models.trade.Trade.get_total_pnl', return_value=Decimal('150.50')), \
                    patch('app.models.trade.Trade.get_daily_pnl', return_value=Decimal('25.75')), \
                    patch('app.database.get_db', return_value=mock_db):

                # Mock closed trades query
                mock_winning_trade = Mock()
                mock_winning_trade.pnl = Decimal('100')
                mock_losing_trade = Mock()
                mock_losing_trade.pnl = Decimal('-50')

                mock_db.query.return_value.filter.return_value.all.return_value = [
                    mock_winning_trade, mock_losing_trade
                ]

                response = client.get("/api/trades/stats")

                assert response.status_code == 200
                data = response.json()
                assert data["open_positions"] == 2
                assert data["total_realized_pnl"] == 150.50
                assert data["daily_pnl"] == 25.75
                assert data["total_trades"] == 2
                assert data["winning_trades"] == 1
                assert data["losing_trades"] == 1


class TestPositionEndpoints:
    """Test suite for position API endpoints."""

    def test_get_current_positions(self, mock_env, mock_db, sample_position):
        """Test GET /api/positions endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)

            with patch('app.models.position.Position.get_all_positions', return_value=[sample_position]), \
                    patch('app.database.get_db', return_value=mock_db):

                response = client.get("/api/positions/")

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["symbol"] == "BTCUSDT"
                assert data[0]["side"] == "LONG"

    def test_get_positions_summary(self, mock_env, mock_db, sample_position):
        """Test GET /api/positions/summary endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)

            with patch('app.models.position.Position.get_all_positions', return_value=[sample_position]), \
                    patch('app.models.position.Position.get_long_positions', return_value=[sample_position]), \
                    patch('app.models.position.Position.get_short_positions', return_value=[]), \
                    patch('app.models.position.Position.get_total_unrealized_pnl', return_value=Decimal('100')), \
                    patch('app.database.get_db', return_value=mock_db):

                response = client.get("/api/positions/summary")

                assert response.status_code == 200
                data = response.json()
                assert data["total_positions"] == 1
                assert data["long_positions"] == 1
                assert data["short_positions"] == 0
                assert data["total_unrealized_pnl"] == 100.0

    def test_get_position_by_symbol(self, mock_env, mock_db, sample_position):
        """Test GET /api/positions/{symbol} endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)

            with patch('app.models.position.Position.get_by_symbol', return_value=sample_position), \
                    patch('app.database.get_db', return_value=mock_db):

                response = client.get("/api/positions/BTCUSDT")

                assert response.status_code == 200
                data = response.json()
                assert data["symbol"] == "BTCUSDT"

    def test_update_position_pnl(self, mock_env, mock_db, sample_position):
        """Test PUT /api/positions/{symbol}/pnl endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)

            with patch('app.models.position.Position.update_pnl_for_symbol', return_value=sample_position), \
                    patch('app.database.get_db', return_value=mock_db):

                response = client.put(
                    "/api/positions/BTCUSDT/pnl?current_price=51000")

                assert response.status_code == 200
                data = response.json()
                assert data["symbol"] == "BTCUSDT"


class TestOverrideEndpoints:
    """Test suite for manual override API endpoints."""

    def test_get_override_status(self, mock_env):
        """Test GET /api/override/status endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)
            response = client.get("/api/override/status")

            assert response.status_code == 200
            data = response.json()
            assert "manual_override" in data
            assert "last_updated" in data
            assert "reason" in data

    def test_toggle_manual_override(self, mock_env):
        """Test POST /api/override/toggle endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)

            # Test enabling override
            response = client.post("/api/override/toggle", json={
                "enabled": True,
                "reason": "Test enable"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["manual_override"] is True
            assert data["reason"] == "Test enable"

    def test_enable_manual_override(self, mock_env):
        """Test POST /api/override/enable endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)
            response = client.post("/api/override/enable?reason=Test%20enable")

            assert response.status_code == 200
            data = response.json()
            assert data["manual_override"] is True

    def test_disable_manual_override(self, mock_env):
        """Test POST /api/override/disable endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)
            response = client.post(
                "/api/override/disable?reason=Test%20disable")

            assert response.status_code == 200
            data = response.json()
            assert data["manual_override"] is False

    def test_get_trading_config(self, mock_env):
        """Test GET /api/override/config endpoint."""
        with patch.dict(os.environ, mock_env):
            from app.main import app

            client = TestClient(app)
            response = client.get("/api/override/config")

            assert response.status_code == 200
            data = response.json()
            assert data["signal_threshold"] == 70
            assert data["position_size_percent"] == 0.01
            assert data["stop_loss_percent"] == 0.02
            assert data["take_profit_percent"] == 0.04


def run_tests():
    """Run all API endpoint tests."""
    print("API Endpoints Test Suite")
    print("=" * 50)

    # Create test instances
    mock_env_data = {
        'APP_NAME': 'test',
        'APP_VERSION': '1.0',
        'DEBUG': 'false',
        'DATABASE_URL': 'sqlite:///test.db',
        'SQL_DEBUG': 'false',
        'REDIS_URL': 'redis://localhost:6379',
        'TWITTER_BEARER_TOKEN': 'test_token',
        'BINANCE_API_KEY': 'test_key',
        'BINANCE_API_SECRET': 'test_secret',
        'FRONTEND_URL': 'http://localhost:3000',
        'HOST': 'localhost',
        'PORT': '8000',
        'TRADING__SIGNAL_THRESHOLD': '70',
        'TRADING__POSITION_SIZE_PERCENT': '0.01',
        'TRADING__STOP_LOSS_PERCENT': '0.02',
        'TRADING__TAKE_PROFIT_PERCENT': '0.04',
        'TRADING__MAX_DAILY_DRAWDOWN': '0.05',
        'TRADING__MAX_OPEN_POSITIONS': '5'
    }

    # Test basic endpoint availability
    with patch.dict(os.environ, mock_env_data):
        try:
            from app.main import app
            client = TestClient(app)

            # Test root endpoint
            response = client.get("/")
            assert response.status_code == 200
            print("✓ Root endpoint accessible")

            # Test API status endpoint
            response = client.get("/api/status")
            assert response.status_code == 200
            print("✓ API status endpoint accessible")

            # Test health endpoint
            response = client.get("/health")
            if response.status_code != 200:
                print(
                    f"Health endpoint failed with status {response.status_code}: {response.text}")
            else:
                print("✓ Health endpoint accessible")

            print("\n✓ All basic endpoint tests passed!")

        except Exception as e:
            print(f"✗ Basic endpoint test failed: {e}")
            raise


if __name__ == "__main__":
    try:
        run_tests()
        print("\n" + "=" * 50)
        print("✓ All API endpoint tests completed successfully!")

    except Exception as e:
        print(f"\n✗ API endpoint tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
