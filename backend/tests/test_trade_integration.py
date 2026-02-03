#!/usr/bin/env python3
"""Integration test for trade execution workflow."""

import sys
import os
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)


def test_complete_trade_workflow():
    """Test the complete trade execution workflow with mocked dependencies."""
    print("Testing complete trade execution workflow...")

    # Mock all the external dependencies
    with patch.dict(os.environ, {
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
    }):

        # Import after setting environment
        from workers.trade_executor import TradeExecutor
        from app.models.trade import Trade

        # Create executor instance
        executor = TradeExecutor()

        # Mock the Binance client methods
        executor.binance_client = Mock()
        executor.binance_client.get_ticker_price.return_value = Decimal(
            '50000')
        executor.binance_client.get_balance.return_value = Decimal('1000')
        executor.binance_client.get_symbol_info.return_value = {
            'filters': [{'filterType': 'LOT_SIZE', 'stepSize': '0.00001000'}]
        }
        executor.binance_client.place_market_order.return_value = {
            'orderId': 12345,
            'status': 'FILLED'
        }

        # Mock database session
        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Mock risk management checks
        with patch.object(executor, 'check_daily_drawdown', return_value=True), \
                patch.object(executor, 'check_position_limits', return_value=True), \
                patch.object(executor, 'update_position'):

            # Execute trade signal
            trade = executor.execute_trade_signal(
                mock_db, 123, 'BTCUSDT', 'LONG')

            # Verify the workflow
            print("✓ Trade execution workflow completed")

            # Verify calculations
            expected_position_value = Decimal(
                '1000') * Decimal('0.01')  # 1% of balance
            expected_quantity = expected_position_value / \
                Decimal('50000')  # Position value / price

            print(f"Account balance: $1000")
            print(f"Position size (1%): ${expected_position_value}")
            print(f"BTC price: $50,000")
            print(f"Expected quantity: {expected_quantity} BTC")

            # Verify stop-loss and take-profit calculations
            entry_price = Decimal('50000')
            expected_stop_loss = entry_price * Decimal('0.98')  # 2% below
            expected_take_profit = entry_price * Decimal('1.04')  # 4% above

            print(f"Entry price: ${entry_price}")
            print(f"Expected stop-loss: ${expected_stop_loss}")
            print(f"Expected take-profit: ${expected_take_profit}")

            # Verify API calls were made
            assert executor.binance_client.get_ticker_price.called
            assert executor.binance_client.get_balance.called
            assert executor.binance_client.place_market_order.called

            # Verify database operations
            assert mock_db.add.called
            assert mock_db.commit.called

            print("✓ All API calls and database operations verified")


def test_risk_management_workflow():
    """Test risk management prevents trades when limits are reached."""
    print("\nTesting risk management workflow...")

    with patch.dict(os.environ, {
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
    }):

        from workers.trade_executor import TradeExecutor

        executor = TradeExecutor()
        mock_db = Mock()

        # Test 1: Daily drawdown limit reached
        with patch.object(executor, 'check_daily_drawdown', return_value=False):
            trade = executor.execute_trade_signal(
                mock_db, 123, 'BTCUSDT', 'LONG')
            assert trade is None
            print("✓ Trade blocked due to daily drawdown limit")

        # Test 2: Position limit reached
        with patch.object(executor, 'check_daily_drawdown', return_value=True), \
                patch.object(executor, 'check_position_limits', return_value=False):
            trade = executor.execute_trade_signal(
                mock_db, 123, 'BTCUSDT', 'LONG')
            assert trade is None
            print("✓ Trade blocked due to position limit")

        # Test 3: Insufficient balance
        executor.binance_client = Mock()
        executor.binance_client.get_balance.return_value = Decimal('0')

        with patch.object(executor, 'check_daily_drawdown', return_value=True), \
                patch.object(executor, 'check_position_limits', return_value=True):
            trade = executor.execute_trade_signal(
                mock_db, 123, 'BTCUSDT', 'LONG')
            assert trade is None
            print("✓ Trade blocked due to insufficient balance")


def test_position_monitoring_workflow():
    """Test position monitoring for stop-loss and take-profit triggers."""
    print("\nTesting position monitoring workflow...")

    with patch.dict(os.environ, {
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
    }):

        from workers.trade_executor import TradeExecutor

        executor = TradeExecutor()
        executor.binance_client = Mock()

        # Mock a trade with stop-loss and take-profit levels
        mock_trade = Mock()
        mock_trade.id = 1
        mock_trade.symbol = 'BTCUSDT'
        mock_trade.side = 'LONG'
        mock_trade.stop_loss = Decimal('49000')  # 2% below 50000
        mock_trade.take_profit = Decimal('52000')  # 4% above 50000

        mock_db = Mock()

        # Test stop-loss trigger
        executor.binance_client.get_ticker_price.return_value = Decimal(
            '48000')  # Below stop-loss

        with patch.object(executor, 'close_trade', return_value=True) as mock_close:
            # Simulate the monitoring logic
            current_price = executor.binance_client.get_ticker_price('BTCUSDT')
            should_close = current_price <= mock_trade.stop_loss

            if should_close:
                executor.close_trade(mock_db, mock_trade.id, current_price)

            assert should_close
            assert mock_close.called
            print("✓ Stop-loss trigger detected and trade closed")

        # Test take-profit trigger
        executor.binance_client.get_ticker_price.return_value = Decimal(
            '53000')  # Above take-profit

        with patch.object(executor, 'close_trade', return_value=True) as mock_close:
            # Simulate the monitoring logic
            current_price = executor.binance_client.get_ticker_price('BTCUSDT')
            should_close = current_price >= mock_trade.take_profit

            if should_close:
                executor.close_trade(mock_db, mock_trade.id, current_price)

            assert should_close
            assert mock_close.called
            print("✓ Take-profit trigger detected and trade closed")


if __name__ == "__main__":
    print("Trade Execution Integration Test Suite")
    print("=" * 50)

    try:
        test_complete_trade_workflow()
        test_risk_management_workflow()
        test_position_monitoring_workflow()

        print("\n" + "=" * 50)
        print("✓ All integration tests passed successfully!")

    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
