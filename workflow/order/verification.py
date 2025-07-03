"""
This module contains the OrderVerification class, which is used to verify orders and send verification emails.
See WORKFLOW.md for the functional architecture that includes this module.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from config.config_manager import ConfigManager
import message.gmail as notify
from workflow.order.models.jersey_worksheet_jersey_order import JerseyWorksheetJerseyOrder, FieldAwareDateTime


class NoParentEmailError(Exception):
    """Exception raised when no parent email is found for an order."""
    pass

@dataclass
class OrderDetails:
    """Data class for order details."""
    link: str
    participant_first_name: str
    participant_full_name: str
    jersey_name: str
    jersey_number: str
    jersey_size: str
    jersey_type: str
    sock_size: str
    sock_type: str
    pant_shell_size: str
    parent1_email: str
    parent2_email: str
    parent3_email: str
    parent4_email: str
    contacted: str
    fitting: str
    confirmed: str

class OrderVerification:
    def __init__(self, config_manager: ConfigManager):
        """Initialize the OrderVerification class.
        
        Args:
            config_manager: ConfigManager instance for configuration settings
        """
        self.config = config_manager
        self.sender_email = self.config.jersey_sender_email
        self.template_path = Path(__file__).parent / 'templates' / 'verification_email.html'
        self.signature_path = Path(__file__).parent.parent.parent / 'config' / 'email_signature.html'
        
    def _load_template(self) -> str:
        """Load the email template from file.
        
        Returns:
            The template content as a string
        """
        try:
            with open(self.template_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Email template not found at {self.template_path}")
            
    def _load_signature(self) -> str:
        """Load the email signature from file.
        
        Returns:
            The signature content as a string
        """
        try:
            with open(self.signature_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Email signature not found at {self.signature_path}")
    
    def get_pending_orders(self) -> List[OrderDetails]:
        """Get all orders pending verification.
        
        Returns:
            List of OrderDetails objects for orders pending verification
            
        Raises:
            NoParentEmailError: If an order is found with no parent email addresses
        """
        # Get all jersey orders
        jersey_orders = JerseyWorksheetJerseyOrder.all(self.config)
        
        # Filter for orders that need verification (contacted but not confirmed)
        print(f"Found {len(jersey_orders)} possble jersey orders")
        pending_orders = []
        invalid_rows = []
        for idx, order in enumerate(jersey_orders, start=2):  # start=2 because row 1 is header
            # Silently drop the last row if it's the special "Last Jersey Name" row
            if idx == len(jersey_orders) + 1 and order.full_name == 'Last Jersey Name':
                invalid_rows.append(idx)
                continue
                
            # Skip empty or invalid rows
            if not order.first_name or not order.last_name:
                invalid_rows.append(idx)
                continue
                
            # Check if the order has been contacted or confirmed
            # A date value (FieldAwareDateTime or datetime) means it has been contacted/confirmed
            # An empty string or None means it hasn't been contacted/confirmed
            #print(f"Debug - contacted: {order.contacted}")
            is_contacted = isinstance(order.contacted, (FieldAwareDateTime, datetime)) or (isinstance(order.contacted, str) and order.contacted.strip())
            is_confirmed = isinstance(order.confirmed, (FieldAwareDateTime, datetime)) or (isinstance(order.confirmed, str) and order.confirmed.strip())
            
            if not is_contacted and not is_confirmed:
                # Check if any parent email exists
                if not any([order.parent1_email, order.parent2_email, order.parent3_email, order.parent4_email]):
                    print(f"Warning: No parent email found for order: {order.full_name} (row {idx})")
                    continue
                
                #print(f"Debug - raw_link_value for {order.full_name}: {order.raw_link_value}")
                pending_orders.append(OrderDetails(
                    link=order.raw_link_value,
                    participant_first_name=order.first_name,
                    participant_full_name=order.full_name,
                    jersey_name=order.jersey_name or '',
                    jersey_number=order.jersey_number or '',
                    jersey_size=order.jersey_size or '',
                    jersey_type=order.jersey_type or '',
                    sock_size=order.sock_size or '',
                    sock_type=order.sock_type or '',
                    pant_shell_size=order.pant_shell_size or '',
                    parent1_email=order.parent1_email or '',
                    parent2_email=order.parent2_email or '',
                    parent3_email=order.parent3_email or '',
                    parent4_email=order.parent4_email or '',
                    contacted=order.contacted or '',
                    fitting=order.fitting or '',
                    confirmed=order.confirmed or ''
                ))
        
        if invalid_rows:
            print(f"Skipping invalid rows: {', '.join(map(str, invalid_rows))}")
        
        return pending_orders
    
    def get_next_pending_order(self) -> Optional[OrderDetails]:
        """Get the next order pending verification.
        
        Returns:
            OrderDetails object for the next order to verify, or None if no pending orders
        """
        pending_orders = self.get_pending_orders()
        return pending_orders[0] if pending_orders else None
    
    def build_notification_template(self, order: OrderDetails) -> str:
        """Generate the verification email content based on the template.
        
        Args:
            order: OrderDetails object containing the order information
            
        Returns:
            Formatted email content as a string
        """
        template = self._load_template()
        signature = self._load_signature()
        return template.format(
            participant_first_name=order.participant_first_name,
            jersey_name=order.jersey_name,
            jersey_number=order.jersey_number,
            jersey_size=order.jersey_size,
            jersey_type=order.jersey_type,
            sock_size=order.sock_size,
            sock_type=order.sock_type,
            pant_shell_size=order.pant_shell_size,
            link=order.link,
            signature=signature
        )
    
    def create_verification_gmail_draft(self, order: OrderDetails) -> str:
        """Create a Gmail draft with the verification email.
        
        Args:
            order: OrderDetails object containing the order information
            
        Returns:
            Draft ID of the created draft
        """
        email_content = self.build_notification_template(order)
        
        # Get all available parent emails
        parent_emails = [
            email for email in [
                order.parent1_email,
                order.parent2_email,
                order.parent3_email,
                order.parent4_email
            ] if email
        ]
        
        if not parent_emails:
            raise NoParentEmailError(f"No parent email found for order: {order.participant_full_name}")
        
        # Join all parent emails with commas
        to_email = ", ".join(parent_emails)
        
        draft = notify.create_gmail_draft(
            sender_email=self.sender_email,
            to_email=to_email,
            subject=f"{order.participant_full_name} Uniform Order Confirmation",
            message_text=email_content,
            config_manager=self.config
        )
        
        return draft['id'] if draft else None
    
    def generate_verification_email(self, order: OrderDetails) -> str:
        """Generate a verification email for an order and update the contacted status.
        
        Args:
            order: OrderDetails object containing the order information
            
        Returns:
            Draft ID of the created draft
            
        Raises:
            NoParentEmailError: If no parent email is found for the order
            Exception: If there is an error creating the draft or updating the sheet
        """
        try:
            # Step 1: Create the Gmail draft
            draft_id = self.create_verification_gmail_draft(order)
            if not draft_id:
                raise Exception("Failed to create Gmail draft")
            
            # Step 2: Update the contacted field in the Google Sheet
            # Find the order in the sheet
            jersey_orders = JerseyWorksheetJerseyOrder.all(self.config)
            order_found = False
            for jersey_order in jersey_orders:
                if jersey_order.full_name == order.participant_full_name:
                    # Update the contacted field with today's date in mm/dd format
                    jersey_order.contacted = FieldAwareDateTime(datetime.now().year, datetime.now().month, datetime.now().day, field_name='contacted')
                    jersey_order.save(fields_to_update=['contacted'])
                    order_found = True
                    break
            
            if not order_found:
                raise Exception(f"Could not find order for {order.participant_full_name} in the sheet")
            
            return draft_id
            
        except NoParentEmailError as e:
            # Re-raise NoParentEmailError as it's a specific error we want to handle separately
            raise
        except Exception as e:
            # Log the error and re-raise with more context
            print(f"Error generating verification email: {str(e)}")
            raise Exception(f"Failed to generate verification email: {str(e)}")