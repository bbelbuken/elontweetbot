"""
Prometheus metrics configuration and collection.

This module defines all Prometheus metrics used throughout the application:
- Business metrics (tweets, trades, PnL)
- Technical metrics (API duration, worker tasks)
- Health check metrics
"""

from prometheus_client import Counter, Histogram, Gauge

# Business metrics
tweets_processed = Counter('tweets_processed_total', 'Total tweets processed')
trades_executed = Counter('trades_executed_total',
                          'Total trades executed', ['symbol', 'side'])
pnl_gauge = Gauge('current_pnl', 'Current profit/loss')

# Technical metrics
api_request_duration = Histogram(
    'api_request_duration_seconds', 'API request duration', ['endpoint'])
worker_task_duration = Histogram(
    'worker_task_duration_seconds', 'Worker task duration', ['task_name'])

# Health check metrics
health_check_status = Gauge('health_check_status',
                            'Health check status', ['service'])


def initialize_health_metrics():
    """Initialize health check metrics with default values."""
    health_check_status.labels(service='database').set(0)
    health_check_status.labels(service='redis').set(0)
    health_check_status.labels(service='twitter_api').set(0)
    health_check_status.labels(service='binance_api').set(0)


def update_health_metrics(checks: dict):
    """
    Update health check metrics based on service status.

    Args:
        checks: Dictionary of service names and their health status
    """
    for service, status in checks.items():
        health_check_status.labels(service=service).set(1 if status else 0)
