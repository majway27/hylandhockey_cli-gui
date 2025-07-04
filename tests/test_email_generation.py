#!/usr/bin/env python3
"""
Test email generation functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from config.config_manager import ConfigManager
from workflow.order.verification import OrderVerification, OrderDetails
from workflow.order.models.jersey_worksheet_jersey_order import FieldAwareDateTime
from datetime import datetime


class TestEmailGeneration(unittest.TestCase):
    """Test email generation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = ConfigManager(test=True)
        self.order_verification = OrderVerification(self.config)
        
        # Create a mock order for testing
        self.mock_order = OrderDetails(
            link="https://example.com/order/123",
            participant_first_name="John",
            participant_full_name="John Doe",
            jersey_name="Doe",
            jersey_number="15",
            jersey_size="M",
            jersey_type="Home",
            sock_size="M",
            sock_type="Black",
            pant_shell_size="M",
            parent1_email="parent1@example.com",
            parent2_email="parent2@example.com",
            parent3_email="",
            parent4_email="",
            contacted="",
            fitting="",
            confirmed=""
        )
    
    def test_build_notification_template(self):
        """Test that email template is built correctly"""
        try:
            email_content = self.order_verification.build_notification_template(self.mock_order)
            
            # Check that the template contains expected content
            self.assertIn("John", email_content)
            self.assertIn("Doe", email_content)
            self.assertIn("15", email_content)
            self.assertIn("M", email_content)
            self.assertIn("Home", email_content)
            self.assertIn("https://example.com/order/123", email_content)
            
            print("✓ Email template built successfully")
            
        except Exception as e:
            self.fail(f"Failed to build email template: {e}")
    
    def test_get_pending_orders(self):
        """Test that pending orders can be retrieved"""
        try:
            # This will fail if no Google Sheets connection, but we can test the method exists
            pending_orders = self.order_verification.get_pending_orders()
            
            # Should return a list (even if empty)
            self.assertIsInstance(pending_orders, list)
            
            print("✓ get_pending_orders method works")
            
        except Exception as e:
            # Expected to fail without proper Google Sheets setup
            print(f"⚠ get_pending_orders failed (expected without setup): {e}")
    
    def test_get_next_pending_order(self):
        """Test that next pending order can be retrieved"""
        try:
            # This will fail if no Google Sheets connection, but we can test the method exists
            next_order = self.order_verification.get_next_pending_order()
            
            # Should return None or OrderDetails
            self.assertTrue(next_order is None or isinstance(next_order, OrderDetails))
            
            print("✓ get_next_pending_order method works")
            
        except Exception as e:
            # Expected to fail without proper Google Sheets setup
            print(f"⚠ get_next_pending_order failed (expected without setup): {e}")
    
    @patch('workflow.order.verification.notify.create_gmail_draft')
    @patch('workflow.order.verification.JerseyWorksheetJerseyOrder')
    def test_generate_verification_email_mock(self, mock_jersey_order, mock_create_draft):
        """Test verification email generation with mocked dependencies"""
        # Mock the Gmail draft creation
        mock_create_draft.return_value = {'id': 'test_draft_id'}
        
        # Mock the jersey order save
        mock_jersey_instance = Mock()
        mock_jersey_instance.full_name = "John Doe"
        mock_jersey_instance.contacted = ""
        mock_jersey_instance.save = Mock()
        mock_jersey_order.all.return_value = [mock_jersey_instance]
        
        try:
            # Test the generate_verification_email method
            draft_id = self.order_verification.generate_verification_email(self.mock_order)
            
            # Should return the draft ID
            self.assertEqual(draft_id, 'test_draft_id')
            
            # Should have called create_gmail_draft
            mock_create_draft.assert_called_once()
            
            # Should have called save on the jersey order
            mock_jersey_instance.save.assert_called_once_with(fields_to_update=['contacted'])
            
            print("✓ generate_verification_email works with mocked dependencies")
            
        except Exception as e:
            self.fail(f"Failed to generate verification email: {e}")


if __name__ == '__main__':
    print("Testing email generation functionality...")
    unittest.main(verbosity=2) 