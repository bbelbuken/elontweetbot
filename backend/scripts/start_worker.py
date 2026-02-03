#!/usr/bin/env python3
"""Start Celery worker for tweet ingestion."""

import sys
import os

# Get the absolute path to the backend directory
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
sys.path.insert(0, backend_dir)

try:
    from workers.celery_app import celery_app
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Script directory: {script_dir}")
    print(f"Backend directory: {backend_dir}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

if __name__ == "__main__":
    # Start Celery worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--queues=celery'
    ])
