import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox, filedialog
import asyncio
import threading
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

from workflow.usa_hockey import MasterReportsWorkflow
from config.logging_config import get_logger
from utils.file_utils import FileUtils, DownloadManager

logger = get_logger(__name__)


class UsaImportView(ttk.Frame):
    def __init__(self, master, config, on_navigate=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config = config
        self.on_navigate = on_navigate
        self.workflow = MasterReportsWorkflow(config.usa_hockey)
        self.current_data = None
        self.current_file_path = None
        self.download_manager = DownloadManager()
        self.build_ui()

    def build_ui(self):
        # Header
        header_label = ttk.Label(
            self,
            text="USA Hockey Data Synchronization",
            font=("Helvetica", 14, "bold")
        )
        header_label.pack(pady=(20, 10))

        # Description
        desc_label = ttk.Label(
            self,
            text="Download and synchronize registration data with USA Hockey systems",
            font=("Helvetica", 10)
        )
        desc_label.pack(pady=(0, 20))

        # Main content frame
        content_frame = ttk.LabelFrame(self, text="Data Synchronization", padding=20)
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

        # Create a frame to hold both panels horizontally
        top_panels_frame = ttk.Frame(content_frame)
        top_panels_frame.pack(fill=X, pady=(0, 20))

        # Credentials check frame
        credentials_frame = ttk.LabelFrame(top_panels_frame, text="Authentication Status", padding=10)
        credentials_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

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
        self.data_info_frame = ttk.LabelFrame(top_panels_frame, text="Generate", padding=10)
        self.data_info_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 0))

        # Download button
        self.download_btn = ttk.Button(
            self.data_info_frame,
            text="Download Latest Master Report",
            command=self.download_master_report,
            style="primary.TButton"
        )
        self.download_btn.pack(anchor=W, pady=(10, 0))

        # Downloaded files panel
        files_frame = ttk.LabelFrame(content_frame, text="Available Snapshots", padding=10)
        files_frame.pack(fill=BOTH, expand=True, pady=(0, 20))

        # Files list frame
        files_list_frame = ttk.Frame(files_frame)
        files_list_frame.pack(fill=BOTH, expand=True)

        # Create Treeview for files
        columns = ("age", "status", "filename", "size", "modified")
        self.files_tree = ttk.Treeview(files_list_frame, columns=columns, show="headings", height=6)
        
        # Create custom style for Treeview headers
        style = ttk.Style()
        style.configure("Treeview.Heading", background="#495057", foreground="white", font=("Helvetica", 9, "bold"))
        
        # Configure columns
        self.files_tree.heading("age", text="Age")
        self.files_tree.heading("status", text="Status")
        self.files_tree.heading("filename", text="Filename")
        self.files_tree.heading("size", text="Size")
        self.files_tree.heading("modified", text="Modified")
        
        # Configure column widths
        self.files_tree.column("age", width=80, anchor="center")
        self.files_tree.column("status", width=100, anchor="center")
        self.files_tree.column("filename", width=300, anchor="center")
        self.files_tree.column("size", width=100, anchor="center")
        self.files_tree.column("modified", width=150, anchor="center")

        # Add scrollbar
        files_scrollbar = ttk.Scrollbar(files_list_frame, orient=VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=files_scrollbar.set)

        # Pack tree and scrollbar
        self.files_tree.pack(side=LEFT, fill=BOTH, expand=True)
        files_scrollbar.pack(side=RIGHT, fill=Y)

        # Bind double-click event to load file
        self.files_tree.bind("<Double-1>", self.on_file_double_click)

        # Files action buttons frame
        files_actions_frame = ttk.Frame(files_frame)
        files_actions_frame.pack(fill=X, pady=(10, 0))

        # Refresh files button
        refresh_files_btn = ttk.Button(
            files_actions_frame,
            text="Refresh Files List",
            command=self.refresh_files_list,
            style="secondary.TButton"
        )
        refresh_files_btn.pack(side=LEFT, padx=(0, 10))

        # Load selected file button
        self.load_selected_btn = ttk.Button(
            files_actions_frame,
            text="Load Selected File",
            command=self.load_selected_file,
            style="info.TButton",
            state="disabled"
        )
        self.load_selected_btn.pack(side=LEFT, padx=(0, 10))

        # Delete selected file button
        self.delete_selected_btn = ttk.Button(
            files_actions_frame,
            text="Delete Selected File",
            command=self.delete_selected_file,
            style="danger.TButton",
            state="disabled"
        )
        self.delete_selected_btn.pack(side=LEFT)

        # Bind selection event
        self.files_tree.bind("<<TreeviewSelect>>", self.on_file_selection_change)

        # Loaded file panel
        loaded_file_frame = ttk.LabelFrame(content_frame, text="Loaded File", padding=10)
        loaded_file_frame.pack(fill=X, pady=(0, 20))

        # Loaded file info
        self.loaded_file_var = tk.StringVar(value="No file loaded")
        self.loaded_file_label = ttk.Label(
            loaded_file_frame,
            textvariable=self.loaded_file_var,
            font=("Consolas", 9),
            justify=tk.LEFT
        )
        self.loaded_file_label.pack(anchor=W)

        # View Data button
        self.view_data_btn = ttk.Button(
            loaded_file_frame,
            text="View Data",
            command=self.view_data,
            style="info.TButton",
            state="disabled"
        )
        self.view_data_btn.pack(anchor=W, pady=(10, 0))

        # Initialize
        self.check_credentials()
        self.refresh_files_list()

    def refresh_files_list(self):
        """Refresh the list of downloaded files."""
        # Clear existing items
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # Get files using the download manager
        files = self.download_manager.get_usa_hockey_files(sort_by="modified", reverse=True)
        
        for file_info in files:
            # Determine status
            if self.current_file_path and file_info['path'] == self.current_file_path:
                status = "Loaded"
            else:
                status = "Available"
            
            # Calculate age
            age_str = self.format_file_age(file_info['modified'])
            
            # Insert into tree
            self.files_tree.insert("", "end", values=(
                age_str,
                status,
                file_info['name'],
                file_info['size_formatted'],
                file_info['modified_str']
            ), tags=(file_info['path'],))

    def on_file_selection_change(self, event):
        """Handle file selection change in the treeview."""
        selection = self.files_tree.selection()
        if selection:
            self.load_selected_btn.config(state="normal")
            self.delete_selected_btn.config(state="normal")
        else:
            self.load_selected_btn.config(state="disabled")
            self.delete_selected_btn.config(state="disabled")

    def on_file_double_click(self, event):
        """Handle double-click on a file in the treeview."""
        selection = self.files_tree.selection()
        if selection:
            self.load_selected_file()

    def load_selected_file(self):
        """Load the selected file from the treeview."""
        selection = self.files_tree.selection()
        if not selection:
            return
        
        # Get the file path from the item tags
        item = selection[0]
        file_path = self.files_tree.item(item, "tags")[0]
        
        if file_path and Path(file_path).exists():
            self.load_and_display_data(Path(file_path))
        else:
            messagebox.showerror("Error", "Selected file not found")

    def delete_selected_file(self):
        """Delete the selected file from the treeview."""
        selection = self.files_tree.selection()
        if not selection:
            return
        
        # Get the file path from the item tags
        item = selection[0]
        file_path = self.files_tree.item(item, "tags")[0]
        
        if not file_path or not Path(file_path).exists():
            messagebox.showerror("Error", "Selected file not found")
            return
        
        # Confirm deletion
        filename = Path(file_path).name
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{filename}'?"):
            success, message = FileUtils.safe_delete_file(Path(file_path))
            
            if success:
                messagebox.showinfo("Success", f"File '{filename}' deleted successfully")
                self.refresh_files_list()
                
                # If this was the currently loaded file, clear the current data
                if self.current_file_path and Path(file_path) == self.current_file_path:
                    self.current_data = None
                    self.current_file_path = None
                    #self.data_info_var.set("No data downloaded")
                    self.loaded_file_var.set("No file loaded")
                    self.view_data_btn.config(state="disabled")
            else:
                messagebox.showerror("Error", f"Failed to delete file: {message}")

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
            
            # Refresh files list to show the new file
            self.refresh_files_list()
            
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

    def format_file_age(self, modified_time: datetime) -> str:
        """
        Format file age in human-friendly hours-minutes format.
        
        Args:
            modified_time: File modification time
            
        Returns:
            Formatted age string (e.g., "2h 30m", "45m", "1d 3h")
        """
        if not modified_time:
            return "Unknown"
        
        now = datetime.now()
        age_delta = now - modified_time
        
        # Convert to total minutes
        total_minutes = int(age_delta.total_seconds() / 60)
        
        if total_minutes < 60:
            return f"{total_minutes}m"
        elif total_minutes < 1440:  # Less than 24 hours
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if minutes == 0:
                return f"{hours}h"
            else:
                return f"{hours}h {minutes}m"
        else:  # 24 hours or more
            days = total_minutes // 1440
            remaining_minutes = total_minutes % 1440
            hours = remaining_minutes // 60
            minutes = remaining_minutes % 60
            
            if hours == 0 and minutes == 0:
                return f"{days}d"
            elif minutes == 0:
                return f"{days}d {hours}h"
            else:
                return f"{days}d {hours}h {minutes}m"

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
                                
                # Update loaded file info
                loaded_file_text = f"Currently loaded: {file_path.name}\n"
                loaded_file_text += f"Records: {summary['total_records']:,}\n"
                loaded_file_text += f"Columns: {summary['column_count']}"
                
                self.loaded_file_var.set(loaded_file_text)
                
                # Enable view button
                self.view_data_btn.config(state="normal")
                
                # Refresh files list to update status
                self.refresh_files_list()
                
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
                    # Refresh files list to show the new exported file
                    self.refresh_files_list()
                else:
                    messagebox.showerror("Error", "Failed to export data")
                    
            except Exception as e:
                logger.error(f"Export error: {e}")
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def view_data(self):
        """Navigate to the master data view to see the records."""
        if self.current_data is not None:
            # Store the data in a way that the master view can access it
            self.config.current_master_data = self.current_data
            self.config.current_master_file_path = self.current_file_path
            
            # Navigate to the master view using the navigation callback
            if self.on_navigate:
                self.on_navigate("Master (USA)")
            else:
                logger.error("No navigation callback available")
        else:
            messagebox.showwarning("Warning", "No data to view")

    def refresh(self):
        """Refresh the view and check for updates."""
        self.check_credentials()
        
        # Refresh files list
        self.refresh_files_list()
        
        # Refresh data info if we have data
        if self.current_file_path and self.current_file_path.exists():
            self.load_and_display_data(self.current_file_path)
        else:
            #self.data_info_var.set("No data downloaded")
            self.loaded_file_var.set("No file loaded")
            self.view_data_btn.config(state="disabled")
        
        self.status_var.set("Ready")
        self.progress_var.set(0) 