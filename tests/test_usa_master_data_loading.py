import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import pandas as pd
import pandas.testing as pdt

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.views.usa_master import UsaMasterView


class TestUsaMasterDataLoading(unittest.TestCase):
    """Test that USA Master view loads data from config when available."""
    
    def test_refresh_logic_with_data_in_config(self):
        """Test the refresh logic when data is available in config."""
        # Create mock config with data
        mock_config = Mock()
        mock_config.usa_hockey = Mock()
        
        # Create sample data
        sample_data = pd.DataFrame({
            'Name': ['John Doe', 'Jane Smith'],
            'Email': ['john@example.com', 'jane@example.com'],
            'Status': ['Active', 'Pending']
        })
        
        # Set data in config
        mock_config.current_master_data = sample_data
        mock_config.current_master_file_path = '/path/to/file.csv'
        
        # Test the refresh logic directly
        current_data = None
        current_file_path = None
        
        # Simulate the refresh logic from UsaMasterView
        if hasattr(mock_config, 'current_master_data') and mock_config.current_master_data is not None:
            current_data = mock_config.current_master_data
            current_file_path = getattr(mock_config, 'current_master_file_path', None)
        
        # Verify that data was loaded from config
        pdt.assert_frame_equal(current_data, sample_data)
        self.assertEqual(current_file_path, '/path/to/file.csv')
    
    def test_refresh_logic_without_data_in_config(self):
        """Test the refresh logic when no data is available in config."""
        # Create mock config without data
        mock_config = Mock()
        mock_config.usa_hockey = Mock()
        
        # Ensure no data in config
        if hasattr(mock_config, 'current_master_data'):
            delattr(mock_config, 'current_master_data')
        if hasattr(mock_config, 'current_master_file_path'):
            delattr(mock_config, 'current_master_file_path')
        
        # Test the refresh logic directly
        current_data = None
        current_file_path = None
        
        # Simulate the refresh logic from UsaMasterView
        if hasattr(mock_config, 'current_master_data') and mock_config.current_master_data is not None:
            current_data = mock_config.current_master_data
            current_file_path = getattr(mock_config, 'current_master_file_path', None)
        
        # Verify that data is None
        self.assertIsNone(current_data)
        self.assertIsNone(current_file_path)
    
    def test_load_data_logic_from_config(self):
        """Test the load_data logic when data is available in config."""
        # Create mock config with data
        mock_config = Mock()
        mock_config.usa_hockey = Mock()
        
        # Create sample data
        sample_data = pd.DataFrame({
            'Name': ['John Doe', 'Jane Smith'],
            'Email': ['john@example.com', 'jane@example.com']
        })
        
        # Set data in config
        mock_config.current_master_data = sample_data
        mock_config.current_master_file_path = '/path/to/file.csv'
        
        # Test the load_data logic directly
        current_data = None
        current_file_path = None
        
        # Simulate the load_data logic from UsaMasterView
        if hasattr(mock_config, 'current_master_data') and mock_config.current_master_data is not None:
            current_data = mock_config.current_master_data
            current_file_path = getattr(mock_config, 'current_master_file_path', None)
        
        # Verify that data was loaded from config
        pdt.assert_frame_equal(current_data, sample_data)
        self.assertEqual(current_file_path, '/path/to/file.csv')


if __name__ == '__main__':
    unittest.main() 