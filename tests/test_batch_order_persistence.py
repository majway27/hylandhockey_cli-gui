"""
Test batch order size persistence functionality.
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# Add the project root to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_manager import ConfigManager


class TestBatchOrderPersistence(unittest.TestCase):
    """Test batch order size persistence functionality."""
    
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
""")
        
        # Create a minimal preferences file in the config directory
        config_dir = Path(__file__).parent.parent / 'config'
        self.preferences_file = config_dir / 'preferences.yaml'
        
        # Backup existing preferences file if it exists
        self.original_preferences = None
        if self.preferences_file.exists():
            with open(self.preferences_file, 'r') as f:
                self.original_preferences = f.read()
        
        # Create test preferences file
        with open(self.preferences_file, 'w') as f:
            f.write("test_mode: true\nbatch_order_size: 5\n")
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
        # Restore original preferences file
        if self.original_preferences is not None:
            with open(self.preferences_file, 'w') as f:
                f.write(self.original_preferences)
        elif self.preferences_file.exists():
            # If we created a new file, remove it
            self.preferences_file.unlink()
    
    def test_get_batch_order_size_default(self):
        """Test getting batch order size when no preference is set."""
        # Remove the preferences file to test default behavior
        os.remove(self.preferences_file)
        
        config = ConfigManager(config_file=self.config_file, test=True)
        batch_size = config.get_batch_order_size()
        
        self.assertEqual(batch_size, 1)
    
    def test_get_batch_order_size_from_preferences(self):
        """Test getting batch order size from preferences file."""
        config = ConfigManager(config_file=self.config_file, test=True)
        batch_size = config.get_batch_order_size()
        
        self.assertEqual(batch_size, 5)
    
    def test_set_batch_order_size(self):
        """Test setting batch order size and verifying it's saved."""
        config = ConfigManager(config_file=self.config_file, test=True)
        
        # Set a new batch size
        config.set_batch_order_size(10)
        
        # Verify it was saved by reading it back
        batch_size = config.get_batch_order_size()
        self.assertEqual(batch_size, 10)
        
        # Verify the file was actually updated
        with open(self.preferences_file, 'r') as f:
            content = f.read()
            self.assertIn('batch_order_size: 10', content)
    
    def test_set_batch_order_size_preserves_other_preferences(self):
        """Test that setting batch order size preserves other preferences."""
        config = ConfigManager(config_file=self.config_file, test=True)
        
        # Set a new batch size
        config.set_batch_order_size(15)
        
        # Verify test_mode is still preserved
        self.assertTrue(config.is_test_mode)
        
        # Verify the file contains both preferences
        with open(self.preferences_file, 'r') as f:
            content = f.read()
            self.assertIn('test_mode: true', content)
            self.assertIn('batch_order_size: 15', content)


if __name__ == '__main__':
    unittest.main() 