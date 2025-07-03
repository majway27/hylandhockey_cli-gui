#!/usr/bin/env python3
"""
Hyland Hockey Jersey Order Management System
Main GUI Application

This application replaces the Jupyter notebook interface with a modern
Tkinter + ttkbootstrap GUI for managing hockey jersey orders.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame

from config.config_manager import ConfigManager
from workflow.order.verification import OrderVerification, OrderDetails


class HockeyJerseyApp:
    """Main application class for the Hockey Jersey Order Management System."""
    
    def __init__(self):
        """Initialize the main application window."""
        self.root = ttk.Window(
            title="Hyland Hockey Jersey Order Management",
            themename="cosmo",
            size=(1200, 800),
            resizable=(True, True)
        )
        
        # Initialize configuration
        self.config = ConfigManager(test=True)
        self.order_verification = OrderVerification(self.config)
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main user interface."""
        # Create main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=X, pady=(0, 20))
        
        title_label = ttk.Label(
            header_frame, 
            text="Hyland Hockey Jersey Order Management",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=SUNKEN,
            anchor=W
        )
        status_bar.pack(side=BOTTOM, fill=X, pady=(10, 0))
        
        # Main content area
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=BOTH, expand=True)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_orders_tab()
        self.create_email_tab()
        self.create_config_tab()
        
    def create_dashboard_tab(self):
        """Create the main dashboard tab."""
        dashboard_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Dashboard content
        welcome_label = ttk.Label(
            dashboard_frame,
            text="Welcome to the Jersey Order Management System",
            font=("Helvetica", 12)
        )
        welcome_label.pack(pady=20)
        
        # Quick stats frame
        stats_frame = ttk.LabelFrame(dashboard_frame, text="Quick Statistics", padding=10)
        stats_frame.pack(fill=X, pady=10)
        
        # Stats will be populated here
        self.pending_orders_var = tk.StringVar(value="Loading...")
        self.total_orders_var = tk.StringVar(value="Loading...")
        
        ttk.Label(stats_frame, text="Pending Orders:").grid(row=0, column=0, sticky=W, padx=(0, 10))
        ttk.Label(stats_frame, textvariable=self.pending_orders_var).grid(row=0, column=1, sticky=W)
        
        ttk.Label(stats_frame, text="Total Orders:").grid(row=1, column=0, sticky=W, padx=(0, 10))
        ttk.Label(stats_frame, textvariable=self.total_orders_var).grid(row=1, column=1, sticky=W)
        
        # Refresh button
        refresh_btn = ttk.Button(
            dashboard_frame,
            text="Refresh Dashboard",
            command=self.refresh_dashboard,
            style="primary.TButton"
        )
        refresh_btn.pack(pady=20)
        
        # Initial load
        self.refresh_dashboard()
        
    def create_orders_tab(self):
        """Create the orders management tab."""
        orders_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(orders_frame, text="Orders")
        
        # Orders toolbar
        toolbar_frame = ttk.Frame(orders_frame)
        toolbar_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Button(
            toolbar_frame,
            text="Refresh Orders",
            command=self.refresh_orders,
            style="info.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(
            toolbar_frame,
            text="Get Next Order",
            command=self.get_next_order,
            style="success.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
        # Orders table
        table_frame = ttk.Frame(orders_frame)
        table_frame.pack(fill=BOTH, expand=True)
        
        # Create Treeview for orders
        columns = (
            'name', 'jersey_name', 'jersey_number', 'jersey_size', 
            'jersey_type', 'contacted', 'confirmed'
        )
        
        self.orders_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            height=15
        )
        
        # Define headings
        self.orders_tree.heading('name', text='Participant Name')
        self.orders_tree.heading('jersey_name', text='Jersey Name')
        self.orders_tree.heading('jersey_number', text='Number')
        self.orders_tree.heading('jersey_size', text='Size')
        self.orders_tree.heading('jersey_type', text='Type')
        self.orders_tree.heading('contacted', text='Contacted')
        self.orders_tree.heading('confirmed', text='Confirmed')
        
        # Define columns
        self.orders_tree.column('name', width=150)
        self.orders_tree.column('jersey_name', width=120)
        self.orders_tree.column('jersey_number', width=80)
        self.orders_tree.column('jersey_size', width=80)
        self.orders_tree.column('jersey_type', width=100)
        self.orders_tree.column('contacted', width=100)
        self.orders_tree.column('confirmed', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.orders_tree.yview)
        self.orders_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.orders_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Bind selection event
        self.orders_tree.bind('<<TreeviewSelect>>', self.on_order_select)
        
        # Order details frame
        details_frame = ttk.LabelFrame(orders_frame, text="Order Details", padding=10)
        details_frame.pack(fill=X, pady=(10, 0))
        
        self.details_text = tk.Text(details_frame, height=8, wrap=tk.WORD)
        self.details_text.pack(fill=X)
        
        # Initial load
        self.refresh_orders()
        
    def create_email_tab(self):
        """Create the email management tab."""
        email_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(email_frame, text="Email")
        
        # Email composition area
        compose_frame = ttk.LabelFrame(email_frame, text="Email Composition", padding=10)
        compose_frame.pack(fill=BOTH, expand=True)
        
        # Recipient info
        recipient_frame = ttk.Frame(compose_frame)
        recipient_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(recipient_frame, text="To:").pack(side=LEFT)
        self.recipient_var = tk.StringVar()
        recipient_entry = ttk.Entry(recipient_frame, textvariable=self.recipient_var, width=50)
        recipient_entry.pack(side=LEFT, padx=(10, 0))
        
        # Subject
        subject_frame = ttk.Frame(compose_frame)
        subject_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(subject_frame, text="Subject:").pack(side=LEFT)
        self.subject_var = tk.StringVar()
        subject_entry = ttk.Entry(subject_frame, textvariable=self.subject_var, width=50)
        subject_entry.pack(side=LEFT, padx=(10, 0))
        
        # Email content
        content_frame = ttk.Frame(compose_frame)
        content_frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(content_frame, text="Content:").pack(anchor=W)
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill=BOTH, expand=True, pady=(5, 0))
        
        self.email_text = tk.Text(text_frame, wrap=tk.WORD)
        email_scrollbar = ttk.Scrollbar(text_frame, orient=VERTICAL, command=self.email_text.yview)
        self.email_text.configure(yscrollcommand=email_scrollbar.set)
        
        self.email_text.pack(side=LEFT, fill=BOTH, expand=True)
        email_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Email buttons
        button_frame = ttk.Frame(compose_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Generate Draft",
            command=self.generate_email_draft,
            style="primary.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Clear",
            command=self.clear_email_form,
            style="secondary.TButton"
        ).pack(side=LEFT)
        
    def create_config_tab(self):
        """Create the configuration management tab."""
        config_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(config_frame, text="Configuration")
        
        # Config info
        info_frame = ttk.LabelFrame(config_frame, text="Configuration Information", padding=10)
        info_frame.pack(fill=X, pady=(0, 20))
        
        # Test mode indicator
        test_mode = "Test Mode" if self.config.is_test_mode else "Production Mode"
        mode_label = ttk.Label(
            info_frame,
            text=f"Mode: {test_mode}",
            font=("Helvetica", 10, "bold")
        )
        mode_label.pack(anchor=W)
        
        # Spreadsheet info
        spreadsheet_frame = ttk.LabelFrame(config_frame, text="Spreadsheet Configuration", padding=10)
        spreadsheet_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Label(spreadsheet_frame, text=f"Jersey Spreadsheet: {self.config.jersey_spreadsheet_name}").pack(anchor=W)
        ttk.Label(spreadsheet_frame, text=f"Sender Email: {self.config.jersey_sender_email}").pack(anchor=W)
        
        # Actions
        actions_frame = ttk.LabelFrame(config_frame, text="Actions", padding=10)
        actions_frame.pack(fill=X)
        
        ttk.Button(
            actions_frame,
            text="Test Connection",
            command=self.test_connection,
            style="info.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
    def refresh_dashboard(self):
        """Refresh the dashboard statistics."""
        try:
            self.status_var.set("Loading dashboard...")
            self.root.update()
            
            # Get pending orders
            pending_orders = self.order_verification.get_pending_orders()
            self.pending_orders_var.set(str(len(pending_orders)))
            
            # Get total orders (this would need to be implemented)
            # For now, just show pending count
            self.total_orders_var.set(str(len(pending_orders)))
            
            self.status_var.set("Dashboard refreshed successfully")
            
        except Exception as e:
            self.status_var.set(f"Error refreshing dashboard: {str(e)}")
            
    def refresh_orders(self):
        """Refresh the orders table."""
        try:
            self.status_var.set("Loading orders...")
            self.root.update()
            
            # Clear existing items
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)
            
            # Get pending orders
            pending_orders = self.order_verification.get_pending_orders()
            
            # Add to treeview
            for order in pending_orders:
                contacted_status = "Yes" if order.contacted else "No"
                confirmed_status = "Yes" if order.confirmed else "No"
                
                self.orders_tree.insert('', END, values=(
                    order.participant_full_name,
                    order.jersey_name,
                    order.jersey_number,
                    order.jersey_size,
                    order.jersey_type,
                    contacted_status,
                    confirmed_status
                ))
            
            self.status_var.set(f"Loaded {len(pending_orders)} pending orders")
            
        except Exception as e:
            self.status_var.set(f"Error loading orders: {str(e)}")
            
    def get_next_order(self):
        """Get the next pending order and populate email form."""
        try:
            self.status_var.set("Getting next order...")
            self.root.update()
            
            next_order = self.order_verification.get_next_pending_order()
            if next_order:
                self.populate_email_form(next_order)
                self.status_var.set(f"Loaded order for {next_order.participant_full_name}")
            else:
                self.status_var.set("No pending orders found")
                
        except Exception as e:
            self.status_var.set(f"Error getting next order: {str(e)}")
            
    def on_order_select(self, event):
        """Handle order selection in the treeview."""
        selection = self.orders_tree.selection()
        if selection:
            # Get the selected item
            item = self.orders_tree.item(selection[0])
            values = item['values']
            
            # Display details
            details = f"Participant: {values[0]}\n"
            details += f"Jersey Name: {values[1]}\n"
            details += f"Jersey Number: {values[2]}\n"
            details += f"Jersey Size: {values[3]}\n"
            details += f"Jersey Type: {values[4]}\n"
            details += f"Contacted: {values[5]}\n"
            details += f"Confirmed: {values[6]}\n"
            
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, details)
            
    def populate_email_form(self, order: OrderDetails):
        """Populate the email form with order details."""
        # Set recipient (use first available parent email)
        parent_emails = [
            email for email in [
                order.parent1_email,
                order.parent2_email,
                order.parent3_email,
                order.parent4_email
            ] if email
        ]
        
        if parent_emails:
            self.recipient_var.set(parent_emails[0])
        
        # Set subject
        self.subject_var.set(f"Good morning, here is what you ordered for {order.participant_first_name} during registration:")
        
        # Generate email content
        try:
            email_content = self.order_verification.build_notification_template(order)
            self.email_text.delete(1.0, tk.END)
            self.email_text.insert(1.0, email_content)
        except Exception as e:
            self.status_var.set(f"Error generating email content: {str(e)}")
            
    def generate_email_draft(self):
        """Generate a Gmail draft with the current email content."""
        try:
            self.status_var.set("Generating Gmail draft...")
            self.root.update()
            
            # This would need to be implemented to work with the current order
            # For now, just show a message
            self.status_var.set("Gmail draft generation not yet implemented")
            
        except Exception as e:
            self.status_var.set(f"Error generating draft: {str(e)}")
            
    def clear_email_form(self):
        """Clear the email form."""
        self.recipient_var.set("")
        self.subject_var.set("")
        self.email_text.delete(1.0, tk.END)
        self.status_var.set("Email form cleared")
        
    def test_connection(self):
        """Test the connection to Google services."""
        try:
            self.status_var.set("Testing connections...")
            self.root.update()
            
            # Test getting orders
            orders = self.order_verification.get_pending_orders()
            
            self.status_var.set(f"Connection test successful - {len(orders)} orders found")
            
        except Exception as e:
            self.status_var.set(f"Connection test failed: {str(e)}")
            
    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Main entry point for the application."""
    app = HockeyJerseyApp()
    app.run()


if __name__ == "__main__":
    main() 