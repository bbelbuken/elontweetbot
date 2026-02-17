"""Simple retry utilities with exponential backoff."""

import time
import functools
from typing import Callable, Type, Tuple, Optional
from app.utils.logging import get_logger

logger = get_logger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds (doubles each retry)
        max_delay: Maximum delay between retries
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called on each retry
        
    Example:
        @retry_with_backoff(max_retries=3, base_delay=2.0)
        def fetch_data():
            return api_call()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt >= max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries",
                            error=str(e),
                            attempts=attempt + 1
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    logger.warning(
                        f"Function {func.__name__} failed, retrying",
                        error=str(e),
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        retry_delay=delay
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempt, e)
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_exception
            
        return wrapper
    return decorator


def retry_api_call(func: Callable) -> Callable:
    """
    Convenience decorator for API calls with sensible defaults.
    Retries 3 times with exponential backoff starting at 1 second.
    """
    return retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0
    )(func)
