"""Twitter API client with authentication and rate limiting."""

import time
import tweepy
from typing import List, Dict, Optional
from datetime import datetime, timezone

from app.utils.logging import get_logger
from app.utils.retry import retry_with_backoff
from app.config import settings

logger = get_logger(__name__)


class TwitterClient:
    """Twitter API client with rate limiting and error handling."""

    def __init__(self):
        """Initialize Twitter API client."""
        self.client = None
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Tweepy client with bearer token."""
        try:
            self.client = tweepy.Client(
                bearer_token=settings.twitter_bearer_token,
                wait_on_rate_limit=False  # Don't wait, just fail fast for testing
            )
            logger.info("Twitter client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Twitter client", error=str(e))
            raise

    def _rate_limit_delay(self):
        """Implement basic rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    @retry_with_backoff(max_retries=2, base_delay=5.0, exceptions=(tweepy.TwitterServerError, Exception))
    def search_recent_tweets(
        self,
        query: str = "elonmusk OR @elonmusk OR \"Elon Musk\" -is:retweet lang:en",
        max_results: int = 100
    ) -> List[Dict]:
        """
        Search for recent tweets matching the query.

        Args:
            query: Twitter search query
            max_results: Maximum number of tweets to return (10-100)

        Returns:
            List of tweet dictionaries
        """
        if not self.client:
            logger.error("Twitter client not initialized")
            return []

        try:
            self._rate_limit_delay()

            # Search for tweets
            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),  # API limit is 100
                tweet_fields=["id", "text", "author_id",
                              "created_at", "public_metrics"]
            )

            if not response.data:
                logger.info("No tweets found for query", query=query)
                return []

            tweets = []
            for tweet in response.data:
                tweet_data = {
                    "id": tweet.id,
                    "text": tweet.text,
                    "author_id": tweet.author_id,
                    "created_at": tweet.created_at,
                    "public_metrics": tweet.public_metrics if hasattr(tweet, 'public_metrics') else {}
                }
                tweets.append(tweet_data)

            logger.info("Retrieved tweets from Twitter API", count=len(tweets))
            return tweets

        except tweepy.TooManyRequests as e:
            # Don't retry on rate limits - fail immediately
            logger.error("Twitter API rate limit exceeded", error=str(e))
            print(f"❌ RATE LIMIT: {e}")
            print(
                f"Response headers: {e.response.headers if hasattr(e, 'response') else 'No headers'}")
            return []
        except tweepy.Unauthorized as e:
            # Don't retry on auth errors - fail immediately
            logger.error("Twitter API unauthorized", error=str(e))
            return []
        except Exception as e:
            logger.error(
                "Error fetching tweets from Twitter API", error=str(e))
            raise  # Let retry decorator handle it

    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """
        Get user information by user ID.

        Args:
            user_id: Twitter user ID

        Returns:
            User information dictionary or None
        """
        if not self.client:
            logger.error("Twitter client not initialized")
            return None

        try:
            self._rate_limit_delay()

            user = self.client.get_user(id=user_id)
            if user.data:
                return {
                    "id": user.data.id,
                    "username": user.data.username,
                    "name": user.data.name,
                    "verified": getattr(user.data, 'verified', False)
                }
            return None

        except Exception as e:
            logger.error("Error fetching user info",
                         user_id=user_id, error=str(e))
            return None
