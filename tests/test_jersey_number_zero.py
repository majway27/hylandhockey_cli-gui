#!/usr/bin/env python3
"""
Test jersey number zero handling
"""

import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from config.config_manager import ConfigManager
from workflow.order.verification import OrderVerification, OrderDetails
from workflow.order.models.jersey_worksheet_jersey_order import JerseyWorksheetJerseyOrder


class TestJerseyNumberZero(unittest.TestCase):
    """Test jersey number zero handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = ConfigManager(test=True)
        self.order_verification = OrderVerification(self.config)
    
    def test_jersey_number_zero_handling(self):
        """Test that jersey numbers 0 and 00 are handled correctly"""
        # Test the problematic line in verification.py
        # jersey_number=order.jersey_number or ''
        
        # Test with jersey number 0
        jersey_number_0 = 0
        result_0 = jersey_number_0 or ''
        print(f"jersey_number_0 = {jersey_number_0}, result = '{result_0}'")
        self.assertEqual(result_0, '')  # This is the bug!
        
        # Test with jersey number 00 (string)
        jersey_number_00 = '00'
        result_00 = jersey_number_00 or ''
        print(f"jersey_number_00 = '{jersey_number_00}', result = '{result_00}'")
        self.assertEqual(result_00, '00')  # This works correctly
        
        # Test with jersey number 0 (string)
        jersey_number_0_str = '0'
        result_0_str = jersey_number_0_str or ''
        print(f"jersey_number_0_str = '{jersey_number_0_str}', result = '{result_0_str}'")
        self.assertEqual(result_0_str, '0')  # This works correctly
    
    def test_fix_jersey_number_zero(self):
        """Test the fix for jersey number zero handling"""
        # Test the corrected approach using str() to handle all cases
        jersey_number_0 = 0
        result_0 = str(jersey_number_0) if jersey_number_0 is not None else ''
        print(f"Fixed: jersey_number_0 = {jersey_number_0}, result = '{result_0}'")
        self.assertEqual(result_0, '0')  # This should work correctly
        
        jersey_number_00 = '00'
        result_00 = str(jersey_number_00) if jersey_number_00 is not None else ''
        print(f"Fixed: jersey_number_00 = '{jersey_number_00}', result = '{result_00}'")
        self.assertEqual(result_00, '00')
        
        jersey_number_none = None
        result_none = str(jersey_number_none) if jersey_number_none is not None else ''
        print(f"Fixed: jersey_number_none = {jersey_number_none}, result = '{result_none}'")
        self.assertEqual(result_none, '')
    
    def test_order_details_with_zero_jersey_numbers(self):
        """Test OrderDetails creation with zero jersey numbers"""
        # Test with integer 0
        order_details_0 = OrderDetails(
            link="https://example.com",
            participant_first_name="John",
            participant_full_name="John Doe",
            jersey_name="Doe",
            jersey_number="0",  # String representation
            jersey_size="M",
            jersey_type="Home",
            sock_size="M",
            sock_type="Black",
            pant_shell_size="M",
            parent1_email="parent@example.com",
            parent2_email="",
            parent3_email="",
            parent4_email="",
            contacted="",
            fitting="",
            confirmed="",
            parent_emails=["parent@example.com"],
            registration_deep_link="https://example.com"
        )
        
        self.assertEqual(order_details_0.jersey_number, "0")
        print(f"OrderDetails with jersey_number '0': {order_details_0.jersey_number}")
        
        # Test with string "00"
        order_details_00 = OrderDetails(
            link="https://example.com",
            participant_first_name="Jane",
            participant_full_name="Jane Smith",
            jersey_name="Smith",
            jersey_number="00",  # String representation
            jersey_size="S",
            jersey_type="Away",
            sock_size="S",
            sock_type="White",
            pant_shell_size="S",
            parent1_email="parent@example.com",
            parent2_email="",
            parent3_email="",
            parent4_email="",
            contacted="",
            fitting="",
            confirmed="",
            parent_emails=["parent@example.com"],
            registration_deep_link="https://example.com"
        )
        
        self.assertEqual(order_details_00.jersey_number, "00")
        print(f"OrderDetails with jersey_number '00': {order_details_00.jersey_number}")
    
    def test_email_template_with_zero_jersey_numbers(self):
        """Test email template formatting with zero jersey numbers"""
        # Create OrderDetails with zero jersey numbers
        order_details = OrderDetails(
            link="https://example.com",
            participant_first_name="John",
            participant_full_name="John Doe",
            jersey_name="Doe",
            jersey_number="0",  # String representation
            jersey_size="M",
            jersey_type="Home",
            sock_size="M",
            sock_type="Black",
            pant_shell_size="M",
            parent1_email="parent@example.com",
            parent2_email="",
            parent3_email="",
            parent4_email="",
            contacted="",
            fitting="",
            confirmed="",
            parent_emails=["parent@example.com"],
            registration_deep_link="https://example.com"
        )
        
        # Test the template formatting
        template_content = "- Jersey #: {jersey_number}"
        formatted_content = template_content.format(jersey_number=order_details.jersey_number)
        
        self.assertEqual(formatted_content, "- Jersey #: 0")
        print(f"Template formatting result: {formatted_content}")


if __name__ == '__main__':
    print("Testing jersey number zero handling...")
    unittest.main(verbosity=2) 