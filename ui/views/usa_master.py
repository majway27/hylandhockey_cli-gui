import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox, filedialog
import asyncio
import threading
from pathlib import Path
from datetime import datetime
import pandas as pd

from workflow.usa_hockey import MasterReportsWorkflow
from config.logging_config import get_logger

logger = get_logger(__name__)


class UsaMasterView(ttk.Frame):
    def __init__(self, master, config, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config = config
        self.workflow = MasterReportsWorkflow(config.usa_hockey)
        self.current_data = None
        self.current_file_path = None
        self.build_ui()

    def build_ui(self):
        # Header
        header_label = ttk.Label(
            self,
            text="USA Hockey Master Registration",
            font=("Helvetica", 14, "bold")
        )
        header_label.pack(pady=(20, 10))

        # Description
        desc_label = ttk.Label(
            self,
            text="Download and manage master registration reports from USA Hockey",
            font=("Helvetica", 10)
        )
        desc_label.pack(pady=(0, 20))

        # Main content frame
        content_frame = ttk.LabelFrame(self, text="Master Registration Data", padding=20)
        content_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)

        # Status frame
        self.status_frame = ttk.Frame(content_frame)
        self.status_frame.pack(fill=X, pady=(0, 20))

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            self.status_frame,
            textvariable=self.status_var,
            font=("Helvetica", 10, "bold")
        )
        self.status_label.pack(side=LEFT)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            variable=self.progress_var,
            maximum=100,
            length=300
        )
        self.progress_bar.pack(side=RIGHT, padx=(10, 0))

        # Credentials check frame
        credentials_frame = ttk.LabelFrame(content_frame, text="Authentication Status", padding=10)
        credentials_frame.pack(fill=X, pady=(0, 20))

        # Credentials status
        self.credentials_var = tk.StringVar()
        self.credentials_label = ttk.Label(
            credentials_frame,
            textvariable=self.credentials_var,
            font=("Helvetica", 9)
        )
        self.credentials_label.pack(anchor=W)

        # Check credentials button
        check_creds_btn = ttk.Button(
            credentials_frame,
            text="Check Credentials",
            command=self.check_credentials,
            style="secondary.TButton"
        )
        check_creds_btn.pack(anchor=W, pady=(5, 0))

        # Data info frame
        self.data_info_frame = ttk.LabelFrame(content_frame, text="Data Information", padding=10)
        self.data_info_frame.pack(fill=X, pady=(0, 20))

        # Data info text
        self.data_info_var = tk.StringVar(value="No data loaded")
        self.data_info_label = ttk.Label(
            self.data_info_frame,
            textvariable=self.data_info_var,
            font=("Consolas", 9),
            justify=tk.LEFT
        )
        self.data_info_label.pack(anchor=W)

        # Action buttons frame
        actions_frame = ttk.Frame(content_frame)
        actions_frame.pack(side=BOTTOM, fill=X, pady=(20, 0))

        # Download button
        self.download_btn = ttk.Button(
            actions_frame,
            text="Download Master Report",
            command=self.download_master_report,
            style="primary.TButton"
        )
        self.download_btn.pack(side=LEFT, padx=(0, 10))

        # Load existing button
        load_btn = ttk.Button(
            actions_frame,
            text="Load Existing Report",
            command=self.load_existing_report,
            style="secondary.TButton"
        )
        load_btn.pack(side=LEFT, padx=(0, 10))

        # Export button
        self.export_btn = ttk.Button(
            actions_frame,
            text="Export Data",
            command=self.export_data,
            style="secondary.TButton",
            state="disabled"
        )
        self.export_btn.pack(side=LEFT, padx=(0, 10))

        # Refresh button
        refresh_btn = ttk.Button(
            actions_frame,
            text="Refresh",
            command=self.refresh,
            style="secondary.TButton"
        )
        refresh_btn.pack(side=LEFT)

        # Initialize
        self.check_credentials()

    def check_credentials(self):
        """Check if USA Hockey credentials are available."""
        try:
            has_credentials = self.workflow.validate_credentials()
            if has_credentials:
                self.credentials_var.set("✅ USA Hockey credentials available")
                self.download_btn.config(state="normal")
            else:
                self.credentials_var.set("❌ USA Hockey credentials not found. Please add username and password to config.yaml file.")
                self.download_btn.config(state="disabled")
        except Exception as e:
            self.credentials_var.set(f"❌ Error checking credentials: {str(e)}")
            self.download_btn.config(state="disabled")

    def update_progress(self, message: str, progress: float):
        """Update progress bar and status message."""
        self.status_var.set(message)
        self.progress_var.set(progress * 100)
        self.update_idletasks()

    def download_master_report(self):
        """Download master registration report."""
        if not self.workflow.validate_credentials():
            messagebox.showerror("Error", "USA Hockey credentials not available")
            return

        # Disable download button during operation
        self.download_btn.config(state="disabled")
        
        # Start download in background thread
        def download_thread():
            try:
                # Create event loop for async operations
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Run the download
                result = loop.run_until_complete(
                    self.workflow.download_master_report(
                        progress_callback=self.update_progress
                    )
                )
                
                # Update UI in main thread
                self.after(0, self.download_completed, result)
                
            except Exception as e:
                logger.error(f"Download error: {e}")
                self.after(0, self.download_failed, str(e))
            finally:
                loop.close()

        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()

    def download_completed(self, file_path):
        """Handle download completion."""
        self.download_btn.config(state="normal")
        
        if file_path:
            self.current_file_path = file_path
            messagebox.showinfo("Success", f"Master report downloaded successfully!\nFile: {file_path}")
            
            # Load and display the data
            self.load_and_display_data(file_path)
        else:
            messagebox.showerror("Error", "Download failed. Check the logs for details.")

    def download_failed(self, error_message):
        """Handle download failure."""
        self.download_btn.config(state="normal")
        self.status_var.set("Download failed")
        self.progress_var.set(0)
        messagebox.showerror("Download Error", f"Failed to download master report:\n{error_message}")

    def load_existing_report(self):
        """Load an existing master report file."""
        file_path = filedialog.askopenfilename(
            title="Select Master Report File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=self.workflow.get_download_directory()
        )
        
        if file_path:
            self.load_and_display_data(Path(file_path))

    def load_and_display_data(self, file_path: Path):
        """Load and display the master report data."""
        try:
            self.status_var.set("Loading data...")
            
            # Process the data
            df = self.workflow.process_master_report(file_path)
            
            if df is not None:
                self.current_data = df
                self.current_file_path = file_path
                
                # Generate summary
                summary = self.workflow.get_report_summary(df)
                
                # Update data info
                info_text = f"File: {file_path.name}\n"
                info_text += f"Records: {summary['total_records']:,}\n"
                info_text += f"Columns: {summary['column_count']}\n"
                info_text += f"Last modified: {datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}"
                
                self.data_info_var.set(info_text)
                
                # Enable export button
                self.export_btn.config(state="normal")
                
                self.status_var.set("Data loaded successfully")
                messagebox.showinfo("Success", f"Loaded {len(df):,} records from master report")
            else:
                messagebox.showerror("Error", "Failed to process the master report file")
                
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
        finally:
            self.progress_var.set(0)

    def export_data(self):
        """Export the current data to various formats."""
        if self.current_data is None:
            messagebox.showwarning("Warning", "No data to export")
            return

        # Ask user for export format and location
        file_path = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            initialdir=self.workflow.get_download_directory()
        )
        
        if file_path:
            try:
                output_path = Path(file_path)
                
                if output_path.suffix.lower() == '.xlsx':
                    success = self.workflow.export_to_excel(self.current_data, output_path)
                else:
                    # Export as CSV
                    self.current_data.to_csv(output_path, index=False)
                    success = True
                
                if success:
                    messagebox.showinfo("Success", f"Data exported successfully to:\n{output_path}")
                else:
                    messagebox.showerror("Error", "Failed to export data")
                    
            except Exception as e:
                logger.error(f"Export error: {e}")
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def refresh(self):
        """Refresh the view and check for updates."""
        self.check_credentials()
        
        # Refresh data info if we have data
        if self.current_file_path and self.current_file_path.exists():
            self.load_and_display_data(self.current_file_path)
        else:
            self.data_info_var.set("No data loaded")
            self.export_btn.config(state="disabled")
        
        self.status_var.set("Ready")
        self.progress_var.set(0) 