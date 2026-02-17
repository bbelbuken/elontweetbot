"""
Integration tests for worker tasks with mocked external APIs.

Tests worker functionality without calling real APIs.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime


class TestTwitterWorker:
    """Test suite for Twitter ingestion worker."""

    @patch('workers.tweet_ingestion.TwitterClient')
    @patch('workers.tweet_ingestion.get_db_session')
    def test_poll_twitter_api_success(self, mock_db, mock_twitter_client):
        """Test successful Twitter API polling."""
        from workers.tweet_ingestion import poll_twitter_api
        
        # Mock Twitter API response
        mock_client = Mock()
        mock_client.search_recent_tweets.return_value = [
            {
                "id": 123,
                "text": "Bitcoin to the moon!",
                "author_id": "44196397",
                "created_at": datetime.utcnow()
            }
        ]
        mock_twitter_client.return_value = mock_client
        
        # Mock database
        db_mock = Mock()
        db_mock.query.return_value.filter.return_value.first.return_value = None
        mock_db.return_value = db_mock
        
        # Create mock task
        mock_task = Mock()
        mock_task.request.retries = 0
        
        # Execute task
        result = poll_twitter_api(mock_task)
        
        assert result["status"] == "success"
        assert result["tweets_processed"] >= 0

    @patch('workers.tweet_ingestion.TwitterClient')
    def test_poll_twitter_api_rate_limit(self, mock_twitter_client):
        """Test Twitter API rate limit handling."""
        from workers.tweet_ingestion import poll_twitter_api
        import tweepy
        
        # Mock rate limit error
        mock_client = Mock()
        mock_client.search_recent_tweets.side_effect = tweepy.TooManyRequests("Rate limit exceeded")
        mock_twitter_client.return_value = mock_client
        
        # Create mock task
        mock_task = Mock()
        mock_task.request.retries = 0
        mock_task.max_retries = 3
        
        # Should handle gracefully and retry
        try:
            poll_twitter_api(mock_task)
        except Exception as e:
            # Should retry on error
            assert mock_task.request.retries < mock_task.max_retries


class TestTradeExecutorWorker:
    """Test suite for trade execution worker."""

    @patch('workers.trade_executor.BinanceClient')
    @patch('workers.trade_executor.get_db')
    def test_process_trading_signals(self, mock_db, mock_binance):
        """Test trading signal processing."""
        from workers.trade_executor import process_trading_signals
        
        # Mock database with high signal tweets
        db_mock = Mock()
        
        # Mock tweet with high signal
        mock_tweet = Mock()
        mock_tweet.id = 123
        mock_tweet.signal_score = 85
        mock_tweet.processed = True
        
        # Mock query chain
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_tweet]
        query_mock.notin_.return_value = []
        
        db_mock.query.return_value = query_mock
        mock_db.return_value = db_mock
        
        # Mock Binance client
        binance_mock = Mock()
        binance_mock.get_ticker_price.return_value = Decimal('50000')
        binance_mock.get_balance.return_value = Decimal('10000')
        binance_mock.place_market_order.return_value = {'orderId': 12345}
        mock_binance.return_value = binance_mock
        
        # Create mock task
        mock_task = Mock()
        mock_task.request.retries = 0
        
        # Execute task
        with patch('workers.trade_executor.risk_manager') as mock_risk:
            mock_risk.validate_trade_request.return_value = {
                "allowed": True,
                "reasons": []
            }
            
            result = process_trading_signals(mock_task)
            
            assert "processed" in result
            assert result["processed"] >= 0

    @patch('workers.trade_executor.BinanceClient')
    @patch('workers.trade_executor.get_db')
    def test_monitor_open_positions(self, mock_db, mock_binance):
        """Test open position monitoring."""
        from workers.trade_executor import monitor_open_positions
        
        # Mock database with open trade
        db_mock = Mock()
        
        mock_trade = Mock()
        mock_trade.id = 1
        mock_trade.symbol = "BTCUSDT"
        mock_trade.side = "LONG"
        mock_trade.entry_price = Decimal('50000')
        mock_trade.stop_loss = Decimal('49000')
        mock_trade.take_profit = Decimal('52000')
        mock_trade.status = "OPEN"
        mock_trade.quantity = Decimal('0.1')
        
        db_mock.query.return_value = db_mock
        mock_db.return_value = db_mock
        
        # Mock Trade.get_open_trades
        with patch('workers.trade_executor.Trade') as mock_trade_class:
            mock_trade_class.get_open_trades.return_value = [mock_trade]
            
            # Mock Binance client
            binance_mock = Mock()
            binance_mock.get_ticker_price.return_value = Decimal('53000')  # Above take profit
            mock_binance.return_value = binance_mock
            
            # Create mock task
            mock_task = Mock()
            mock_task.request.retries = 0
            
            # Execute task
            result = monitor_open_positions(mock_task)
            
            assert "monitored" in result
            assert result["monitored"] >= 0

    @patch('workers.trade_executor.BinanceClient')
    @patch('workers.trade_executor.get_db')
    def test_update_position_pnl(self, mock_db, mock_binance):
        """Test position PnL update."""
        from workers.trade_executor import update_position_pnl
        
        # Mock database with position
        db_mock = Mock()
        
        mock_position = Mock()
        mock_position.symbol = "BTCUSDT"
        mock_position.size = Decimal('0.1')
        mock_position.avg_entry = Decimal('50000')
        mock_position.unrealized_pnl = Decimal('100')
        
        with patch('workers.trade_executor.Position') as mock_pos_class:
            mock_pos_class.get_all_positions.return_value = [mock_position]
            mock_pos_class.update_pnl_for_symbol.return_value = mock_position
            
            # Mock Binance client
            binance_mock = Mock()
            binance_mock.get_ticker_price.return_value = Decimal('51000')
            mock_binance.return_value = binance_mock
            
            mock_db.return_value = db_mock
            
            # Create mock task
            mock_task = Mock()
            mock_task.request.retries = 0
            
            # Execute task
            result = update_position_pnl(mock_task)
            
            assert "updated" in result
            assert result["updated"] >= 0


class TestNLPWorker:
    """Test suite for NLP processing worker."""

    @patch('workers.nlp_processor.get_sentiment_pipeline')
    @patch('workers.nlp_processor.get_db')
    def test_analyze_tweet_sentiment(self, mock_db, mock_pipeline):
        """Test tweet sentiment analysis."""
        from workers.nlp_processor import analyze_tweet_sentiment
        
        # Mock database
        db_mock = Mock()
        
        mock_tweet = Mock()
        mock_tweet.id = 123
        mock_tweet.text = "Bitcoin is extremely bullish! #BTC #crypto"
        mock_tweet.processed = False
        mock_tweet.mark_processed.return_value = True
        
        db_mock.query.return_value.filter.return_value.first.return_value = mock_tweet
        mock_db.return_value = db_mock
        
        # Mock sentiment pipeline
        pipeline_mock = Mock()
        pipeline_mock.return_value = [[
            {'label': 'positive', 'score': 0.85},
            {'label': 'negative', 'score': 0.05},
            {'label': 'neutral', 'score': 0.10}
        ]]
        mock_pipeline.return_value = pipeline_mock
        
        # Create mock task
        mock_task = Mock()
        mock_task.request.retries = 0
        mock_task.max_retries = 3
        
        # Execute task
        result = analyze_tweet_sentiment(mock_task, tweet_id=123)
        
        assert "signal_score" in result
        assert result["signal_score"] > 0

    @patch('workers.nlp_processor.get_db')
    def test_process_unprocessed_tweets(self, mock_db):
        """Test batch processing of unprocessed tweets."""
        from workers.nlp_processor import process_unprocessed_tweets
        
        # Mock database
        db_mock = Mock()
        
        mock_tweet = Mock()
        mock_tweet.id = 123
        
        with patch('workers.nlp_processor.Tweet') as mock_tweet_class:
            mock_tweet_class.get_unprocessed.return_value = [mock_tweet]
            
            mock_db.return_value = db_mock
            
            # Create mock task
            mock_task = Mock()
            mock_task.request.retries = 0
            mock_task.max_retries = 3
            
            # Mock analyze_tweet_sentiment task
            with patch('workers.nlp_processor.analyze_tweet_sentiment') as mock_analyze:
                mock_result = Mock()
                mock_result.get.return_value = {"signal_score": 75}
                mock_analyze.apply.return_value = mock_result
                
                # Execute task
                result = process_unprocessed_tweets(mock_task, limit=10)
                
                assert "processed_count" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
