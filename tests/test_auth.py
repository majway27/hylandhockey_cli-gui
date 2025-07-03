#!/usr/bin/env python3
"""
Test script for the improved authentication system.
This script demonstrates how to handle token expiration and authentication errors.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config_manager import ConfigManager
from config.logging_config import setup_logging, get_logger
from auth.google_auth import (
    check_credentials_status,
    get_credentials_with_retry,
    clear_credentials,
    AuthenticationError,
    TokenExpiredError,
    CredentialsNotFoundError
)

# Setup logging
setup_logging()
logger = get_logger(__name__)

def test_authentication():
    """Test the authentication system."""
    print("=== Hyland Hockey Authentication Test ===\n")
    
    # Initialize config
    config = ConfigManager(test=True)
    print(f"Using test mode: {config.is_test_mode}")
    print(f"Scopes: {config.scopes}")
    print()
    
    # Test 1: Check credentials status
    print("1. Checking credentials status...")
    try:
        is_valid, status_message = check_credentials_status(config)
        print(f"   Status: {'✓ Valid' if is_valid else '✗ Invalid'}")
        print(f"   Message: {status_message}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test 2: Try to get credentials
    print("2. Testing credential retrieval...")
    try:
        creds = get_credentials_with_retry(config)
        print("   ✓ Successfully retrieved credentials")
        print(f"   Token valid: {creds.valid}")
        if creds.expired:
            print(f"   Token expired: {creds.expired}")
        if creds.refresh_token:
            print("   ✓ Refresh token available")
    except TokenExpiredError as e:
        print(f"   ✗ Token expired: {e}")
        print("   → Use 'Clear Tokens' button in the GUI to re-authenticate")
    except CredentialsNotFoundError as e:
        print(f"   ✗ Credentials not found: {e}")
        print("   → Make sure credentials.json file exists in config/ directory")
    except AuthenticationError as e:
        print(f"   ✗ Authentication error: {e}")
        print("   → Check your Google API project settings")
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
    print()
    
    # Test 3: Test clearing credentials
    print("3. Testing credential clearing...")
    try:
        success = clear_credentials(config)
        if success:
            print("   ✓ Credentials cleared successfully")
        else:
            print("   ✗ Failed to clear credentials")
    except Exception as e:
        print(f"   ✗ Error clearing credentials: {e}")
    print()
    
    # Test 4: Check status after clearing
    print("4. Checking status after clearing...")
    try:
        is_valid, status_message = check_credentials_status(config)
        print(f"   Status: {'✓ Valid' if is_valid else '✗ Invalid'}")
        print(f"   Message: {status_message}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    print("=== Test Complete ===")
    print("\nNext steps:")
    print("1. Run the main application: python main.py")
    print("2. Use the 'Authenticate' button to set up OAuth")
    print("3. Use 'Check Auth Status' to verify authentication")
    print("4. Use 'Test Connection' to verify Google API access")

if __name__ == "__main__":
    test_authentication() 