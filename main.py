#!/usr/bin/env python3
"""
Registrar Operations Center System
Main GUI Application

This application replaces the Jupyter notebook interface with a modern
Tkinter + ttkbootstrap GUI for managing youth hockey registrations and jersey orders.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
import argparse
import sys

from config.config_manager import ConfigManager
from config.logging_config import setup_logging, get_logger
from workflow.order.verification import OrderVerification, OrderDetails
from utils.log_viewer import LogViewer
from auth.google_auth import (
    get_credentials_with_retry, 
    check_credentials_status, 
    clear_credentials,
    AuthenticationError,
    TokenExpiredError,
    CredentialsNotFoundError
)

# Setup logging
logger = get_logger(__name__)


class HockeyJerseyApp:
    """Main application class for the Registrar Operations Center System."""
    
    def __init__(self, test_mode: bool = False):
        """
        Initialize the main application window.
        
        Args:
            test_mode: If True, use test configuration and credentials
        """
        logger.info(f"Initializing Registrar Operations Center application (test_mode: {test_mode})")
        
        # Initialize configuration first to get organization name
        logger.debug(f"Initializing configuration manager (test_mode: {test_mode})")
        self.config = ConfigManager(test=test_mode)
        
        # Set title based on mode and organization name
        title = f"Registrar Operations Center: {self.config.organization_name}"
        if test_mode:
            title += " (TEST MODE)"
        else:
            title += " (PRODUCTION)"
            
        self.root = ttk.Window(
            title=title,
            themename="cosmo",
            size=(1200, 800),
            resizable=(True, True)
        )
        
        self.order_verification = OrderVerification(self.config)
        
        # Initialize log viewer in quiet mode (no STDOUT output)
        self.log_viewer = LogViewer(quiet=True)
        
        # Setup UI
        logger.debug("Setting up user interface")
        self.setup_ui()
        
        # Check authentication status (after UI is set up)
        self.check_auth_status()
        
        logger.info("Application initialization completed")
        
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
            text=f"Registrar Operations Center: {self.config.organization_name}",
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
        self.create_logs_tab()
        
        # Update dashboard tab text to reflect initial mode
        self.update_dashboard_tab_text()
        
    def create_dashboard_tab(self):
        """Create the main dashboard tab."""
        dashboard_frame = ttk.Frame(self.notebook, padding=10)
        # Store reference to dashboard frame for tab text updates
        self.dashboard_frame = dashboard_frame
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Dashboard content
        mode_text = "TEST MODE" if self.config.is_test_mode else "PRODUCTION MODE"
        welcome_label = ttk.Label(
            dashboard_frame,
            text=f"Welcome to the Registrar Operations System",
            font=("Helvetica", 12)
        )
        welcome_label.pack(pady=(20, 5))
        
        # Store reference to mode label for updating
        self.mode_label = ttk.Label(
            dashboard_frame,
            text=f"Running in: {mode_text}",
            font=("Helvetica", 10, "bold"),
            foreground="red" if self.config.is_test_mode else "green"
        )
        self.mode_label.pack(pady=(0, 20))
        
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
        
        # Action buttons frame
        actions_frame = ttk.Frame(dashboard_frame)
        actions_frame.pack(pady=20)
        
        # Refresh button
        refresh_btn = ttk.Button(
            actions_frame,
            text="Refresh Dashboard",
            command=self.refresh_dashboard,
            style="primary.TButton"
        )
        refresh_btn.pack(side=LEFT, padx=(0, 10))
        
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
        
        # Environment Mode Section
        mode_frame = ttk.LabelFrame(config_frame, text="Environment Mode", padding=10)
        mode_frame.pack(fill=X, pady=(0, 20))
        
        # Mode selection
        mode_selection_frame = ttk.Frame(mode_frame)
        mode_selection_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(mode_selection_frame, text="Current Mode:").pack(side=LEFT)
        
        # Mode variable and radio buttons
        self.mode_var = tk.StringVar(value="test" if self.config.is_test_mode else "production")
        
        test_radio = ttk.Radiobutton(
            mode_selection_frame,
            text="Test Mode",
            variable=self.mode_var,
            value="test",
            command=self.on_mode_change
        )
        test_radio.pack(side=LEFT, padx=(10, 20))
        
        prod_radio = ttk.Radiobutton(
            mode_selection_frame,
            text="Production Mode",
            variable=self.mode_var,
            value="production",
            command=self.on_mode_change
        )
        prod_radio.pack(side=LEFT)
        
        # Mode description
        self.mode_description_var = tk.StringVar()
        self.update_mode_description()
        mode_desc_label = ttk.Label(
            mode_frame,
            textvariable=self.mode_description_var,
            font=("Helvetica", 9),
            foreground="gray"
        )
        mode_desc_label.pack(anchor=W)
        
        # Mode warning
        if not self.config.is_test_mode:
            warning_label = ttk.Label(
                mode_frame,
                text="⚠️  WARNING: You are in PRODUCTION mode. Changes will affect live data.",
                font=("Helvetica", 9, "bold"),
                foreground="red"
            )
            warning_label.pack(anchor=W, pady=(5, 0))
        
        # Config info
        info_frame = ttk.LabelFrame(config_frame, text="Configuration Information", padding=10)
        info_frame.pack(fill=X, pady=(0, 20))
        
        # Current configuration display
        self.config_info_var = tk.StringVar()
        self.update_config_info()
        config_info_label = ttk.Label(
            info_frame,
            textvariable=self.config_info_var,
            font=("Consolas", 9),
            justify=tk.LEFT
        )
        config_info_label.pack(anchor=W)
        
        # Spreadsheet info
        spreadsheet_frame = ttk.LabelFrame(config_frame, text="Spreadsheet Configuration", padding=10)
        spreadsheet_frame.pack(fill=X, pady=(0, 20))
        
        self.spreadsheet_info_var = tk.StringVar()
        self.update_spreadsheet_info()
        spreadsheet_info_label = ttk.Label(
            spreadsheet_frame,
            textvariable=self.spreadsheet_info_var,
            font=("Consolas", 9),
            justify=tk.LEFT
        )
        spreadsheet_info_label.pack(anchor=W)
        
        # Authentication Section
        auth_frame = ttk.LabelFrame(config_frame, text="Authentication", padding=10)
        auth_frame.pack(fill=X, pady=(0, 20))
        
        auth_buttons_frame = ttk.Frame(auth_frame)
        auth_buttons_frame.pack()
        
        ttk.Button(
            auth_buttons_frame,
            text="Check Auth Status",
            command=self.check_auth_status,
            style="info.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(
            auth_buttons_frame,
            text="Authenticate",
            command=self.authenticate_user,
            style="success.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(
            auth_buttons_frame,
            text="Clear Tokens",
            command=self.clear_auth_tokens,
            style="danger.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(
            auth_buttons_frame,
            text="Test Connection",
            command=self.test_connection,
            style="warning.TButton"
        ).pack(side=LEFT)
        
        # Actions
        actions_frame = ttk.LabelFrame(config_frame, text="Actions", padding=10)
        actions_frame.pack(fill=X)
        
        ttk.Button(
            actions_frame,
            text="Refresh Configuration",
            command=self.refresh_config_tab,
            style="info.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
    def create_logs_tab(self):
        """Create the logs viewing tab."""
        logs_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(logs_frame, text="Logs")
        
        # Initialize log viewer
        self.log_viewer = LogViewer("logs")
        
        # Top controls frame
        controls_frame = ttk.Frame(logs_frame)
        controls_frame.pack(fill=X, pady=(0, 10))
        
        # Log file selection
        file_frame = ttk.Frame(controls_frame)
        file_frame.pack(side=LEFT, fill=X, expand=True)
        
        ttk.Label(file_frame, text="Log File:").pack(side=LEFT)
        self.log_file_var = tk.StringVar()
        self.log_file_combo = ttk.Combobox(
            file_frame, 
            textvariable=self.log_file_var,
            width=30,
            state="readonly"
        )
        self.log_file_combo.pack(side=LEFT, padx=(10, 0))
        
        # Filter controls
        filter_frame = ttk.Frame(controls_frame)
        filter_frame.pack(side=LEFT, padx=(20, 0))
        
        ttk.Label(filter_frame, text="Level:").pack(side=LEFT)
        self.log_level_var = tk.StringVar(value="ALL")
        level_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.log_level_var,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            width=10,
            state="readonly"
        )
        level_combo.pack(side=LEFT, padx=(10, 0))
        
        ttk.Label(filter_frame, text="Search:").pack(side=LEFT, padx=(20, 0))
        self.log_search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.log_search_var, width=20)
        search_entry.pack(side=LEFT, padx=(10, 0))
        
        # Action buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(side=RIGHT)
        
        ttk.Button(
            button_frame,
            text="Refresh",
            command=self.refresh_logs,
            style="info.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Clear Filters",
            command=self.clear_log_filters,
            style="secondary.TButton"
        ).pack(side=LEFT)
        
        # Log display area
        display_frame = ttk.Frame(logs_frame)
        display_frame.pack(fill=BOTH, expand=True)
        
        # Log text widget with scrollbars
        text_frame = ttk.Frame(display_frame)
        text_frame.pack(fill=BOTH, expand=True)
        
        # Create text widget with both scrollbars
        self.log_text = tk.Text(
            text_frame,
            wrap=tk.NONE,
            font=("Consolas", 9),
            bg="#f8f9fa",
            fg="#212529"
        )
        
        # Configure color tags for log levels
        self.log_text.tag_configure("error", foreground="#dc3545", background="#f8d7da")
        self.log_text.tag_configure("warning", foreground="#856404", background="#fff3cd")
        self.log_text.tag_configure("critical", foreground="#721c24", background="#f5c6cb")
        self.log_text.tag_configure("info", foreground="#0c5460", background="#d1ecf1")
        self.log_text.tag_configure("debug", foreground="#6c757d", background="#e2e3e5")
        
        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(text_frame, orient=VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=v_scrollbar.set)
        
        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(text_frame, orient=HORIZONTAL, command=self.log_text.xview)
        self.log_text.configure(xscrollcommand=h_scrollbar.set)
        
        # Pack widgets
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        
        # Status frame
        status_frame = ttk.Frame(logs_frame)
        status_frame.pack(fill=X, pady=(10, 0))
        
        self.log_status_var = tk.StringVar(value="Ready")
        log_status_label = ttk.Label(
            status_frame,
            textvariable=self.log_status_var,
            relief=SUNKEN,
            anchor=W
        )
        log_status_label.pack(fill=X)
        
        # Initialize log files list
        self.refresh_log_files()
        
        # Bind events for automatic refresh
        self.log_file_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_logs())
        level_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_logs())
        search_entry.bind('<KeyRelease>', self.on_search_change)
        
        # Load initial log content
        self.refresh_logs()
        
    def update_dashboard_mode_label(self):
        """Update the dashboard mode label to reflect current mode."""
        mode_text = "TEST MODE" if self.config.is_test_mode else "PRODUCTION MODE"
        self.mode_label.config(
            text=f"Running in: {mode_text}",
            foreground="red" if self.config.is_test_mode else "green"
        )
    
    def update_dashboard_tab_text(self):
        """Update the dashboard tab header text to reflect current mode."""
        # Find the tab index for the dashboard frame
        for i in range(self.notebook.index('end')):
            if self.notebook.winfo_children()[i] == self.dashboard_frame:
                # Update the tab text to include mode information
                tab_text = f"Dashboard: {self.config.organization_name}"
                if self.config.is_test_mode:
                    tab_text += " (TEST)"
                else:
                    tab_text += " (PROD)"
                self.notebook.tab(i, text=tab_text)
                break
    
    def refresh_dashboard(self):
        """Refresh the dashboard statistics."""
        logger.info("Refreshing dashboard")
        try:
            self.status_var.set("Loading dashboard...")
            self.root.update()
            
            # Update mode label
            self.update_dashboard_mode_label()
            self.update_dashboard_tab_text()
            
            # Get pending orders
            pending_orders = self.order_verification.get_pending_orders()
            self.pending_orders_var.set(str(len(pending_orders)))
            
            # Get total orders (this would need to be implemented)
            # For now, just show pending count
            self.total_orders_var.set(str(len(pending_orders)))
            
            self.status_var.set("Dashboard refreshed successfully")
            logger.info(f"Dashboard refreshed successfully: {len(pending_orders)} pending orders")
            
        except TokenExpiredError as e:
            error_msg = f"Authentication expired: {str(e)}"
            logger.error(error_msg)
            self.status_var.set(error_msg)
            self.pending_orders_var.set("Auth Error")
            self.total_orders_var.set("Auth Error")
        except AuthenticationError as e:
            error_msg = f"Authentication error: {str(e)}"
            logger.error(error_msg)
            self.status_var.set(error_msg)
            self.pending_orders_var.set("Auth Error")
            self.total_orders_var.set("Auth Error")
        except Exception as e:
            error_msg = f"Error refreshing dashboard: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status_var.set(error_msg)
            self.pending_orders_var.set("Error")
            self.total_orders_var.set("Error")
            
    def refresh_orders(self):
        """Refresh the orders table."""
        logger.info("Refreshing orders table")
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
            logger.info(f"Orders table refreshed successfully: {len(pending_orders)} orders loaded")
            
        except TokenExpiredError as e:
            error_msg = f"Authentication expired: {str(e)}"
            logger.error(error_msg)
            self.status_var.set(error_msg)
        except AuthenticationError as e:
            error_msg = f"Authentication error: {str(e)}"
            logger.error(error_msg)
            self.status_var.set(error_msg)
        except Exception as e:
            error_msg = f"Error loading orders: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status_var.set(error_msg)
            
    def get_next_order(self):
        """Get the next pending order and populate email form."""
        logger.info("Getting next pending order")
        try:
            self.status_var.set("Getting next order...")
            self.root.update()
            
            next_order = self.order_verification.get_next_pending_order()
            if next_order:
                self.populate_email_form(next_order)
                self.status_var.set(f"Loaded order for {next_order.participant_full_name}")
                logger.info(f"Loaded next order for {next_order.participant_full_name}")
            else:
                self.status_var.set("No pending orders found")
                logger.info("No pending orders found")
                
        except TokenExpiredError as e:
            error_msg = f"Authentication expired: {str(e)}"
            logger.error(error_msg)
            self.status_var.set(error_msg)
        except AuthenticationError as e:
            error_msg = f"Authentication error: {str(e)}"
            logger.error(error_msg)
            self.status_var.set(error_msg)
        except Exception as e:
            error_msg = f"Error getting next order: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status_var.set(error_msg)
            
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
        
    def check_auth_status(self):
        """Check authentication status and update UI accordingly."""
        try:
            is_valid, status_message = check_credentials_status(self.config)
            if not is_valid:
                logger.warning(f"Authentication issue detected: {status_message}")
                self.status_var.set(f"Auth Issue: {status_message}")
            else:
                logger.info("Authentication status: Valid")
                self.status_var.set("Ready")
        except Exception as e:
            logger.error(f"Error checking authentication status: {e}")
            self.status_var.set(f"Auth Error: {str(e)}")
    
    def authenticate_user(self):
        """Authenticate user with Google OAuth."""
        try:
            self.status_var.set("Authenticating with Google...")
            self.root.update()
            
            # This will trigger the OAuth flow
            get_credentials_with_retry(self.config)
            
            self.status_var.set("Authentication successful!")
            logger.info("User authenticated successfully")
            
            # Refresh the dashboard to show data
            self.refresh_dashboard()
            
        except TokenExpiredError as e:
            error_msg = f"Authentication failed: {str(e)}"
            logger.error(error_msg)
            self.status_var.set(error_msg)
        except CredentialsNotFoundError as e:
            error_msg = f"Credentials not found: {str(e)}"
            logger.error(error_msg)
            self.status_var.set(error_msg)
        except AuthenticationError as e:
            error_msg = f"Authentication error: {str(e)}"
            logger.error(error_msg)
            self.status_var.set(error_msg)
        except Exception as e:
            error_msg = f"Unexpected authentication error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status_var.set(error_msg)
    
    def clear_auth_tokens(self):
        """Clear stored authentication tokens."""
        try:
            self.status_var.set("Clearing authentication tokens...")
            self.root.update()
            
            success = clear_credentials(self.config)
            if success:
                self.status_var.set("Authentication tokens cleared. Please re-authenticate.")
                logger.info("Authentication tokens cleared successfully")
            else:
                self.status_var.set("Failed to clear authentication tokens.")
                logger.error("Failed to clear authentication tokens")
                
        except Exception as e:
            error_msg = f"Error clearing tokens: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status_var.set(error_msg)
    
    def on_mode_change(self):
        """Handle mode change from radio buttons."""
        new_mode = self.mode_var.get() == "test"
        if new_mode != self.config.is_test_mode:
            logger.info(f"User requested mode change to {'test' if new_mode else 'production'}")
            
            # Show confirmation dialog
            from tkinter import messagebox
            mode_text = "TEST" if new_mode else "PRODUCTION"
            result = messagebox.askyesno(
                "Confirm Mode Change",
                f"Are you sure you want to switch to {mode_text} mode?\n\n"
                f"This will:\n"
                f"• Use {'test' if new_mode else 'production'} credentials\n"
                f"• Use {'test' if new_mode else 'production'} configuration\n"
                f"• Require re-authentication\n\n"
                f"Continue?"
            )
            
            if result:
                self.switch_mode(new_mode)
            else:
                # Revert the radio button selection
                self.mode_var.set("test" if self.config.is_test_mode else "production")
    
    def switch_mode(self, test_mode: bool):
        """Switch between test and production modes."""
        try:
            logger.info(f"Switching to {'test' if test_mode else 'production'} mode")
            self.status_var.set(f"Switching to {'test' if test_mode else 'production'} mode...")
            self.root.update()
            
            # Update the configuration
            self.config.set_test_mode(test_mode)
            
            # Update the application title
            title = f"Registrar Operations Center: {self.config.organization_name}"
            if test_mode:
                title += " (TEST MODE)"
            else:
                title += " (PRODUCTION)"
            self.root.title(title)
            
            # Check if credentials for the new mode are valid before clearing
            try:
                is_valid, status_message = check_credentials_status(self.config)
                if is_valid:
                    logger.info(f"Credentials for {'test' if test_mode else 'production'} mode are valid, preserving them")
                    # Don't clear valid credentials
                    credentials_cleared = False
                else:
                    logger.info(f"Credentials for {'test' if test_mode else 'production'} mode are invalid: {status_message}")
                    # Clear invalid credentials
                    clear_credentials(self.config)
                    credentials_cleared = True
            except Exception as e:
                logger.warning(f"Error checking credentials status: {e}, clearing credentials as precaution")
                clear_credentials(self.config)
                credentials_cleared = True
            
            # Update configuration tab
            self.update_mode_description()
            self.update_config_info()
            self.update_spreadsheet_info()
            
            # Update dashboard mode indicator and tab text
            self.refresh_dashboard()
            self.update_dashboard_tab_text()
            
            self.status_var.set(f"Switched to {'test' if test_mode else 'production'} mode successfully")
            
            # Show success message
            from tkinter import messagebox
            if credentials_cleared:
                messagebox.showinfo(
                    "Mode Changed",
                    f"Successfully switched to {'TEST' if test_mode else 'PRODUCTION'} mode.\n\n"
                    f"Please re-authenticate using the Dashboard tab."
                )
            else:
                messagebox.showinfo(
                    "Mode Changed",
                    f"Successfully switched to {'TEST' if test_mode else 'PRODUCTION'} mode.\n\n"
                    f"Your existing authentication is still valid."
                )
            
        except Exception as e:
            error_msg = f"Failed to switch modes: {e}"
            logger.error(error_msg)
            self.status_var.set("Mode switch failed")
            
            # Show error message
            from tkinter import messagebox
            messagebox.showerror("Mode Switch Failed", error_msg)
            
            # Revert the radio button selection
            self.mode_var.set("test" if self.config.is_test_mode else "production")
    
    def update_mode_description(self):
        """Update the mode description text."""
        if self.config.is_test_mode:
            self.mode_description_var.set(
                "Test Mode: Uses test credentials and configuration. Safe for development and testing."
            )
        else:
            self.mode_description_var.set(
                "Production Mode: Uses production credentials and configuration. Changes affect live data."
            )
    
    def update_config_info(self):
        """Update the configuration information display."""
        info = f"Mode: {'TEST' if self.config.is_test_mode else 'PRODUCTION'}\n"
        info += f"Credentials File: credentials{'test' if self.config.is_test_mode else ''}.json\n"
        info += f"Token File: token{'test' if self.config.is_test_mode else ''}.pickle\n"
        info += f"Config File: config.yaml\n"
        info += f"Preferences File: preferences.yaml"
        
        self.config_info_var.set(info)
    
    def update_spreadsheet_info(self):
        """Update the spreadsheet information display."""
        try:
            info = f"Spreadsheet Name: {self.config.jersey_spreadsheet_name}\n"
            info += f"Spreadsheet ID: {self.config.jersey_spreadsheet_id}\n"
            info += f"Worksheet Name: {self.config.jersey_worksheet_jersey_orders_name}\n"
            info += f"Worksheet GID: {self.config.jersey_worksheet_jersey_orders_gid}\n"
            info += f"Sender Email: {self.config.jersey_sender_email}\n"
            info += f"Default To Email: {self.config.jersey_default_to_email}"
        except Exception as e:
            info = f"Error loading configuration: {e}"
        
        self.spreadsheet_info_var.set(info)
    
    def refresh_config_tab(self):
        """Refresh the configuration tab display."""
        logger.info("Refreshing configuration tab")
        self.update_mode_description()
        self.update_config_info()
        self.update_spreadsheet_info()
        self.status_var.set("Configuration refreshed")
    
    def test_connection(self):
        """Test the connection to Google services."""
        logger.info("Testing Google services connection")
        try:
            self.status_var.set("Testing connections...")
            self.root.update()
            
            # Test getting orders
            orders = self.order_verification.get_pending_orders()
            
            self.status_var.set(f"Connection test successful - {len(orders)} orders found")
            logger.info(f"Connection test successful - {len(orders)} orders found")
            
        except TokenExpiredError as e:
            error_msg = f"Authentication expired: {str(e)}"
            logger.error(error_msg)
            self.status_var.set(error_msg)
        except AuthenticationError as e:
            error_msg = f"Authentication error: {str(e)}"
            logger.error(error_msg)
            self.status_var.set(error_msg)
        except Exception as e:
            error_msg = f"Connection test failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status_var.set(error_msg)
            
    def refresh_log_files(self):
        """Refresh the list of available log files."""
        try:
            log_files = self.log_viewer.list_log_files()
            file_names = [f.name for f in log_files]
            
            self.log_file_combo['values'] = file_names
            if file_names and not self.log_file_var.get():
                self.log_file_var.set(file_names[0])  # Select first file by default
                
        except Exception as e:
            logger.error(f"Error refreshing log files: {e}", exc_info=True)
            self.log_status_var.set(f"Error loading log files: {str(e)}")
    
    def refresh_logs(self):
        """Refresh the log display with current filters."""
        try:
            self.log_status_var.set("Loading logs...")
            self.root.update()
            
            # Get current filter values
            log_file = self.log_file_var.get()
            level = self.log_level_var.get()
            search = self.log_search_var.get()
            
            if not log_file:
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(1.0, "No log file selected")
                self.log_status_var.set("No log file selected")
                return
            
            # Clear current content
            self.log_text.delete(1.0, tk.END)
            
            # Get filtered log content
            level_filter = None if level == "ALL" else level
            search_filter = None if not search.strip() else search.strip()
            
            # Read and filter log content
            log_file_path = self.log_viewer.log_dir / log_file
            if not log_file_path.exists():
                self.log_text.insert(1.0, f"Log file not found: {log_file}")
                self.log_status_var.set(f"Log file not found: {log_file}")
                return
            
            with open(log_file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            # Apply filters
            filtered_lines = []
            for line in all_lines:
                # Apply level filter
                if level_filter and level_filter.upper() not in line.upper():
                    continue
                
                # Apply search filter
                if search_filter and search_filter.lower() not in line.lower():
                    continue
                
                filtered_lines.append(line)
            
            # Display filtered content
            if filtered_lines:
                # Show last 1000 lines to avoid memory issues
                display_lines = filtered_lines[-1000:] if len(filtered_lines) > 1000 else filtered_lines
                
                for line in display_lines:
                    # Add color coding for different log levels
                    self.log_text.insert(tk.END, line)
                    
                    # Apply color tags based on log level
                    line_start = self.log_text.index("end-2l linestart")
                    line_end = self.log_text.index("end-1c")
                    
                    if "ERROR" in line.upper():
                        self.log_text.tag_add("error", line_start, line_end)
                    elif "WARNING" in line.upper():
                        self.log_text.tag_add("warning", line_start, line_end)
                    elif "CRITICAL" in line.upper():
                        self.log_text.tag_add("critical", line_start, line_end)
                    elif "INFO" in line.upper():
                        self.log_text.tag_add("info", line_start, line_end)
                    elif "DEBUG" in line.upper():
                        self.log_text.tag_add("debug", line_start, line_end)
                
                # Auto-scroll to bottom
                self.log_text.see(tk.END)
                
                self.log_status_var.set(
                    f"Showing {len(display_lines)} of {len(filtered_lines)} lines "
                    f"from {log_file} "
                    f"(Level: {level}, Search: '{search}' if any)"
                )
            else:
                self.log_text.insert(1.0, "No log entries match the current filters")
                self.log_status_var.set("No matching log entries")
                
        except Exception as e:
            error_msg = f"Error loading logs: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(1.0, f"Error: {error_msg}")
            self.log_status_var.set(error_msg)
    
    def clear_log_filters(self):
        """Clear all log filters and refresh display."""
        self.log_level_var.set("ALL")
        self.log_search_var.set("")
        self.refresh_logs()
    
    def on_search_change(self, event):
        """Handle search text changes with debouncing."""
        # Cancel any existing timer
        if hasattr(self, '_search_timer'):
            self.root.after_cancel(self._search_timer)
        
        # Set a new timer to refresh after 500ms of no typing
        self._search_timer = self.root.after(500, self.refresh_logs)
            
    def run(self):
        """Start the application."""
        logger.info("Starting Hockey Jersey Order Management application")
        self.root.mainloop()
        logger.info("Application shutdown")


def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Registrar Operations Center System')
    parser.add_argument('--test', action='store_true', 
                       help='Run in test mode (use test credentials and configuration)')
    parser.add_argument('--production', action='store_true',
                       help='Run in production mode (use production credentials and configuration)')
    
    args = parser.parse_args()
    
    # Setup logging first
    setup_logging()
    
    # Determine test mode
    test_mode = args.test
    if args.production:
        test_mode = False
    
    # If no mode specified, create a temporary config to check saved preferences
    if not args.test and not args.production:
        try:
            # Create a temporary config to check saved preferences
            temp_config = ConfigManager(test=False)  # Will load saved preferences
            test_mode = temp_config.is_test_mode
            logger.info(f"Using saved preference: {'test' if test_mode else 'production'} mode")
        except Exception as e:
            # Default to test mode if no mode specified (for safety)
            test_mode = True
            logger.info(f"No mode specified and failed to load preferences: {e}, defaulting to test mode for safety")
    else:
        logger.info(f"Using command line argument: {'test' if test_mode else 'production'} mode")
    
    logger.info(f"Starting application in {'test' if test_mode else 'production'} mode")
    
    # Create and run the application
    app = HockeyJerseyApp(test_mode=test_mode)
    app.run()


if __name__ == "__main__":
    main() 