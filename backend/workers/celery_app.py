"""Celery application configuration."""

import os
from celery import Celery
from celery.schedules import crontab

# Create Celery app
celery_app = Celery(
    "trading_bot_workers",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=[
        "workers.tweet_ingestion",
        "workers.nlp_processor",
        "workers.trade_executor",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
)

# Beat schedule for periodic tasks - 3 times daily for free API plan (100 reads/month)
# This gives us 93 API calls per month (31 days * 3 calls = 93), staying within the limit
celery_app.conf.beat_schedule = {
    "poll-twitter-api-morning": {
        "task": "workers.tweet_ingestion.poll_twitter_api",
        "schedule": crontab(hour=8, minute=0),  # 8:00 AM daily
    },
    "poll-twitter-api-afternoon": {
        "task": "workers.tweet_ingestion.poll_twitter_api",
        "schedule": crontab(hour=14, minute=0),  # 2:00 PM daily
    },
    "poll-twitter-api-evening": {
        "task": "workers.tweet_ingestion.poll_twitter_api",
        "schedule": crontab(hour=20, minute=0),  # 8:00 PM daily
    },
    "process-unprocessed-tweets": {
        "task": "workers.nlp_processor.process_unprocessed_tweets",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    "process-trading-signals": {
        "task": "workers.trade_executor.process_trading_signals",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    "monitor-open-positions": {
        "task": "workers.trade_executor.monitor_open_positions",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    "update-position-pnl": {
        "task": "workers.trade_executor.update_position_pnl",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
}
