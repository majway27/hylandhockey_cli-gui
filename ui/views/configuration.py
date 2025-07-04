import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
import logging

from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class ConfigurationView(ttk.Frame):
    def __init__(self, master, config: ConfigManager, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config = config
        self.mode_var = tk.StringVar(value="test" if self.config.is_test_mode else "production")
        self.mode_description_var = tk.StringVar()
        self.config_info_var = tk.StringVar()
        self.spreadsheet_info_var = tk.StringVar()
        self.build_ui()
        self.load_config()
        self.refresh()

    def build_ui(self):
        # Main configuration frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

        # Environment Mode Section
        mode_frame = ttk.LabelFrame(main_frame, text="Environment Mode", padding=10)
        mode_frame.pack(fill=X, pady=(0, 20))
        
        mode_selection_frame = ttk.Frame(mode_frame)
        mode_selection_frame.pack(fill=X, pady=(0, 10))
        ttk.Label(mode_selection_frame, text="Current Mode:").pack(side=LEFT)
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
        mode_desc_label = ttk.Label(
            mode_frame,
            textvariable=self.mode_description_var,
            font=("Helvetica", 9),
            foreground="gray"
        )
        mode_desc_label.pack(anchor=W)

        # Configuration Information Section
        info_frame = ttk.LabelFrame(main_frame, text="Configuration Information", padding=10)
        info_frame.pack(fill=X, pady=(0, 20))
        config_info_label = ttk.Label(
            info_frame,
            textvariable=self.config_info_var,
            font=("Consolas", 9),
            justify=tk.LEFT
        )
        config_info_label.pack(anchor=W)

        # Spreadsheet Configuration Section
        spreadsheet_frame = ttk.LabelFrame(main_frame, text="Spreadsheet Configuration", padding=10)
        spreadsheet_frame.pack(fill=X, pady=(0, 20))
        spreadsheet_info_label = ttk.Label(
            spreadsheet_frame,
            textvariable=self.spreadsheet_info_var,
            font=("Consolas", 9),
            justify=tk.LEFT
        )
        spreadsheet_info_label.pack(anchor=W)

        # Create notebook for different configuration sections
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=True, pady=(0, 20))

        # General settings tab
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General Settings")
        self.build_general_settings(general_frame)

        # Rate limiting tab
        rate_limiting_frame = ttk.Frame(notebook)
        notebook.add(rate_limiting_frame, text="Rate Limiting")
        self.build_rate_limiting_settings(rate_limiting_frame)

        # Save button
        save_frame = ttk.Frame(main_frame)
        save_frame.pack(fill=X, pady=(0, 0))
        
        ttk.Button(
            save_frame,
            text="Save Configuration",
            command=self.save_config,
            style="success.TButton"
        ).pack(side=RIGHT)

    def build_general_settings(self, parent):
        """Build the general settings section."""
        # Organization settings
        org_frame = ttk.LabelFrame(parent, text="Organization Settings", padding=10)
        org_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(org_frame, text="Organization Name:").pack(anchor=W)
        self.org_name_var = tk.StringVar()
        ttk.Entry(org_frame, textvariable=self.org_name_var, width=50).pack(fill=X, pady=(5, 0))

        # Email settings
        email_frame = ttk.LabelFrame(parent, text="Email Settings", padding=10)
        email_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(email_frame, text="Sender Email:").pack(anchor=W)
        self.sender_email_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.sender_email_var, width=50).pack(fill=X, pady=(5, 0))

        ttk.Label(email_frame, text="Default Recipient Email:").pack(anchor=W, pady=(10, 0))
        self.recipient_email_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.recipient_email_var, width=50).pack(fill=X, pady=(5, 0))

    def build_rate_limiting_settings(self, parent):
        """Build the rate limiting settings section."""
        # Retry settings
        retry_frame = ttk.LabelFrame(parent, text="Retry Settings", padding=10)
        retry_frame.pack(fill=X, pady=(0, 10))

        # Max retries
        retry_row1 = ttk.Frame(retry_frame)
        retry_row1.pack(fill=X, pady=(0, 5))
        ttk.Label(retry_row1, text="Max Retries:").pack(side=LEFT)
        self.max_retries_var = tk.StringVar()
        ttk.Entry(retry_row1, textvariable=self.max_retries_var, width=10).pack(side=LEFT, padx=(10, 0))
        ttk.Label(retry_row1, text="(Number of retry attempts for failed API calls)").pack(side=LEFT, padx=(10, 0))

        # Base delay
        retry_row2 = ttk.Frame(retry_frame)
        retry_row2.pack(fill=X, pady=(0, 5))
        ttk.Label(retry_row2, text="Base Delay (seconds):").pack(side=LEFT)
        self.base_delay_var = tk.StringVar()
        ttk.Entry(retry_row2, textvariable=self.base_delay_var, width=10).pack(side=LEFT, padx=(10, 0))
        ttk.Label(retry_row2, text="(Initial delay before first retry)").pack(side=LEFT, padx=(10, 0))

        # Max delay
        retry_row3 = ttk.Frame(retry_frame)
        retry_row3.pack(fill=X, pady=(0, 5))
        ttk.Label(retry_row3, text="Max Delay (seconds):").pack(side=LEFT)
        self.max_delay_var = tk.StringVar()
        ttk.Entry(retry_row3, textvariable=self.max_delay_var, width=10).pack(side=LEFT, padx=(10, 0))
        ttk.Label(retry_row3, text="(Maximum delay cap for exponential backoff)").pack(side=LEFT, padx=(10, 0))

        # Exponential backoff
        self.use_exponential_backoff_var = tk.BooleanVar()
        ttk.Checkbutton(
            retry_frame,
            text="Use Exponential Backoff (doubles delay on each retry)",
            variable=self.use_exponential_backoff_var
        ).pack(anchor=W, pady=(10, 0))

        # Delay settings
        delay_frame = ttk.LabelFrame(parent, text="Delay Settings", padding=10)
        delay_frame.pack(fill=X, pady=(0, 10))

        # API call delay
        delay_row1 = ttk.Frame(delay_frame)
        delay_row1.pack(fill=X, pady=(0, 5))
        ttk.Label(delay_row1, text="API Call Delay (seconds):").pack(side=LEFT)
        self.api_call_delay_var = tk.StringVar()
        ttk.Entry(delay_row1, textvariable=self.api_call_delay_var, width=10).pack(side=LEFT, padx=(10, 0))
        ttk.Label(delay_row1, text="(Delay between individual API calls)").pack(side=LEFT, padx=(10, 0))

        # Batch delay
        delay_row2 = ttk.Frame(delay_frame)
        delay_row2.pack(fill=X, pady=(0, 5))
        ttk.Label(delay_row2, text="Batch Delay (seconds):").pack(side=LEFT)
        self.batch_delay_var = tk.StringVar()
        ttk.Entry(delay_row2, textvariable=self.batch_delay_var, width=10).pack(side=LEFT, padx=(10, 0))
        ttk.Label(delay_row2, text="(Delay between batch operations)").pack(side=LEFT, padx=(10, 0))

        # Help text
        help_frame = ttk.LabelFrame(parent, text="Rate Limiting Help", padding=10)
        help_frame.pack(fill=X, pady=(0, 10))

        help_text = """
Rate limiting helps prevent 429 (Too Many Requests) errors from Google APIs.

• Max Retries: How many times to retry a failed API call
• Base Delay: Initial wait time before first retry
• Max Delay: Maximum wait time (prevents excessive delays)
• Exponential Backoff: Doubles delay on each retry for better recovery
• API Call Delay: Minimum time between API calls
• Batch Delay: Time to wait between processing batches

Recommended settings for most users:
• Max Retries: 3
• Base Delay: 1.0 seconds
• Max Delay: 60.0 seconds
• API Call Delay: 0.1 seconds
• Batch Delay: 0.5 seconds
        """
        
        help_label = ttk.Label(help_frame, text=help_text, justify=LEFT, wraplength=600)
        help_label.pack(anchor=W)

    def refresh(self):
        """Refresh the configuration display."""
        self.update_mode_description()
        self.update_config_info()
        self.update_spreadsheet_info()
        self.load_config()  # Reload configuration values to reflect current mode

    def on_mode_change(self):
        """Handle mode change via radio buttons."""
        new_mode = self.mode_var.get() == "test"
        if new_mode != self.config.is_test_mode:
            try:
                self.config.set_test_mode(new_mode)
                self.refresh()
                messagebox.showinfo("Mode Changed", f"Switched to {'TEST' if new_mode else 'PRODUCTION'} mode")
            except Exception as e:
                logger.error(f"Failed to change mode: {e}")
                messagebox.showerror("Error", f"Failed to change mode: {str(e)}")
                # Revert the radio button
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
        """Update the spreadsheet configuration information display."""
        try:
            info = f"Spreadsheet Name: {self.config.jersey_spreadsheet_name}\n"
            info += f"Spreadsheet ID: {self.config.jersey_spreadsheet_id}\n"
            info += f"Worksheet Name: {self.config.jersey_worksheet_jersey_orders_name}\n"
            info += f"Worksheet GID: {self.config.jersey_worksheet_jersey_orders_gid}\n"
            info += f"Sender Email: {self.config.jersey_sender_email}\n"
            info += f"Default To Email: {self.config.jersey_default_to_email}"
            self.spreadsheet_info_var.set(info)
        except Exception as e:
            info = f"Error loading configuration: {e}"
            self.spreadsheet_info_var.set(info)

    def load_config(self):
        """Load current configuration into the UI."""
        try:
            # Use ConfigManager properties to respect test mode
            self.org_name_var.set(self.config.organization_name)
            self.sender_email_var.set(self.config.jersey_sender_email)
            self.recipient_email_var.set(self.config.jersey_default_to_email)
            
            # Rate limiting settings (these don't have test variants, so use raw config)
            config_data = self.config.as_dict()
            rate_limiting = config_data.get('rate_limiting', {})
            self.max_retries_var.set(str(rate_limiting.get('max_retries', 3)))
            self.base_delay_var.set(str(rate_limiting.get('base_delay', 1.0)))
            self.max_delay_var.set(str(rate_limiting.get('max_delay', 60.0)))
            self.use_exponential_backoff_var.set(rate_limiting.get('use_exponential_backoff', True))
            self.api_call_delay_var.set(str(rate_limiting.get('api_call_delay', 0.1)))
            self.batch_delay_var.set(str(rate_limiting.get('batch_delay', 0.5)))
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")

    def save_config(self):
        """Save configuration from the UI."""
        try:
            config_data = self.config.as_dict()
            
            # Update general settings based on current mode
            if self.config.is_test_mode:
                config_data['organization_name_test'] = self.org_name_var.get()
                config_data['jersey_sender_email_test'] = self.sender_email_var.get()
                config_data['jersey_default_to_email_test'] = self.recipient_email_var.get()
            else:
                config_data['organization_name'] = self.org_name_var.get()
                config_data['jersey_sender_email'] = self.sender_email_var.get()
                config_data['jersey_default_to_email'] = self.recipient_email_var.get()
            
            # Update rate limiting settings
            if 'rate_limiting' not in config_data:
                config_data['rate_limiting'] = {}
            
            config_data['rate_limiting'].update({
                'max_retries': int(self.max_retries_var.get()),
                'base_delay': float(self.base_delay_var.get()),
                'max_delay': float(self.max_delay_var.get()),
                'use_exponential_backoff': self.use_exponential_backoff_var.get(),
                'api_call_delay': float(self.api_call_delay_var.get()),
                'batch_delay': float(self.batch_delay_var.get()),
                'retry_status_codes': [429, 500, 502, 503, 504]  # Default retry codes
            })
            
            # Save the configuration
            self.config.save_config(config_data)
            
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
        except ValueError as e:
            logger.error(f"Invalid configuration value: {e}")
            messagebox.showerror("Error", f"Invalid configuration value: {str(e)}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}") 