"""
Test rate limiting functionality.
"""

import unittest
import time
import tempfile
import os
from pathlib import Path
import sys
from unittest.mock import Mock, patch

# Add the project root to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.rate_limiting import RateLimiter, RateLimitExceededError, get_rate_limiting_config
from config.config_manager import ConfigManager


class TestRateLimiting(unittest.TestCase):
    """Test rate limiting functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test config files
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'config.yaml')
        
        # Create a minimal config file for testing
        with open(self.config_file, 'w') as f:
            f.write("""
organization_name: Test Organization
organization_name_test: Test Organization Test
scopes: ['https://www.googleapis.com/auth/gmail.readonly']
scopes_test: ['https://www.googleapis.com/auth/gmail.readonly']
jersey_spreadsheet_name: Test Spreadsheet
jersey_spreadsheet_name_test: Test Spreadsheet Test
jersey_spreadsheet_id: test_id
jersey_spreadsheet_id_test: test_id_test
jersey_worksheet_jersey_orders_gid: test_gid
jersey_worksheet_jersey_orders_gid_test: test_gid_test
jersey_worksheet_jersey_orders_name: Test Orders
jersey_worksheet_jersey_orders_name_test: Test Orders Test
jersey_sender_email: test@example.com
jersey_sender_email_test: test@example.com
jersey_default_to_email: recipient@example.com
jersey_default_to_email_test: recipient@example.com
rate_limiting:
  max_retries: 2
  base_delay: 0.1
  max_delay: 1.0
  batch_delay: 0.1
  api_call_delay: 0.05
  use_exponential_backoff: true
  retry_status_codes: [429, 500, 502, 503, 504]
""")
        
        # Create config manager for testing
        self.config_manager = ConfigManager(self.config_file)
    
    def test_rate_limiter_initialization(self):
        """Test that RateLimiter initializes correctly."""
        config = {
            'max_retries': 3,
            'base_delay': 1.0,
            'max_delay': 60.0,
            'batch_delay': 0.5,
            'api_call_delay': 0.1,
            'use_exponential_backoff': True,
            'retry_status_codes': [429, 500, 502, 503, 504]
        }
        
        limiter = RateLimiter(config)
        
        self.assertEqual(limiter.max_retries, 3)
        self.assertEqual(limiter.base_delay, 1.0)
        self.assertEqual(limiter.max_delay, 60.0)
        self.assertEqual(limiter.batch_delay, 0.5)
        self.assertEqual(limiter.api_call_delay, 0.1)
        self.assertTrue(limiter.use_exponential_backoff)
        self.assertEqual(limiter.retry_status_codes, [429, 500, 502, 503, 504])
    
    def test_should_retry_http_error(self):
        """Test that HTTP errors are correctly identified for retry."""
        config = {'retry_status_codes': [429, 500, 502, 503, 504]}
        limiter = RateLimiter(config)
        
        # Mock HTTP error with resp attribute
        mock_error = Mock()
        mock_error.resp = Mock()
        mock_error.resp.status = 429
        
        self.assertTrue(limiter.should_retry(mock_error))
        
        # Test non-retryable error
        mock_error.resp.status = 400
        self.assertFalse(limiter.should_retry(mock_error))
    
    def test_get_retry_delay_exponential_backoff(self):
        """Test exponential backoff delay calculation."""
        config = {
            'base_delay': 1.0,
            'max_delay': 10.0,
            'use_exponential_backoff': True
        }
        limiter = RateLimiter(config)
        
        # Test exponential backoff
        delay1 = limiter.get_retry_delay(0)  # First retry
        delay2 = limiter.get_retry_delay(1)  # Second retry
        delay3 = limiter.get_retry_delay(2)  # Third retry
        
        # Delays should increase exponentially (with some jitter)
        self.assertGreater(delay2, delay1)
        self.assertGreater(delay3, delay2)
        
        # But should not exceed max_delay
        self.assertLessEqual(delay1, 10.0)
        self.assertLessEqual(delay2, 10.0)
        self.assertLessEqual(delay3, 10.0)
    
    def test_get_retry_delay_no_exponential_backoff(self):
        """Test delay calculation without exponential backoff."""
        config = {
            'base_delay': 1.0,
            'use_exponential_backoff': False
        }
        limiter = RateLimiter(config)
        
        delay1 = limiter.get_retry_delay(0)
        delay2 = limiter.get_retry_delay(1)
        delay3 = limiter.get_retry_delay(2)
        
        # All delays should be approximately the same (base_delay)
        self.assertAlmostEqual(delay1, 1.0, delta=0.1)
        self.assertAlmostEqual(delay2, 1.0, delta=0.1)
        self.assertAlmostEqual(delay3, 1.0, delta=0.1)
    
    def test_retry_with_backoff_success(self):
        """Test successful retry with backoff."""
        config = {
            'max_retries': 2,
            'base_delay': 0.1,
            'use_exponential_backoff': True
        }
        limiter = RateLimiter(config)
        
        # Mock function that succeeds on first try
        mock_func = Mock(return_value="success")
        
        result = limiter.retry_with_backoff(mock_func)
        
        self.assertEqual(result, "success")
        mock_func.assert_called_once()
    
    def test_retry_with_backoff_success_after_retry(self):
        """Test successful retry after initial failure."""
        config = {
            'max_retries': 2,
            'base_delay': 0.1,
            'use_exponential_backoff': True
        }
        limiter = RateLimiter(config)
        
        # Mock function that fails once then succeeds
        mock_func = Mock(side_effect=[Exception("429 error"), "success"])
        
        # Mock the should_retry method to return True for the first error
        with patch.object(limiter, 'should_retry', side_effect=[True, False]):
            result = limiter.retry_with_backoff(mock_func)
            
            self.assertEqual(result, "success")
            self.assertEqual(mock_func.call_count, 2)
    
    def test_retry_with_backoff_max_retries_exceeded(self):
        """Test that max retries are respected."""
        config = {
            'max_retries': 2,
            'base_delay': 0.1,
            'use_exponential_backoff': True
        }
        limiter = RateLimiter(config)
        
        # Mock function that always fails
        mock_func = Mock(side_effect=Exception("429 error"))
        
        # Mock the should_retry method to always return True
        with patch.object(limiter, 'should_retry', return_value=True):
            with self.assertRaises(Exception):
                limiter.retry_with_backoff(mock_func)
            
            # Should have been called max_retries + 1 times (initial + retries)
            self.assertEqual(mock_func.call_count, 3)
    
    def test_get_rate_limiting_config(self):
        """Test getting rate limiting config from config manager."""
        config = get_rate_limiting_config(self.config_manager)
        
        self.assertEqual(config['max_retries'], 2)
        self.assertEqual(config['base_delay'], 0.1)
        self.assertEqual(config['max_delay'], 1.0)
        self.assertEqual(config['batch_delay'], 0.1)
        self.assertEqual(config['api_call_delay'], 0.05)
        self.assertTrue(config['use_exponential_backoff'])
        self.assertEqual(config['retry_status_codes'], [429, 500, 502, 503, 504])
    
    def test_get_rate_limiting_config_defaults(self):
        """Test getting rate limiting config with defaults."""
        # Create config manager without rate limiting section
        temp_config_file = os.path.join(self.temp_dir, 'config_no_rate.yaml')
        with open(temp_config_file, 'w') as f:
            f.write("""
organization_name: Test Organization
jersey_spreadsheet_id: test_id
jersey_worksheet_jersey_orders_gid: test_gid
jersey_sender_email: test@example.com
jersey_default_to_email: recipient@example.com
""")
        
        config_manager = ConfigManager(temp_config_file)
        config = get_rate_limiting_config(config_manager)
        
        # Should use defaults
        self.assertEqual(config['max_retries'], 3)
        self.assertEqual(config['base_delay'], 1.0)
        self.assertEqual(config['max_delay'], 60.0)
        self.assertEqual(config['batch_delay'], 0.5)
        self.assertEqual(config['api_call_delay'], 0.1)
        self.assertTrue(config['use_exponential_backoff'])
        self.assertEqual(config['retry_status_codes'], [429, 500, 502, 503, 504])
    
    def test_wait_for_rate_limit(self):
        """Test rate limiting between API calls."""
        config = {'api_call_delay': 0.1}
        limiter = RateLimiter(config)
        
        start_time = time.time()
        limiter.wait_for_rate_limit()  # First call should not wait
        first_call_time = time.time() - start_time
        
        # Second call should wait
        start_time = time.time()
        limiter.wait_for_rate_limit()
        second_call_time = time.time() - start_time
        
        # First call should be fast, second should have delay
        self.assertLess(first_call_time, 0.05)  # Should be very fast
        self.assertGreater(second_call_time, 0.08)  # Should have delay
        self.assertLess(second_call_time, 0.15)  # But not too long


if __name__ == '__main__':
    unittest.main() 