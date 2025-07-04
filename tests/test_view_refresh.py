import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.app import RegistrarApp


class TestViewRefresh(unittest.TestCase):
    """Test that views refresh when displayed."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock objects
        self.mock_config = Mock()
        self.mock_config.organization_name = "Test Organization"
        self.mock_config.is_test_mode = True
        
        self.mock_order_verification = Mock()
        self.mock_log_viewer = Mock()
        
        # Mock tkinter components to avoid GUI issues
        with patch('tkinter.Tk') as mock_tk:
            with patch('ttkbootstrap.Window') as mock_window:
                with patch('tkinter.StringVar') as mock_stringvar:
                    # Mock the StringVar to return a Mock object
                    mock_stringvar.return_value = Mock()
                    mock_window.return_value = Mock()
                    self.app = RegistrarApp(
                        self.mock_config,
                        self.mock_order_verification,
                        self.mock_log_viewer
                    )
    
    def test_single_order_view_refresh_on_show(self):
        """Test that Single (Order) view refreshes when displayed."""
        # Get the Single (Order) view
        single_order_view = self.app.views["Single (Order)"]
        
        # Mock the refresh method
        single_order_view.refresh = Mock()
        
        # Call show_view to display the Single (Order) view
        self.app.show_view("Single (Order)")
        
        # Verify that refresh was called
        single_order_view.refresh.assert_called_once()
    
    def test_batch_orders_view_refresh_on_show(self):
        """Test that Batch (Orders) view refreshes when displayed."""
        # Get the Batch (Orders) view
        batch_orders_view = self.app.views["Batch (Orders)"]
        
        # Mock the refresh method
        batch_orders_view.refresh = Mock()
        
        # Call show_view to display the Batch (Orders) view
        self.app.show_view("Batch (Orders)")
        
        # Verify that refresh was called
        batch_orders_view.refresh.assert_called_once()
    
    def test_dashboard_view_refresh_on_show(self):
        """Test that Dashboard view refreshes when displayed."""
        # Get the Dashboard view
        dashboard_view = self.app.views["Dashboard"]
        
        # Mock the refresh method
        dashboard_view.refresh = Mock()
        
        # Call show_view to display the Dashboard view
        self.app.show_view("Dashboard")
        
        # Verify that refresh was called
        dashboard_view.refresh.assert_called_once()
    
    def test_email_view_no_refresh_on_show(self):
        """Test that Email view does not refresh when displayed."""
        # Get the Email view
        email_view = self.app.views["Email"]
        
        # Mock the refresh method (if it exists)
        if hasattr(email_view, 'refresh'):
            email_view.refresh = Mock()
        
        # Call show_view to display the Email view
        self.app.show_view("Email")
        
        # Verify that refresh was NOT called (Email view doesn't have refresh)
        if hasattr(email_view, 'refresh'):
            email_view.refresh.assert_not_called()
    
    def test_configuration_view_no_refresh_on_show(self):
        """Test that Configuration view does not refresh when displayed."""
        # Get the Configuration view
        config_view = self.app.views["Configuration"]
        
        # Mock the refresh method (if it exists)
        if hasattr(config_view, 'refresh'):
            config_view.refresh = Mock()
        
        # Call show_view to display the Configuration view
        self.app.show_view("Configuration")
        
        # Verify that refresh was NOT called
        if hasattr(config_view, 'refresh'):
            config_view.refresh.assert_not_called()
    
    def test_logs_view_no_refresh_on_show(self):
        """Test that Logs view does not refresh when displayed."""
        # Get the Logs view
        logs_view = self.app.views["Logs"]
        
        # Mock the refresh method (if it exists)
        if hasattr(logs_view, 'refresh'):
            logs_view.refresh = Mock()
        
        # Call show_view to display the Logs view
        self.app.show_view("Logs")
        
        # Verify that refresh was NOT called
        if hasattr(logs_view, 'refresh'):
            logs_view.refresh.assert_not_called()


if __name__ == '__main__':
    unittest.main() 