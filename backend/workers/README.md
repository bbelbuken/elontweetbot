# Tweet Ingestion Worker

This module implements the tweet ingestion worker that polls the Twitter API for crypto-related tweets and stores them in the database.

## Components

### `celery_app.py`
- Celery application configuration
- Task routing and scheduling
- Beat schedule for periodic Twitter API polling

### `twitter_client.py`
- Twitter API client with authentication
- Rate limiting and error handling
- Tweet search and user information retrieval

### `tweet_ingestion.py`
- Main worker tasks for tweet processing
- Tweet deduplication logic
- Database storage with error handling

## Usage

### Starting the Worker

```bash
# From backend directory
python scripts/start_worker.py
```

### Testing the Worker

```bash
# Safe testing (no API credits used) - RECOMMENDED
python scripts/test_worker_components.py

# Interactive testing with mock data (default)
python scripts/test_twitter_worker.py

# Real API test (uses 1 API credit - be careful!)
python scripts/test_twitter_worker.py
# Then choose option 2 when prompted
```

### Manual Task Execution

```bash
# Manual polling (uses 1 API call - be careful!)
python scripts/manual_twitter_poll.py
```

```python
# Through Celery (if worker is running)
from workers.tweet_ingestion import poll_twitter_api

result = poll_twitter_api.delay()
print(result.get())
```

## Configuration

Required environment variables:
- `TWITTER_BEARER_TOKEN`: Twitter API Bearer Token
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string for Celery broker

## API Limits

This implementation is designed for Twitter's **Free API Plan**:
- **100 reads per month** limit
- **3 scheduled polls per day** (8 AM, 2 PM, 8 PM)
- **100 tweets per request** to maximize data collection
- **93 API calls per month** (31 days × 3 = 93), staying within limits

## Features

- **Automatic Polling**: Polls Twitter API 3 times daily (8 AM, 2 PM, 8 PM)
- **Rate Limiting**: Respects Twitter API rate limits
- **Deduplication**: Prevents duplicate tweets using tweet IDs
- **Error Handling**: Retry logic with exponential backoff
- **Batch Processing**: Efficient processing of multiple tweets
- **Logging**: Structured logging for monitoring and debugging

## Requirements

The worker requires the following requirements from the spec:
- **1.1**: Polls Twitter API 3 times daily to stay within free plan limits (100 reads/month)
- **1.2**: Stores tweets with metadata (id, author, text, created_at)
- **1.3**: Implements deduplication using tweet IDs
- **1.4**: Handles Twitter API rate limits and errors