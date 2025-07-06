#!/usr/bin/env python3
"""
Test script for USA Hockey integration components.
This script tests the configuration, authentication, and workflow components.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config_manager import ConfigManager
from config.usa_hockey_config import USAHockeyConfig
from config.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def test_configuration():
    """Test USA Hockey configuration loading."""
    print("=== Testing USA Hockey Configuration ===\n")
    
    try:
        # Initialize config manager
        config = ConfigManager(test=True)
        print(f"✅ ConfigManager initialized (test mode: {config.is_test_mode})")
        
        # Get USA Hockey config
        usa_config = config.usa_hockey
        print(f"✅ USAHockeyConfig initialized")
        
        # Test configuration properties
        print(f"Login URL: {usa_config.login_url}")
        print(f"Base URL: {usa_config.base_url}")
        print(f"Reports URL: {usa_config.reports_url}")
        print(f"Download directory: {usa_config.download_directory}")
        print(f"Browser type: {usa_config.browser_type}")
        print(f"Headless mode: {usa_config.headless}")
        
        # Test credentials validation
        has_creds = usa_config.validate_credentials()
        print(f"Credentials available: {has_creds}")
        
        if has_creds:
            print(f"Username: {usa_config.username}")
            print(f"Password: {'*' * len(usa_config.password) if usa_config.password else 'Not set'}")
        else:
            print("⚠️  No credentials found. Add username and password to config.yaml file.")
        
        print("\n✅ Configuration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_workflow_components():
    """Test workflow components."""
    print("\n=== Testing Workflow Components ===\n")
    
    try:
        # Initialize config
        config = ConfigManager(test=True)
        usa_config = config.usa_hockey
        
        # Test workflow initialization
        from workflow.usa_hockey.master_reports import MasterReportsWorkflow
        workflow = MasterReportsWorkflow(usa_config)
        print("✅ MasterReportsWorkflow initialized")
        
        # Test data processor
        from workflow.usa_hockey.data_processor import DataProcessor
        processor = DataProcessor()
        print("✅ DataProcessor initialized")
        
        # Test credential validation
        has_creds = workflow.validate_credentials()
        print(f"Workflow credential validation: {has_creds}")
        
        # Test download directory
        download_dir = workflow.get_download_directory()
        print(f"Download directory: {download_dir}")
        
        # Test listing downloaded reports
        reports = workflow.list_downloaded_reports()
        print(f"Found {len(reports)} existing reports")
        
        print("\n✅ Workflow components test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Workflow components test failed: {e}")
        return False


def test_ui_components():
    """Test UI components (without actually creating the GUI)."""
    print("\n=== Testing UI Components ===\n")
    
    try:
        # Test that we can import UI components
        from ui.views.usa_master import UsaMasterView
        print("✅ UsaMasterView import successful")
        
        # Test that we can import the main app
        from ui.app import RegistrarApp
        print("✅ RegistrarApp import successful")
        
        print("\n✅ UI components test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ UI components test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 USA Hockey Integration Test Suite")
    print("=" * 50)
    
    # Run tests
    config_success = test_configuration()
    workflow_success = test_workflow_components()
    ui_success = test_ui_components()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Configuration: {'✅ PASS' if config_success else '❌ FAIL'}")
    print(f"Workflow Components: {'✅ PASS' if workflow_success else '❌ FAIL'}")
    print(f"UI Components: {'✅ PASS' if ui_success else '❌ FAIL'}")
    
    all_passed = config_success and workflow_success and ui_success
    
    if all_passed:
        print("\n🎉 All tests passed! USA Hockey integration is ready.")
        print("\nNext steps:")
        print("1. Add username and password to config.yaml file")
        print("2. Run the main application: python main.py")
        print("3. Navigate to 'Master (USA)' tab to test the functionality")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 