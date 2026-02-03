"""Tweet ingestion worker for polling Twitter API and storing tweets."""

from datetime import datetime, timezone
from typing import List, Dict
from sqlalchemy.exc import IntegrityError

from .celery_app import celery_app
from app.clients.twitter_client import TwitterClient
from app.database import get_db_session
from app.models.tweet import Tweet
from app.utils.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def poll_twitter_api(self):
    """
    Periodic task to poll Twitter API for Elon Musk related tweets.

    This task runs 3 times daily (8 AM, 2 PM, 8 PM) to stay within 
    the free API plan limit of 100 reads per month.
    """
    try:
        logger.info("Starting Twitter API polling")

        # Initialize Twitter client
        twitter_client = TwitterClient()

        # Search for Elon Musk related tweets - maximize results for free API plan
        tweets = twitter_client.search_recent_tweets(
            query="elonmusk OR @elonmusk OR \"Elon Musk\" -is:retweet lang:en",
            max_results=100  # Maximum allowed per request
        )

        # Filter for tweets from Elon Musk specifically (his user ID: 44196397)
        elon_user_id = "44196397"  # Elon Musk's Twitter user ID
        elon_tweets = [tweet for tweet in tweets if tweet.get(
            "author_id") == elon_user_id]

        logger.info("Filtered tweets from Elon Musk",
                    total_tweets=len(tweets), elon_tweets=len(elon_tweets))

        if not tweets:
            logger.info("No new tweets found")
            return {"status": "success", "tweets_processed": 0}

        # Use only Elon's tweets if any found, otherwise use all tweets
        tweets_to_process = elon_tweets if elon_tweets else tweets

        logger.info("Processing tweets",
                    total_found=len(tweets),
                    elon_only=len(elon_tweets),
                    processing=len(tweets_to_process))

        # Process tweets in batch
        processed_count = 0
        for tweet_data in tweets_to_process:
            try:
                if store_tweet(tweet_data):
                    processed_count += 1
            except Exception as e:
                logger.error("Error processing individual tweet",
                             tweet_id=tweet_data.get("id"), error=str(e))
                continue

        logger.info("Twitter API polling completed",
                    total_tweets=len(tweets), processed=processed_count)

        return {
            "status": "success",
            "tweets_found": len(tweets),
            "tweets_processed": processed_count
        }

    except Exception as exc:
        logger.error("Twitter API polling failed", error=str(exc))
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


def store_tweet(tweet_data: Dict) -> bool:
    """
    Store a single tweet in the database with deduplication.

    Args:
        tweet_data: Tweet data from Twitter API

    Returns:
        True if tweet was stored, False if it was a duplicate or failed
    """
    db = get_db_session()
    if not db:
        logger.error("Failed to get database session")
        return False

    try:
        # Check if tweet already exists (deduplication)
        existing_tweet = db.query(Tweet).filter(
            Tweet.id == tweet_data["id"]).first()
        if existing_tweet:
            logger.debug("Tweet already exists, skipping",
                         tweet_id=tweet_data["id"])
            return False

        # Use author_id as username to avoid additional API calls
        # This saves API credits - we can get usernames later if needed
        author_username = f"user_{tweet_data['author_id']}"

        # Create new tweet record
        tweet = Tweet(
            id=tweet_data["id"],
            author=author_username,
            text=tweet_data["text"],
            created_at=tweet_data["created_at"],
            processed=False
        )

        # Store in database
        db.add(tweet)
        db.commit()

        logger.info("Tweet stored successfully",
                    tweet_id=tweet.id, author=tweet.author)
        return True

    except IntegrityError:
        # Handle duplicate key constraint (race condition)
        db.rollback()
        logger.debug("Tweet already exists (race condition)",
                     tweet_id=tweet_data["id"])
        return False

    except Exception as e:
        db.rollback()
        logger.error("Error storing tweet",
                     tweet_id=tweet_data.get("id"), error=str(e))
        return False

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def process_tweet_batch(self, tweet_ids: List[int]):
    """
    Process a batch of tweets for efficiency.

    Args:
        tweet_ids: List of tweet IDs to process
    """
    try:
        logger.info("Processing tweet batch", count=len(tweet_ids))

        db = get_db_session()
        if not db:
            logger.error("Failed to get database session")
            return {"status": "error", "message": "Database unavailable"}

        try:
            # Fetch unprocessed tweets
            tweets = db.query(Tweet).filter(
                Tweet.id.in_(tweet_ids),
                Tweet.processed == False
            ).all()

            processed_count = 0
            for tweet in tweets:
                # Mark as processed (placeholder - actual NLP processing in task 5)
                tweet.processed = True
                processed_count += 1

            db.commit()

            logger.info("Tweet batch processed", processed=processed_count)
            return {"status": "success", "processed": processed_count}

        finally:
            db.close()

    except Exception as exc:
        logger.error("Tweet batch processing failed", error=str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
