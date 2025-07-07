import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
from datetime import datetime
import pandas as pd
import json

from workflow.usa_hockey import MasterReportsWorkflow
from workflow.usa_hockey.data_processor import DataProcessor
from config.logging_config import get_logger
from ui.utils.styling import apply_treeview_styling, apply_alternating_row_colors, get_alternating_row_tags, configure_columns_with_priority_styling

logger = get_logger(__name__)


class ColumnSettingsDialog:
    """Modal dialog for managing column visibility settings."""
    
    def __init__(self, parent, columns, visible_columns):
        self.parent = parent
        self.columns = columns
        self.visible_columns = visible_columns.copy()
        self.result = None
        
        # Create modal dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Column Visibility Settings")
        self.dialog.geometry("400x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"400x500+{x}+{y}")
        
        self.build_ui()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def build_ui(self):
        """Build the dialog UI."""
        # Header
        header_label = ttk.Label(
            self.dialog,
            text="Select columns to display in the table",
            font=("Helvetica", 12, "bold")
        )
        header_label.pack(pady=(20, 10))
        
        # Description
        desc_label = ttk.Label(
            self.dialog,
            text="Check/uncheck columns to show/hide them in the records table",
            font=("Helvetica", 9)
        )
        desc_label.pack(pady=(0, 20))
        
        # Main content frame
        content_frame = ttk.Frame(self.dialog)
        content_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        # Create scrollable frame for checkboxes
        canvas = tk.Canvas(content_frame)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create checkboxes for each column
        self.checkbox_vars = {}
        for col in self.columns:
            var = tk.BooleanVar(value=col in self.visible_columns)
            self.checkbox_vars[col] = var
            
            checkbox = ttk.Checkbutton(
                scrollable_frame,
                text=col,
                variable=var,
                command=self.update_visible_columns
            )
            checkbox.pack(anchor="w", pady=2)
        
        # Pack canvas and scrollbar in correct order
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.pack(fill=X, padx=20, pady=20)
        
        # Select All button
        select_all_btn = ttk.Button(
            buttons_frame,
            text="Select All",
            command=self.select_all,
            style="secondary.TButton"
        )
        select_all_btn.pack(side=LEFT, padx=(0, 10))
        
        # Deselect All button
        deselect_all_btn = ttk.Button(
            buttons_frame,
            text="Deselect All",
            command=self.deselect_all,
            style="secondary.TButton"
        )
        deselect_all_btn.pack(side=LEFT, padx=(0, 10))
        
        # Spacer
        ttk.Frame(buttons_frame).pack(side=LEFT, fill=X, expand=True)
        
        # OK button
        ok_btn = ttk.Button(
            buttons_frame,
            text="OK",
            command=self.ok_clicked,
            style="primary.TButton"
        )
        ok_btn.pack(side=RIGHT, padx=(10, 0))
        
        # Cancel button
        cancel_btn = ttk.Button(
            buttons_frame,
            text="Cancel",
            command=self.cancel_clicked,
            style="secondary.TButton"
        )
        cancel_btn.pack(side=RIGHT)
        
        # Bind Enter key to OK
        self.dialog.bind("<Return>", lambda e: self.ok_clicked())
        self.dialog.bind("<Escape>", lambda e: self.cancel_clicked())
        
        # Focus on dialog
        self.dialog.focus_set()
    
    def update_visible_columns(self):
        """Update the visible columns based on checkbox states."""
        self.visible_columns = [col for col, var in self.checkbox_vars.items() if var.get()]
    
    def select_all(self):
        """Select all columns."""
        for var in self.checkbox_vars.values():
            var.set(True)
        self.update_visible_columns()
    
    def deselect_all(self):
        """Deselect all columns."""
        for var in self.checkbox_vars.values():
            var.set(False)
        self.update_visible_columns()
    
    def ok_clicked(self):
        """Handle OK button click."""
        self.result = self.visible_columns
        self.dialog.destroy()
    
    def cancel_clicked(self):
        """Handle Cancel button click."""
        self.dialog.destroy()


class UsaVbdView(ttk.Frame):
    def __init__(self, master, config, on_navigate=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config = config
        self.on_navigate = on_navigate
        self.workflow = MasterReportsWorkflow(config.usa_hockey)
        self.data_processor = DataProcessor()
        self.current_data = None
        self.filtered_data = None
        self.current_file_path = None
        self.visible_columns = None
        self.build_ui()

    def build_ui(self):
        # Header
        header_label = ttk.Label(
            self,
            text="USA Hockey VBD (Verification Required) Data",
            font=("Helvetica", 14, "bold")
        )
        header_label.pack(pady=(20, 10))

        # Description
        desc_label = ttk.Label(
            self,
            text="Records requiring DOB verification (Member Type: 'P', DOB Verified: 'Not Verified')",
            font=("Helvetica", 10),
            foreground="gray"
        )
        desc_label.pack(pady=(0, 20))

        # Control panel
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=X, padx=20, pady=(0, 10))

        # Status label
        self.data_status_var = tk.StringVar(value="No data loaded")
        status_label = ttk.Label(
            control_frame,
            textvariable=self.data_status_var,
            font=("Helvetica", 9)
        )
        status_label.pack(side=LEFT)

        # Right side frame for record count and settings
        right_frame = ttk.Frame(control_frame)
        right_frame.pack(side=RIGHT)

        # Record count
        self.record_count_var = tk.StringVar()
        count_label = ttk.Label(
            right_frame,
            textvariable=self.record_count_var,
            font=("Helvetica", 9)
        )
        count_label.pack(side=LEFT, padx=(0, 10))

        # Settings icon button
        self.settings_btn = ttk.Button(
            right_frame,
            text="⚙",
            command=self.show_column_settings,
            style="secondary.TButton",
            width=3
        )
        self.settings_btn.pack(side=LEFT)

        # Top controls frame (50/50 split)
        top_controls_frame = ttk.Frame(self)
        top_controls_frame.pack(fill=X, padx=20, pady=(0, 10))
        top_controls_frame.columnconfigure(0, weight=1)
        top_controls_frame.columnconfigure(1, weight=1)

        # Pre-built Filters frame (left 50%)
        filters_frame = ttk.LabelFrame(top_controls_frame, text="Pre-built Filters", padding=10)
        filters_frame.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Filter buttons frame
        filter_buttons_frame = ttk.Frame(filters_frame)
        filter_buttons_frame.pack(fill=X)

        # Back to Master Data button
        self.back_to_master_btn = ttk.Button(
            filter_buttons_frame,
            text="Back to Master Data",
            command=self.navigate_to_master,
            style="info.TButton"
        )
        self.back_to_master_btn.pack(side=LEFT, padx=(0, 10))

        # Safe Sport Check button
        self.safe_sport_btn = ttk.Button(
            filter_buttons_frame,
            text="Safe Sport Check",
            command=self.navigate_to_safe_sport,
            style="warning.TButton"
        )
        self.safe_sport_btn.pack(side=LEFT, padx=(0, 10))

        # Controls frame (right 50%)
        controls_frame = ttk.LabelFrame(top_controls_frame, text="Controls", padding=10)
        controls_frame.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Export button
        self.export_btn = ttk.Button(
            controls_frame,
            text="Export VBD Data",
            command=self.export_vbd_data,
            style="success.TButton",
            state="disabled"
        )
        self.export_btn.pack(side=RIGHT)

        # Main content area
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)

        # Create treeview
        self.create_treeview(content_frame)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(content_frame, orient=VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(content_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid layout for treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Apply custom styling to headers
        apply_treeview_styling(self.tree)
        
        # Bind double-click to show details
        self.tree.bind("<Double-1>", self.show_row_details)

    def create_treeview(self, parent):
        """Create the treeview widget."""
        # Define columns (will be populated when data is loaded)
        columns = ("Loading...",)
        
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=20)
        
        # Configure column headings
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=150, minwidth=100)

    def load_data(self):
        """Load data from the master registration file."""
        try:
            # Try to get data from config first
            if hasattr(self.config, 'current_master_data') and self.config.current_master_data is not None:
                self.current_data = self.config.current_master_data
                self.current_file_path = getattr(self.config, 'current_master_file_path', None)
                self.apply_vbd_filter()
            else:
                # If no data in config, prompt user to load file
                file_path = filedialog.askopenfilename(
                    title="Select USA Hockey Master Registration File",
                    filetypes=[
                        ("Excel files", "*.xlsx"),
                        ("CSV files", "*.csv"),
                        ("All files", "*.*")
                    ],
                    initialdir=self.workflow.get_download_directory()
                )
                
                if file_path:
                    self.load_from_file(Path(file_path))
                    
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")

    def load_from_file(self, file_path: Path):
        """Load data from a specific file."""
        try:
            self.current_data = self.workflow.load_master_data(file_path)
            self.current_file_path = file_path
            self.apply_vbd_filter()
            
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def apply_vbd_filter(self):
        """Apply VBD filter: Member Type 'P' and DOB Verified 'Not Verified'."""
        if self.current_data is None:
            messagebox.showwarning("Warning", "No data to filter")
            return

        try:
            # Apply VBD filter
            self.filtered_data = self.current_data.copy()
            
            # Filter for Member Type 'P'
            if 'Member Type' in self.filtered_data.columns:
                self.filtered_data = self.filtered_data[
                    self.filtered_data['Member Type'] == 'P'
                ]
            elif 'member_type' in self.filtered_data.columns:
                self.filtered_data = self.filtered_data[
                    self.filtered_data['member_type'] == 'P'
                ]
            
            # Filter for DOB Verified 'Not Verified'
            if 'DOB Verified' in self.filtered_data.columns:
                self.filtered_data = self.filtered_data[
                    self.filtered_data['DOB Verified'] == 'Not Verified'
                ]
            elif 'dob_verified' in self.filtered_data.columns:
                self.filtered_data = self.filtered_data[
                    self.filtered_data['dob_verified'] == 'Not Verified'
                ]
            
            # Populate the table
            self.populate_table()
            
        except Exception as e:
            logger.error(f"Error applying VBD filter: {e}")
            messagebox.showerror("Error", f"Failed to apply VBD filter: {str(e)}")

    def populate_table(self):
        """Populate the table with filtered data."""
        if self.filtered_data is None or self.filtered_data.empty:
            self.data_status_var.set("No VBD records found")
            self.record_count_var.set("")
            self.export_btn.config(state="disabled")
            return

        # Get all columns
        all_columns = list(self.filtered_data.columns)
        
        # Load column visibility preferences
        saved_preferences = self.load_column_visibility_preferences()
        if saved_preferences:
            # Apply saved preferences
            visible_columns = []
            for col in all_columns:
                if col in saved_preferences:
                    if saved_preferences[col]:
                        visible_columns.append(col)
                else:
                    # New column, show by default
                    visible_columns.append(col)
            self.visible_columns = visible_columns
        else:
            # No saved preferences, set default visible columns
            if self.visible_columns is None:
                # Prioritize important columns for VBD workflow
                priority_columns = [
                    'Member ID', 'First Name', 'Last Name', 'DOB', 'DOB Verified',
                    'Member Type', 'Registration Date', 'Status'
                ]
                
                # Try to match priority columns with actual columns (case-insensitive)
                self.visible_columns = []
                for priority_col in priority_columns:
                    for col in all_columns:
                        if priority_col.lower() == col.lower():
                            self.visible_columns.append(col)
                            break
                
                # Add any remaining columns
                for col in all_columns:
                    if col not in self.visible_columns:
                        self.visible_columns.append(col)

        # Update the display
        self.update_display_with_filtered_data()

    def update_display_with_filtered_data(self):
        """Update the table display with filtered data."""
        if self.filtered_data is None:
            return

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get display columns
        display_columns = self.visible_columns if self.visible_columns else list(self.filtered_data.columns)
        
        # Configure treeview columns
        self.tree["columns"] = display_columns
        
        # Configure column headings
        for col in display_columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
        
        # Define priority column settings for VBD workflow
        priority_columns = {
            'Member ID': {'width': 120, 'minwidth': 100},
            'First Name': {'width': 120, 'minwidth': 100},
            'Last Name': {'width': 120, 'minwidth': 100},
            'DOB': {'width': 100, 'minwidth': 80},
            'DOB Verified': {'width': 100, 'minwidth': 80},
            'Member Type': {'width': 100, 'minwidth': 80},
            'Registration Date': {'width': 100, 'minwidth': 80},
            'Status': {'width': 100, 'minwidth': 80}
        }
        
        # Configure columns with global styling
        configure_columns_with_priority_styling(self.tree, display_columns, priority_columns)

        # Populate with data
        total_records = len(self.filtered_data)
        displayed_records = 0
        
        for idx, row in self.filtered_data.iterrows():
            values = []
            for col in display_columns:
                value = row.get(col, "")
                if pd.isna(value):
                    value = ""
                elif isinstance(value, (int, float)):
                    value = str(value)
                values.append(str(value))
            
            # Insert with alternating row colors
            tags = get_alternating_row_tags(displayed_records)
            self.tree.insert("", "end", values=values, tags=tags)
            displayed_records += 1

        # Apply alternating row colors
        apply_alternating_row_colors(self.tree)

        # Update status
        self.data_status_var.set("VBD data loaded")
        self.record_count_var.set(f"Showing {displayed_records:,} VBD records")
        
        # Enable export button
        self.export_btn.config(state="normal")
        
        # Apply styling to headers
        apply_treeview_styling(self.tree)

    def sort_by_column(self, column):
        """Sort the table by a column."""
        if self.filtered_data is None:
            return
            
        # Toggle sort order
        if hasattr(self, '_sort_reverse'):
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_reverse = False
            
        # Sort the data
        self.filtered_data = self.filtered_data.sort_values(by=column, ascending=not self._sort_reverse)
        
        # Re-populate the table
        self.update_display_with_filtered_data()

    def show_row_details(self, event):
        """Show detailed information for a selected row."""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        values = item['values']
        columns = self.tree["columns"]

        # Create detail window
        detail_window = tk.Toplevel(self)
        detail_window.title("VBD Record Details")
        detail_window.geometry("600x400")

        # Create text widget for details
        text_widget = tk.Text(detail_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(detail_window, orient=VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        text_widget.configure(yscrollcommand=scrollbar.set)

        # Populate with details
        for i, (col, val) in enumerate(zip(columns, values)):
            text_widget.insert(tk.END, f"{col}: {val}\n")
            if i < len(columns) - 1:
                text_widget.insert(tk.END, "-" * 50 + "\n")

        text_widget.config(state=tk.DISABLED)

    def export_vbd_data(self):
        """Export the VBD data to a file."""
        if self.filtered_data is None or self.filtered_data.empty:
            messagebox.showwarning("Warning", "No VBD data to export")
            return

        # Ask user for export format and location
        file_path = filedialog.asksaveasfilename(
            title="Export VBD Data",
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
                
                # Apply column visibility to export data
                if self.visible_columns is not None:
                    export_data = self.filtered_data[self.visible_columns]
                else:
                    export_data = self.filtered_data
                
                if output_path.suffix.lower() == '.xlsx':
                    success = self.workflow.export_to_excel(export_data, output_path)
                else:
                    # Export as CSV
                    export_data.to_csv(output_path, index=False)
                    success = True
                
                if success:
                    messagebox.showinfo("Success", f"VBD data exported successfully to:\n{output_path}")
                else:
                    messagebox.showerror("Error", "Failed to export VBD data")
                    
            except Exception as e:
                logger.error(f"Export error: {e}")
                messagebox.showerror("Error", f"Failed to export VBD data: {str(e)}")

    def navigate_to_master(self):
        """Navigate to the Master (USA) screen."""
        if self.on_navigate:
            self.on_navigate("Master (USA)")
        else:
            logger.warning("Navigation callback not available")

    def navigate_to_safe_sport(self):
        """Navigate to the Safe Sport (USA) screen."""
        if self.on_navigate:
            self.on_navigate("Safe Sport (USA)")
        else:
            logger.warning("Navigation callback not available")

    def load_column_visibility_preferences(self):
        """Load column visibility preferences from preferences.yaml."""
        try:
            current_dir = Path(__file__).parent.parent.parent / 'config'
            preferences_path = current_dir / 'preferences.yaml'
            
            if preferences_path.exists():
                from ruamel.yaml import YAML
                yaml = YAML(typ='safe')
                with open(preferences_path) as f:
                    preferences = yaml.load(f) or {}
                
                return preferences.get('usa_vbd_column_visibility', {})
        except Exception as e:
            logger.warning(f"Failed to load column visibility preferences: {e}")
        
        return {}
    
    def save_column_visibility_preferences(self, column_visibility):
        """Save column visibility preferences to preferences.yaml."""
        try:
            current_dir = Path(__file__).parent.parent.parent / 'config'
            preferences_path = current_dir / 'preferences.yaml'
            
            # Load existing preferences
            preferences = {}
            if preferences_path.exists():
                from ruamel.yaml import YAML
                yaml = YAML(typ='safe')
                with open(preferences_path) as f:
                    preferences = yaml.load(f) or {}
            
            # Update column visibility preferences
            preferences['usa_vbd_column_visibility'] = column_visibility
            
            # Save updated preferences
            yaml = YAML(typ='safe')
            with open(preferences_path, 'w') as f:
                yaml.dump(preferences, f)
            
            logger.info("Column visibility preferences saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save column visibility preferences: {e}")
            messagebox.showerror("Error", f"Failed to save column visibility preferences: {str(e)}")

    def show_column_settings(self):
        """Show the column visibility settings dialog."""
        if self.filtered_data is None or self.filtered_data.empty:
            messagebox.showwarning("Warning", "No data loaded. Please load data first.")
            return
        
        # Get current columns
        all_columns = list(self.filtered_data.columns)
        
        # Load saved preferences
        saved_preferences = self.load_column_visibility_preferences()
        
        # Determine visible columns (use saved preferences or all columns if none saved)
        if saved_preferences:
            # Use saved preferences, but ensure all current columns are included
            visible_columns = []
            for col in all_columns:
                if col in saved_preferences:
                    if saved_preferences[col]:
                        visible_columns.append(col)
                else:
                    # New column, show by default
                    visible_columns.append(col)
        else:
            # No saved preferences, show all columns
            visible_columns = all_columns.copy()
        
        # Show dialog
        dialog = ColumnSettingsDialog(self, all_columns, visible_columns)
        
        if dialog.result is not None:
            # Save preferences
            column_visibility = {col: col in dialog.result for col in all_columns}
            self.save_column_visibility_preferences(column_visibility)
            
            # Update visible columns
            self.visible_columns = dialog.result
            
            # Refresh the display
            self.update_display_with_filtered_data()

    def refresh(self):
        """Refresh the view and check for data."""
        # Try to load data from config first
        if hasattr(self.config, 'current_master_data') and self.config.current_master_data is not None:
            self.current_data = self.config.current_master_data
            self.current_file_path = getattr(self.config, 'current_master_file_path', None)
            self.apply_vbd_filter()
        else:
            self.data_status_var.set("No data loaded")
            self.record_count_var.set("")
            self.export_btn.config(state="disabled") 