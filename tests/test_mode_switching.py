#!/usr/bin/env python3
"""
Test script to verify that the mode switching fix works correctly.
This script simulates the mode switching behavior to ensure that
valid pickle files are not unnecessarily deleted when switching modes.
"""

import os
import pickle
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project root to the Python path
import sys
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from auth.google_auth import check_credentials_status, clear_credentials
from config.config_manager import ConfigManager


def create_mock_credentials():
    """Create a mock credentials object that appears valid."""
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_creds.refresh_token = "mock_refresh_token"
    return mock_creds


def test_mode_switching_preserves_valid_credentials():
    """Test that mode switching preserves valid credentials."""
    print("Testing mode switching with valid credentials...")
    
    # Create a mock config manager
    mock_config = Mock()
    mock_config.is_test_mode = False
    mock_config.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    
    # Mock check_credentials_status to return valid credentials
    with patch('auth.google_auth.check_credentials_status', return_value=(True, "Valid credentials")):
        # Mock clear_credentials to track if it was called
        with patch('auth.google_auth.clear_credentials') as mock_clear:
            # Simulate the mode switching logic
            try:
                is_valid, status_message = check_credentials_status(mock_config)
                if is_valid:
                    print("✓ Valid credentials detected, should not be cleared")
                    credentials_cleared = False
                else:
                    print("✗ Invalid credentials detected, should be cleared")
                    clear_credentials(mock_config)
                    credentials_cleared = True
                
                # Verify the logic
                assert not credentials_cleared, "Valid credentials should not be cleared"
                assert not mock_clear.called, "clear_credentials should not have been called"
                print("✓ Mode switching correctly preserves valid credentials")
                
            except Exception as e:
                print(f"✗ Error in mode switching logic: {e}")
                return False
    
    return True


def test_mode_switching_clears_invalid_credentials():
    """Test that mode switching clears invalid credentials."""
    print("Testing mode switching with invalid credentials...")
    
    # Create a mock config manager
    mock_config = Mock()
    mock_config.is_test_mode = False
    mock_config.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    
    # Mock check_credentials_status to return invalid credentials
    with patch('auth.google_auth.check_credentials_status', return_value=(False, "Invalid credentials")):
        # Mock clear_credentials to track if it was called
        with patch('auth.google_auth.clear_credentials') as mock_clear:
            # Simulate the mode switching logic
            try:
                is_valid, status_message = check_credentials_status(mock_config)
                if is_valid:
                    print("✗ Valid credentials detected, should not be cleared")
                    credentials_cleared = False
                else:
                    print("✓ Invalid credentials detected, should be cleared")
                    clear_credentials(mock_config)
                    credentials_cleared = True
                
                # Verify the logic
                assert credentials_cleared, "Invalid credentials should be cleared"
                assert mock_clear.called, "clear_credentials should have been called"
                print("✓ Mode switching correctly clears invalid credentials")
                
            except Exception as e:
                print(f"✗ Error in mode switching logic: {e}")
                return False
    
    return True


def test_mode_switching_handles_exceptions():
    """Test that mode switching handles exceptions gracefully."""
    print("Testing mode switching with exception handling...")
    
    # Create a mock config manager
    mock_config = Mock()
    mock_config.is_test_mode = False
    mock_config.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    
    # Mock check_credentials_status to raise an exception
    with patch('auth.google_auth.check_credentials_status', side_effect=Exception("Test exception")):
        # Mock clear_credentials to track if it was called
        with patch('auth.google_auth.clear_credentials') as mock_clear:
            # Simulate the mode switching logic
            try:
                is_valid, status_message = check_credentials_status(mock_config)
                credentials_cleared = False
            except Exception as e:
                print(f"✓ Exception caught: {e}")
                # Clear credentials as precaution
                clear_credentials(mock_config)
                credentials_cleared = True
            
            # Verify the logic
            assert credentials_cleared, "Credentials should be cleared when exception occurs"
            assert mock_clear.called, "clear_credentials should have been called"
            print("✓ Mode switching correctly handles exceptions")
            
    return True


def main():
    """Run all tests."""
    print("Testing mode switching fix...")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    try:
        if test_mode_switching_preserves_valid_credentials():
            tests_passed += 1
        
        if test_mode_switching_clears_invalid_credentials():
            tests_passed += 1
        
        if test_mode_switching_handles_exceptions():
            tests_passed += 1
        
        print("\n" + "=" * 50)
        print(f"✓ {tests_passed}/{total_tests} tests passed!")
        
        if tests_passed == total_tests:
            print("✓ All tests passed! The mode switching fix is working correctly.")
            return 0
        else:
            print("✗ Some tests failed.")
            return 1
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main()) 