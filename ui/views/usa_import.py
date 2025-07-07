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
from workflow.usa_hockey.custom_reports import CustomReportsWorkflow
from config.logging_config import get_logger
from utils.file_utils import FileUtils, DownloadManager

logger = get_logger(__name__)


class UsaImportView(ttk.Frame):
    def __init__(self, master, config, on_navigate=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config = config
        self.on_navigate = on_navigate
        self.workflow = MasterReportsWorkflow(config.usa_hockey)
        self.custom_reports = CustomReportsWorkflow(config.usa_hockey)
        self.current_data = None
        self.current_file_path = None
        self.download_manager = DownloadManager()
        self.timer_running = False
        self.timer_seconds = 0
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

        # Timer label
        self.timer_var = tk.StringVar(value="")
        self.timer_label = ttk.Label(
            self.status_frame,
            textvariable=self.timer_var,
            font=("Helvetica", 9, "bold")
        )
        self.timer_label.pack(side=RIGHT, padx=(10, 0))

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

        # Run saved report button
        self.run_saved_report_btn = ttk.Button(
            self.data_info_frame,
            text="Download Latest Custom Report",
            command=self.run_saved_report,
            style="primary.TButton"
        )
        self.run_saved_report_btn.pack(anchor=W, pady=(10, 0))

        # Downloaded files panel
        files_frame = ttk.LabelFrame(content_frame, text="Available Snapshots", padding=10)
        files_frame.pack(fill=BOTH, expand=True, pady=(0, 20))

        # Files list frame
        files_list_frame = ttk.Frame(files_frame)
        files_list_frame.pack(fill=BOTH, expand=True)

        # Files listbox
        self.files_listbox = tk.Listbox(files_list_frame, height=8)
        self.files_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Bind double-click event to load and view data
        self.files_listbox.bind("<Double-1>", self.on_file_double_click)

        # Scrollbar for files listbox
        files_scrollbar = ttk.Scrollbar(files_list_frame, orient=VERTICAL, command=self.files_listbox.yview)
        files_scrollbar.pack(side=RIGHT, fill=Y)
        self.files_listbox.config(yscrollcommand=files_scrollbar.set)

        # Files actions frame
        files_actions_frame = ttk.Frame(files_frame)
        files_actions_frame.pack(fill=X, pady=(10, 0))

        # Refresh files button
        refresh_files_btn = ttk.Button(
            files_actions_frame,
            text="Refresh Files",
            command=self.refresh_files_list,
            style="secondary.TButton"
        )
        refresh_files_btn.pack(side=LEFT, padx=(0, 10))

        # Load selected file button
        self.load_file_btn = ttk.Button(
            files_actions_frame,
            text="Load Selected File",
            command=self.load_selected_file,
            style="primary.TButton"
        )
        self.load_file_btn.pack(side=LEFT, padx=(0, 10))

        # View Data button (navigate to Master view)
        self.view_data_btn = ttk.Button(
            files_actions_frame,
            text="View Data",
            command=self.view_data,
            style="success.TButton",
            state="disabled"
        )
        self.view_data_btn.pack(side=LEFT, padx=(0, 10))

        # Delete selected file button
        self.delete_file_btn = ttk.Button(
            files_actions_frame,
            text="Delete Selected File",
            command=self.delete_selected_file,
            style="danger.TButton"
        )
        self.delete_file_btn.pack(side=LEFT)

        # Data preview frame
        preview_frame = ttk.LabelFrame(content_frame, text="Data Preview", padding=10)
        preview_frame.pack(fill=BOTH, expand=True, pady=(0, 20))

        # Preview text widget
        self.preview_text = tk.Text(preview_frame, height=10, wrap=tk.WORD)
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=VERTICAL, command=self.preview_text.yview)
        preview_scrollbar.pack(side=RIGHT, fill=Y)
        self.preview_text.config(yscrollcommand=preview_scrollbar.set)
        self.preview_text.pack(side=LEFT, fill=BOTH, expand=True)

        # Initialize
        self.refresh_files_list()
        self.check_credentials()

    def start_timer(self):
        """Start the 5-minute countdown timer."""
        self.timer_running = True
        self.timer_seconds = 5 * 60  # 5 minutes in seconds
        self.update_timer()

    def stop_timer(self):
        """Stop the timer."""
        self.timer_running = False
        self.timer_var.set("")

    def update_timer(self):
        """Update the timer display."""
        if self.timer_running and self.timer_seconds > 0:
            minutes = self.timer_seconds // 60
            seconds = self.timer_seconds % 60
            self.timer_var.set(f"⏱ {minutes:02d}:{seconds:02d}")
            self.timer_seconds -= 1
            self.after(1000, self.update_timer)  # Schedule next update in 1 second
        elif self.timer_running and self.timer_seconds <= 0:
            self.timer_var.set("⏱ Time's up!")
            self.timer_running = False

    def check_credentials(self):
        """Check USA Hockey credentials."""
        try:
            if self.workflow.validate_credentials():
                self.credentials_var.set("✓ Credentials available")
                self.credentials_label.config(foreground="green")
            else:
                self.credentials_var.set("✗ Credentials not available")
                self.credentials_label.config(foreground="red")
        except Exception as e:
            logger.error(f"Error checking credentials: {e}")
            self.credentials_var.set("✗ Error checking credentials")
            self.credentials_label.config(foreground="red")

    def download_master_report(self):
        """Download the latest master report."""
        if not self.workflow.validate_credentials():
            messagebox.showerror("Error", "USA Hockey credentials not available")
            return
        
        self.run_saved_report_btn.config(state="disabled")
        self.start_timer()
        
        def download_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.workflow.download_master_report(
                        progress_callback=self.update_progress
                    )
                )
                self.after(0, self.download_completed, result)
            except Exception as e:
                logger.error(f"Master report download error: {e}")
                self.after(0, self.download_failed, str(e))
            finally:
                loop.close()
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()

    def run_saved_report(self):
        """Run the saved report 'Saved_Report_All_Fields'."""
        if not self.custom_reports.validate_credentials():
            messagebox.showerror("Error", "USA Hockey credentials not available")
            return
        
        # Define the saved report fields and filters
        saved_report_fields = [
            "Member Type", "Last Name", "First Name", "Middle Initial", "DOB", 
            "DOB Verified", "Citizenship", "Citizenship Verified", "Transfer Status", 
            "Gender", "Email", "Confirmation Number", "Address", "City", "State", 
            "Zip", "Phone 1", "Phone 2", "Parental Guardian 1", "Parental Guardian 2", 
            "CEP Level", "CEP #", "CEP Expires", "Total Credit Earned", "Modules", 
            "Safe Sport", "Date to Expire", "Screening", "Season to Renew", 
            "Team Member Position", "Team Member Type", "Team Member Redlined Note", 
            "Home Number", "Away Number", "Date Rostered", "Team Name", "Team ID", 
            "Team Type", "Team Season Type", "Classification", "Division", "Category", 
            "Team Submitted Date", "Team Approved Date", "Public Link URL", 
            "Team Notes", "NT Bound", "Team Status", "Original Approved Date"
        ]
        
        saved_report_filters = {
            "State": {"type": "eq", "value": "CO"}
        }
        
        self.run_saved_report_btn.config(state="disabled")
        self.start_timer()
        
        def download_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.custom_reports.download_custom_report(
                        fields=saved_report_fields,
                        filters=saved_report_filters,
                        format="csv",
                        progress_callback=self.update_progress
                    )
                )
                self.after(0, self.saved_report_completed, result)
            except Exception as e:
                logger.error(f"Saved report download error: {e}")
                self.after(0, self.saved_report_failed, str(e))
            finally:
                loop.close()
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()

    def update_progress(self, message: str, progress: float):
        """Update progress bar and status."""
        self.after(0, lambda: self.status_var.set(message))
        self.after(0, lambda: self.progress_var.set(progress))

    def download_completed(self, file_path):
        """Handle master report download completion."""
        self.run_saved_report_btn.config(state="normal")
        self.stop_timer()
        
        if file_path:
            messagebox.showinfo("Success", f"Master report downloaded successfully!\nFile: {file_path}")
            
            # Refresh files list to show the new file
            self.refresh_files_list()
        else:
            messagebox.showerror("Error", "Master report download failed. Check the logs for details.")

    def saved_report_completed(self, file_path):
        """Handle saved report download completion."""
        self.run_saved_report_btn.config(state="normal")
        self.stop_timer()
        
        if file_path:
            messagebox.showinfo("Success", f"Saved report downloaded successfully!\nFile: {file_path}")
            
            # Refresh files list to show the new file
            self.refresh_files_list()
            
            # Automatically load the newly downloaded file for preview
            if Path(file_path).exists():
                self.load_file_preview(Path(file_path))
        else:
            messagebox.showerror("Error", "Saved report download failed. Check the logs for details.")

    def download_failed(self, error_message):
        """Handle download failure."""
        self.run_saved_report_btn.config(state="normal")
        self.stop_timer()
        self.status_var.set("Download failed")
        self.progress_var.set(0)
        messagebox.showerror("Download Error", f"Failed to download master report:\n{error_message}")

    def saved_report_failed(self, error_message):
        """Handle saved report download failure."""
        self.run_saved_report_btn.config(state="normal")
        self.stop_timer()
        self.status_var.set("Saved report download failed")
        self.progress_var.set(0)
        messagebox.showerror("Download Error", f"Failed to download saved report:\n{error_message}")

    def refresh_files_list(self):
        """Refresh the list of available files."""
        try:
            download_dir = self.config.usa_hockey.download_directory
            if not download_dir.exists():
                return
            
            # Clear current list
            self.files_listbox.delete(0, tk.END)
            
            # Get all CSV and Excel files
            files = []
            for ext in ['*.csv', '*.xlsx', '*.xls']:
                files.extend(download_dir.glob(ext))
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Add files to listbox
            for file_path in files:
                # Format display name with date
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                display_name = f"{mtime.strftime('%Y-%m-%d %H:%M')} - {file_path.name}"
                self.files_listbox.insert(tk.END, display_name)
                # Store full path as item data
                self.files_listbox.itemconfig(tk.END, {'bg': 'white'})
                
        except Exception as e:
            logger.error(f"Error refreshing files list: {e}")

    def load_selected_file(self):
        """Load the selected file for preview."""
        selection = self.files_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to load")
            return
        
        try:
            # Get the selected file path
            download_dir = self.config.usa_hockey.download_directory
            files = []
            for ext in ['*.csv', '*.xlsx', '*.xls']:
                files.extend(download_dir.glob(ext))
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            selected_index = selection[0]
            if selected_index < len(files):
                file_path = files[selected_index]
                self.load_file_preview(file_path)
                
        except Exception as e:
            logger.error(f"Error loading selected file: {e}")
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def load_file_preview(self, file_path: Path):
        """Load and display a preview of the file."""
        try:
            self.status_var.set(f"Loading preview: {file_path.name}")
            
            # Read the file based on its extension
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path, nrows=100)  # Preview first 100 rows
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path, nrows=100)  # Preview first 100 rows
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
            # Clear preview
            self.preview_text.delete(1.0, tk.END)
            
            # Display file info
            info_text = f"File: {file_path.name}\n"
            info_text += f"Preview: {len(df)} rows (first 100)\n"
            info_text += f"Columns: {len(df.columns)}\n"
            info_text += f"Size: {file_path.stat().st_size / 1024:.1f} KB\n\n"
            
            # Display column names
            info_text += "Columns:\n"
            for i, col in enumerate(df.columns, 1):
                info_text += f"{i:2d}. {col}\n"
            
            info_text += "\n" + "="*50 + "\n\n"
            
            # Display first few rows
            info_text += df.head(10).to_string(index=False)
            
            self.preview_text.insert(1.0, info_text)
            self.status_var.set(f"Preview loaded: {file_path.name}")
            
            # Store current file path
            self.current_file_path = file_path
            
            # Load the full data and store in config for Master view
            self.load_full_data(file_path)
            
        except Exception as e:
            logger.error(f"Error loading file preview: {e}")
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, f"Error loading file: {e}")
            self.status_var.set("Error loading preview")

    def load_full_data(self, file_path: Path):
        """Load the full data and store it in config for Master view."""
        try:
            self.status_var.set(f"Loading full data: {file_path.name}")
            
            # Read the full file based on its extension
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
            # Store the full data in config for Master view
            self.config.current_master_data = df
            self.config.current_master_file_path = file_path
            
            # Enable the View Data button
            self.view_data_btn.config(state="normal")
            
            # Update the preview text to show total record count
            self.update_preview_with_total_count(len(df))
            
            self.status_var.set(f"Full data loaded: {len(df):,} records")
            logger.info(f"Full data loaded from {file_path}: {len(df)} records")
            
        except Exception as e:
            logger.error(f"Error loading full data: {e}")
            self.status_var.set("Error loading full data")
            # Disable the View Data button
            self.view_data_btn.config(state="disabled")

    def update_preview_with_total_count(self, total_records):
        """Update the preview text to show the total record count."""
        try:
            # Get current preview text
            current_text = self.preview_text.get(1.0, tk.END)
            
            # Find and replace the preview line with total count
            lines = current_text.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('Preview:'):
                    lines[i] = f"Total Records: {total_records:,}"
                    break
            
            # Update the preview text
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, '\n'.join(lines))
            
        except Exception as e:
            logger.error(f"Error updating preview with total count: {e}")

    def delete_selected_file(self):
        """Delete the selected file."""
        selection = self.files_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to delete")
            return
        
        try:
            # Get the selected file path
            download_dir = self.config.usa_hockey.download_directory
            files = []
            for ext in ['*.csv', '*.xlsx', '*.xls']:
                files.extend(download_dir.glob(ext))
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            selected_index = selection[0]
            if selected_index < len(files):
                file_path = files[selected_index]
                
                # Confirm deletion
                result = messagebox.askyesno(
                    "Confirm Deletion",
                    f"Are you sure you want to delete:\n{file_path.name}?"
                )
                
                if result:
                    file_path.unlink()
                    messagebox.showinfo("Success", f"File deleted: {file_path.name}")
                    self.refresh_files_list()
                    
                    # Clear preview if this was the current file
                    if self.current_file_path == file_path:
                        self.preview_text.delete(1.0, tk.END)
                        self.current_file_path = None
                        # Clear data from config and disable View Data button
                        if hasattr(self.config, 'current_master_data'):
                            self.config.current_master_data = None
                        if hasattr(self.config, 'current_master_file_path'):
                            self.config.current_master_file_path = None
                        self.view_data_btn.config(state="disabled")
                        
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            messagebox.showerror("Error", f"Failed to delete file: {e}")

    def view_data(self):
        """Navigate to the Master view."""
        if hasattr(self.config, 'current_master_data') and self.config.current_master_data is not None:
            if self.on_navigate:
                self.on_navigate("Master (USA)")
            else:
                messagebox.showwarning("Warning", "Navigation not available")
        else:
            messagebox.showwarning("Warning", "No data loaded for viewing")

    def on_file_double_click(self, event):
        """Handle double-click on a file in the listbox."""
        # Get the clicked item
        selection = self.files_listbox.curselection()
        if not selection:
            return
        
        try:
            # Get the selected file path
            download_dir = self.config.usa_hockey.download_directory
            files = []
            for ext in ['*.csv', '*.xlsx', '*.xls']:
                files.extend(download_dir.glob(ext))
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            selected_index = selection[0]
            if selected_index < len(files):
                file_path = files[selected_index]
                
                # Load the file data
                self.load_file_preview(file_path)
                
                # Wait a moment for the data to load, then navigate to Master view
                self.after(100, self.navigate_to_master_after_load)
                
        except Exception as e:
            logger.error(f"Error handling file double-click: {e}")
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def navigate_to_master_after_load(self):
        """Navigate to Master view after data has been loaded."""
        if hasattr(self.config, 'current_master_data') and self.config.current_master_data is not None:
            if self.on_navigate:
                self.on_navigate("Master (USA)")
            else:
                messagebox.showwarning("Warning", "Navigation not available")
        else:
            messagebox.showwarning("Warning", "Failed to load data for viewing") 