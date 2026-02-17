"""
Handler for failed Celery tasks (dead letter queue).

This module provides a simple dead letter queue implementation for tasks
that have exhausted all retry attempts.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from celery import signals

from app.utils.logging import get_logger
from app.database import get_db_session
from sqlalchemy import Column, Integer, String, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base

logger = get_logger(__name__)

Base = declarative_base()


class FailedTask(Base):
    """Model to store failed tasks for later inspection."""
    __tablename__ = "failed_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(255), unique=True, index=True)
    task_name = Column(String(255), index=True)
    args = Column(JSON)
    kwargs = Column(JSON)
    exception = Column(String(1000))
    traceback = Column(String(5000))
    failed_at = Column(DateTime, default=datetime.utcnow)
    retries_exhausted = Column(Integer, default=0)


@signals.task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, 
                       args=None, kwargs=None, traceback=None, 
                       einfo=None, **kw):
    """
    Signal handler for task failures.
    Stores failed tasks in database for inspection and potential replay.
    """
    try:
        # Only log to dead letter queue if all retries are exhausted
        task = sender
        if hasattr(task, 'request') and task.request.retries >= task.max_retries:
            logger.error(
                "Task failed after all retries, adding to dead letter queue",
                task_id=task_id,
                task_name=sender.name,
                exception=str(exception),
                retries=task.request.retries
            )
            
            db = get_db_session()
            if db:
                try:
                    failed_task = FailedTask(
                        task_id=task_id,
                        task_name=sender.name,
                        args=args,
                        kwargs=kwargs,
                        exception=str(exception)[:1000],  # Truncate to fit
                        traceback=str(traceback)[:5000] if traceback else None,
                        retries_exhausted=task.request.retries
                    )
                    db.add(failed_task)
                    db.commit()
                    logger.info("Failed task stored in dead letter queue", task_id=task_id)
                except Exception as e:
                    db.rollback()
                    logger.error("Failed to store task in dead letter queue", error=str(e))
                finally:
                    db.close()
        else:
            # Just log normal failures that will be retried
            logger.warning(
                "Task failed, will retry",
                task_id=task_id,
                task_name=sender.name,
                exception=str(exception),
                retry=task.request.retries if hasattr(task, 'request') else 0
            )
            
    except Exception as e:
        logger.error("Error in task failure handler", error=str(e))


def get_failed_tasks(limit: int = 100) -> list:
    """
    Retrieve failed tasks from dead letter queue.
    
    Args:
        limit: Maximum number of failed tasks to retrieve
        
    Returns:
        List of failed task records
    """
    db = get_db_session()
    if not db:
        return []
    
    try:
        failed_tasks = db.query(FailedTask).order_by(
            FailedTask.failed_at.desc()
        ).limit(limit).all()
        return failed_tasks
    finally:
        db.close()


def clear_failed_tasks(days_old: int = 30):
    """
    Clean up old failed tasks from dead letter queue.
    
    Args:
        days_old: Remove tasks older than this many days
    """
    db = get_db_session()
    if not db:
        return
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        deleted = db.query(FailedTask).filter(
            FailedTask.failed_at < cutoff_date
        ).delete()
        db.commit()
        logger.info(f"Cleaned up {deleted} old failed tasks")
    except Exception as e:
        db.rollback()
        logger.error("Failed to clean up old failed tasks", error=str(e))
    finally:
        db.close()
