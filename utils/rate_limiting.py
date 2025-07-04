"""
Rate limiting utilities for Google API calls.
Provides exponential backoff retry logic and rate limiting decorators.
"""

import time
import random
import logging
from functools import wraps
from typing import Callable, Any, Optional, Dict, List
import requests

# Import HttpError conditionally to avoid import issues in tests
try:
    from googleapiclient.errors import HttpError
except ImportError:
    # Create a mock HttpError for testing
    class HttpError(Exception):
        def __init__(self, resp, content):
            self.resp = resp
            self.content = content

logger = logging.getLogger(__name__)


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded and all retries are exhausted."""
    pass


class RateLimiter:
    """Rate limiter with exponential backoff for Google API calls."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize rate limiter with configuration.
        
        Args:
            config: Configuration dictionary with rate limiting settings
        """
        self.max_retries = config.get('max_retries', 3)
        self.base_delay = config.get('base_delay', 1.0)
        self.max_delay = config.get('max_delay', 60.0)
        self.batch_delay = config.get('batch_delay', 0.5)
        self.api_call_delay = config.get('api_call_delay', 0.1)
        self.use_exponential_backoff = config.get('use_exponential_backoff', True)
        self.retry_status_codes = config.get('retry_status_codes', [429, 500, 502, 503, 504])
        
        # Track API call timing for rate limiting
        self.last_api_call = 0.0
        
    def should_retry(self, error: Exception) -> bool:
        """
        Determine if an error should trigger a retry.
        
        Args:
            error: The exception that occurred
            
        Returns:
            bool: True if the error should trigger a retry
        """
        try:
            if isinstance(error, HttpError):
                return error.resp.status in self.retry_status_codes
            elif isinstance(error, requests.exceptions.RequestException):
                return True
            elif hasattr(error, 'status_code'):
                return error.status_code in self.retry_status_codes
            elif hasattr(error, 'resp') and hasattr(error.resp, 'status'):
                return error.resp.status in self.retry_status_codes
            return False
        except Exception:
            # If we can't determine the error type, don't retry
            return False
    
    def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt using exponential backoff.
        
        Args:
            attempt: Current retry attempt (0-based)
            
        Returns:
            float: Delay in seconds
        """
        if not self.use_exponential_backoff:
            return self.base_delay
        
        # Exponential backoff with jitter
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0, 0.1 * delay)  # 10% jitter
        return delay + jitter
    
    def wait_for_rate_limit(self) -> None:
        """Wait if necessary to respect API call rate limits."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.api_call_delay:
            sleep_time = self.api_call_delay - time_since_last_call
            logger.debug(f"Rate limiting: waiting {sleep_time:.3f}s between API calls")
            time.sleep(sleep_time)
        
        self.last_api_call = time.time()
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function call
            
        Raises:
            RateLimitExceededError: If all retries are exhausted
            Exception: The last exception that occurred
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Wait for rate limit before making API call
                self.wait_for_rate_limit()
                
                # Execute the function
                result = func(*args, **kwargs)
                
                # Log success on retry
                if attempt > 0:
                    logger.info(f"API call succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if we should retry
                if attempt < self.max_retries and self.should_retry(e):
                    delay = self.get_retry_delay(attempt)
                    logger.warning(
                        f"API call failed (attempt {attempt + 1}/{self.max_retries + 1}): {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    # Don't retry or max retries reached
                    break
        
        # All retries exhausted
        if isinstance(last_exception, HttpError) and hasattr(last_exception, 'resp') and last_exception.resp.status == 429:
            raise RateLimitExceededError(f"Rate limit exceeded after {self.max_retries + 1} attempts") from last_exception
        else:
            raise last_exception


def rate_limited(config: Dict[str, Any]):
    """
    Decorator to add rate limiting to functions.
    
    Args:
        config: Configuration dictionary with rate limiting settings
        
    Returns:
        Decorated function with rate limiting
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = RateLimiter(config)
            return limiter.retry_with_backoff(func, *args, **kwargs)
        return wrapper
    return decorator


def batch_delay(config: Dict[str, Any]):
    """
    Decorator to add delay between batch operations.
    
    Args:
        config: Configuration dictionary with rate limiting settings
        
    Returns:
        Decorated function with batch delay
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Add delay after batch operation
            batch_delay_time = config.get('batch_delay', 0.5)
            if batch_delay_time > 0:
                logger.debug(f"Batch operation completed, waiting {batch_delay_time}s")
                time.sleep(batch_delay_time)
            
            return result
        return wrapper
    return decorator


def get_rate_limiting_config(config_manager) -> Dict[str, Any]:
    """
    Get rate limiting configuration from config manager.
    
    Args:
        config_manager: ConfigManager instance
        
    Returns:
        Dict containing rate limiting configuration
    """
    try:
        # Load config and get rate limiting settings
        config = config_manager.load_config()
        return config.get('rate_limiting', {})
    except Exception as e:
        logger.warning(f"Failed to load rate limiting config, using defaults: {e}")
        return {
            'max_retries': 3,
            'base_delay': 1.0,
            'max_delay': 60.0,
            'batch_delay': 0.5,
            'api_call_delay': 0.1,
            'use_exponential_backoff': True,
            'retry_status_codes': [429, 500, 502, 503, 504]
        } 