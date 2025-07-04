import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk

class ConfigurationView(ttk.Frame):
    def __init__(self, master, config, log_viewer, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config = config
        self.log_viewer = log_viewer
        self.mode_var = tk.StringVar(value="test" if self.config.is_test_mode else "production")
        self.mode_description_var = tk.StringVar()
        self.config_info_var = tk.StringVar()
        self.spreadsheet_info_var = tk.StringVar()
        self.build_ui()
        self.refresh()

    def build_ui(self):
        mode_frame = ttk.LabelFrame(self, text="Environment Mode", padding=10)
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
        info_frame = ttk.LabelFrame(self, text="Configuration Information", padding=10)
        info_frame.pack(fill=X, pady=(0, 20))
        config_info_label = ttk.Label(
            info_frame,
            textvariable=self.config_info_var,
            font=("Consolas", 9),
            justify=tk.LEFT
        )
        config_info_label.pack(anchor=W)
        spreadsheet_frame = ttk.LabelFrame(self, text="Spreadsheet Configuration", padding=10)
        spreadsheet_frame.pack(fill=X, pady=(0, 20))
        spreadsheet_info_label = ttk.Label(
            spreadsheet_frame,
            textvariable=self.spreadsheet_info_var,
            font=("Consolas", 9),
            justify=tk.LEFT
        )
        spreadsheet_info_label.pack(anchor=W)
        # Additional controls and actions can be added here

    def refresh(self):
        self.update_mode_description()
        self.update_config_info()
        self.update_spreadsheet_info()

    def on_mode_change(self):
        # Placeholder for integration
        pass

    def update_mode_description(self):
        if self.config.is_test_mode:
            self.mode_description_var.set(
                "Test Mode: Uses test credentials and configuration. Safe for development and testing."
            )
        else:
            self.mode_description_var.set(
                "Production Mode: Uses production credentials and configuration. Changes affect live data."
            )

    def update_config_info(self):
        info = f"Mode: {'TEST' if self.config.is_test_mode else 'PRODUCTION'}\n"
        info += f"Credentials File: credentials{'test' if self.config.is_test_mode else ''}.json\n"
        info += f"Token File: token{'test' if self.config.is_test_mode else ''}.pickle\n"
        info += f"Config File: config.yaml\n"
        info += f"Preferences File: preferences.yaml"
        self.config_info_var.set(info)

    def update_spreadsheet_info(self):
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