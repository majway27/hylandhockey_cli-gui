#!/usr/bin/env python3
"""
Test script to verify the organization_name configuration works correctly.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path.cwd())
if project_root not in sys.path:
    sys.path.append(project_root)

from config.config_manager import ConfigManager

def test_config():
    """Test the organization_name configuration."""
    print("Testing organization_name configuration...")
    
    # Test production mode
    try:
        config_prod = ConfigManager(test=False)
        print(f"Production organization_name: {config_prod.organization_name}")
    except Exception as e:
        print(f"Error loading production config: {e}")
    
    # Test test mode
    try:
        config_test = ConfigManager(test=True)
        print(f"Test organization_name: {config_test.organization_name}")
    except Exception as e:
        print(f"Error loading test config: {e}")
    
    print("Configuration test completed.")

if __name__ == "__main__":
    test_config() 