# Testing Guide

## Setup

Install test dependencies:
```bash
pip install -r requirements-test.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_models.py
```

### Run specific test class
```bash
pytest tests/test_models.py::TestTweetModel
```

### Run specific test
```bash
pytest tests/test_models.py::TestTweetModel::test_mark_processed
```

### Run tests by marker
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only worker tests
pytest -m worker
```

### Run with coverage
```bash
pytest --cov=app --cov=workers --cov-report=html
```

## Test Structure

```
backend/tests/
├── test_models.py           # Unit tests for models
├── test_api_endpoints.py    # Integration tests for API
├── test_workers_mocked.py   # Worker tests with mocked APIs
├── test_nlp.py             # NLP processing tests
└── test_risk_management.py # Risk management tests
```

## Writing Tests

### Unit Test Example
```python
def test_calculate_pnl():
    """Test PnL calculation."""
    entry = Decimal('50000')
    exit = Decimal('51000')
    quantity = Decimal('0.1')
    
    pnl = (exit - entry) * quantity
    assert pnl == Decimal('100')
```

### API Test Example
```python
@patch('app.database.get_db')
def test_get_tweets(mock_db):
    """Test GET /api/tweets endpoint."""
    client = TestClient(app)
    response = client.get("/api/tweets/")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### Worker Test Example
```python
@patch('workers.tweet_ingestion.TwitterClient')
def test_poll_twitter(mock_client):
    """Test Twitter polling worker."""
    mock_client.return_value.search_recent_tweets.return_value = []
    
    result = poll_twitter_api(mock_task)
    assert result["status"] == "success"
```

## Test Coverage

Current test coverage focuses on:
- ✅ Model business logic
- ✅ API endpoint functionality
- ✅ Worker task execution (mocked)
- ✅ NLP processing
- ✅ Risk management

## CI/CD Integration

Add to GitHub Actions:
```yaml
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=app --cov=workers
```
