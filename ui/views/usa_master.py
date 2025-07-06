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
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
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


class UsaMasterView(ttk.Frame):
    def __init__(self, master, config, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config = config
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
            text="USA Hockey Master Registration Data",
            font=("Helvetica", 14, "bold")
        )
        header_label.pack(pady=(20, 10))

        # Description
        desc_label = ttk.Label(
            self,
            text="View and filter master registration records",
            font=("Helvetica", 10)
        )
        desc_label.pack(pady=(0, 20))

        # Main content frame
        content_frame = ttk.LabelFrame(self, text="Registration Records", padding=20)
        content_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)

        # Data status frame
        self.data_status_frame = ttk.Frame(content_frame)
        self.data_status_frame.pack(fill=X, pady=(0, 20))

        # Data status label
        self.data_status_var = tk.StringVar(value="No data loaded")
        self.data_status_label = ttk.Label(
            self.data_status_frame,
            textvariable=self.data_status_var,
            font=("Helvetica", 10, "bold")
        )
        self.data_status_label.pack(side=LEFT)

        # Right side frame for record count and settings
        right_frame = ttk.Frame(self.data_status_frame)
        right_frame.pack(side=RIGHT)

        # Record count label
        self.record_count_var = tk.StringVar(value="")
        self.record_count_label = ttk.Label(
            right_frame,
            textvariable=self.record_count_var,
            font=("Helvetica", 9)
        )
        self.record_count_label.pack(side=LEFT, padx=(0, 10))

        # Settings icon button
        self.settings_btn = ttk.Button(
            right_frame,
            text="⚙",
            command=self.show_column_settings,
            style="secondary.TButton",
            width=3
        )
        self.settings_btn.pack(side=LEFT)

        # Filters frame
        filters_frame = ttk.LabelFrame(content_frame, text="Pre-built Filters", padding=10)
        filters_frame.pack(fill=X, pady=(0, 20))

        # Filter buttons frame
        filter_buttons_frame = ttk.Frame(filters_frame)
        filter_buttons_frame.pack(fill=X)

        # Process-oriented filter buttons
        self.active_filter_btn = ttk.Button(
            filter_buttons_frame,
            text="Active Registrations",
            command=lambda: self.apply_filter("active"),
            style="success.TButton"
        )
        self.active_filter_btn.pack(side=LEFT, padx=(0, 10))

        self.pending_filter_btn = ttk.Button(
            filter_buttons_frame,
            text="Pending Review",
            command=lambda: self.apply_filter("pending"),
            style="warning.TButton"
        )
        self.pending_filter_btn.pack(side=LEFT, padx=(0, 10))

        self.completed_filter_btn = ttk.Button(
            filter_buttons_frame,
            text="Completed",
            command=lambda: self.apply_filter("completed"),
            style="info.TButton"
        )
        self.completed_filter_btn.pack(side=LEFT, padx=(0, 10))

        # Clear filters button
        self.clear_filters_btn = ttk.Button(
            filter_buttons_frame,
            text="Clear Filters",
            command=self.clear_filters,
            style="secondary.TButton"
        )
        self.clear_filters_btn.pack(side=LEFT, padx=(0, 10))

        # Custom filter frame
        custom_filter_frame = ttk.LabelFrame(content_frame, text="Custom Filter", padding=10)
        custom_filter_frame.pack(fill=X, pady=(0, 20))

        # Filter controls
        filter_controls_frame = ttk.Frame(custom_filter_frame)
        filter_controls_frame.pack(fill=X)

        # Column selector
        ttk.Label(filter_controls_frame, text="Column:").pack(side=LEFT, padx=(0, 5))
        self.column_var = tk.StringVar()
        self.column_combo = ttk.Combobox(
            filter_controls_frame,
            textvariable=self.column_var,
            state="readonly",
            width=20
        )
        self.column_combo.pack(side=LEFT, padx=(0, 10))

        # Value entry
        ttk.Label(filter_controls_frame, text="Value:").pack(side=LEFT, padx=(0, 5))
        self.filter_value_var = tk.StringVar()
        self.filter_value_entry = ttk.Entry(
            filter_controls_frame,
            textvariable=self.filter_value_var,
            width=20
        )
        self.filter_value_entry.pack(side=LEFT, padx=(0, 10))

        # Apply custom filter button
        self.apply_custom_filter_btn = ttk.Button(
            filter_controls_frame,
            text="Apply Filter",
            command=self.apply_custom_filter,
            style="primary.TButton"
        )
        self.apply_custom_filter_btn.pack(side=LEFT)

        # Table frame
        table_frame = ttk.Frame(content_frame)
        table_frame.pack(fill=BOTH, expand=True, pady=(0, 20))

        # Create treeview for data display
        self.create_treeview(table_frame)

        # Action buttons frame
        actions_frame = ttk.Frame(content_frame)
        actions_frame.pack(side=BOTTOM, fill=X, pady=(20, 0))

        # Load data button
        self.load_data_btn = ttk.Button(
            actions_frame,
            text="Load Data",
            command=self.load_data,
            style="primary.TButton"
        )
        self.load_data_btn.pack(side=LEFT, padx=(0, 10))

        # Export filtered button
        self.export_filtered_btn = ttk.Button(
            actions_frame,
            text="Export Filtered",
            command=self.export_filtered_data,
            style="secondary.TButton",
            state="disabled"
        )
        self.export_filtered_btn.pack(side=LEFT, padx=(0, 10))

        # Refresh button
        refresh_btn = ttk.Button(
            actions_frame,
            text="Refresh",
            command=self.refresh,
            style="secondary.TButton"
        )
        refresh_btn.pack(side=LEFT)

        # Initialize
        self.refresh()

    def create_treeview(self, parent):
        """Create the treeview for displaying data."""
        # Create frame for treeview and scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=True)

        # Create treeview
        self.tree = ttk.Treeview(tree_frame, show="headings", height=15)
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack treeview and scrollbars
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)

        # Bind double-click event for row details
        self.tree.bind("<Double-1>", self.show_row_details)

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
                
                return preferences.get('usa_master_column_visibility', {})
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
            preferences['usa_master_column_visibility'] = column_visibility
            
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
        if self.current_data is None or self.current_data.empty:
            messagebox.showwarning("Warning", "No data loaded. Please load data first.")
            return
        
        # Get current columns
        all_columns = list(self.current_data.columns)
        
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

    def load_data(self):
        """Load data from the import view or from a file."""
        # First try to get data from config (set by import view)
        if hasattr(self.config, 'current_master_data') and self.config.current_master_data is not None:
            self.current_data = self.config.current_master_data
            self.current_file_path = getattr(self.config, 'current_master_file_path', None)
            self.populate_table()
            return

        # If no data in config, ask user to select a file
        file_path = filedialog.askopenfilename(
            title="Select Master Report File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=self.workflow.get_download_directory()
        )
        
        if file_path:
            self.load_from_file(Path(file_path))

    def load_from_file(self, file_path: Path):
        """Load data from a file."""
        try:
            # Process the data
            df = self.workflow.process_master_report(file_path)
            
            if df is not None:
                self.current_data = df
                self.current_file_path = file_path
                self.populate_table()
                messagebox.showinfo("Success", f"Loaded {len(df):,} records from master report")
            else:
                messagebox.showerror("Error", "Failed to process the master report file")
                
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")

    def populate_table(self):
        """Populate the treeview with data."""
        if self.current_data is None or self.current_data.empty:
            self.data_status_var.set("No data available")
            self.record_count_var.set("")
            return

        # Set filtered data to current data initially
        self.filtered_data = self.current_data.copy()
        
        # Load column visibility preferences
        saved_preferences = self.load_column_visibility_preferences()
        if saved_preferences:
            # Apply saved preferences
            visible_columns = []
            for col in self.current_data.columns:
                if col in saved_preferences:
                    if saved_preferences[col]:
                        visible_columns.append(col)
                else:
                    # New column, show by default
                    visible_columns.append(col)
            self.visible_columns = visible_columns
        else:
            # No saved preferences, show all columns
            self.visible_columns = list(self.current_data.columns)
        
        # Update the display with the data
        self.update_display_with_filtered_data()

    def update_display_with_filtered_data(self):
        """Update the table display with filtered data."""
        if self.filtered_data is None:
            return

        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Determine which columns to show
        if self.visible_columns is None:
            # No visibility preferences set, show all columns
            display_columns = list(self.filtered_data.columns)
        else:
            # Use visibility preferences
            display_columns = [col for col in self.filtered_data.columns if col in self.visible_columns]

        # Set up columns
        self.tree["columns"] = display_columns
        
        # Configure column headings
        for col in display_columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            # Set reasonable column widths
            max_width = max(len(str(col)), 
                          self.filtered_data[col].astype(str).str.len().max() if not self.filtered_data[col].empty else 0)
            width = min(max_width * 10, 300)  # Cap at 300 pixels
            self.tree.column(col, width=width, minwidth=50, anchor="center")

        # Populate with data (limit to first 1000 rows for performance)
        display_data = self.filtered_data.head(1000)
        for idx, row in display_data.iterrows():
            values = []
            for col in display_columns:
                value = row[col]
                # Check for various forms of NaN/null values
                if (pd.isna(value) or 
                    str(value).lower() in ['nan', 'none', 'null', ''] or
                    str(value).strip() == ''):
                    values.append("")
                else:
                    values.append(str(value))
            self.tree.insert("", "end", values=values, tags=(idx,))

        # Update status
        total_records = len(self.current_data)
        filtered_records = len(self.filtered_data)
        displayed_records = len(display_data)
        
        if self.current_file_path:
            self.data_status_var.set(f"Data loaded from {self.current_file_path.name}")
        else:
            self.data_status_var.set("Data loaded")
            
        if filtered_records == total_records:
            self.record_count_var.set(f"Showing {displayed_records:,} of {total_records:,} records")
        else:
            self.record_count_var.set(f"Showing {displayed_records:,} of {filtered_records:,} filtered records (from {total_records:,} total)")
        
        # Enable export button
        self.export_filtered_btn.config(state="normal")
        
        # Update column selector (only show visible columns)
        self.column_combo['values'] = display_columns
        if display_columns:
            self.column_combo.set(display_columns[0])

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

    def apply_filter(self, filter_type):
        """Apply pre-built filters."""
        if self.current_data is None:
            messagebox.showwarning("Warning", "No data to filter")
            return

        try:
            if filter_type == "active":
                # Filter for active registrations (customize based on your data structure)
                self.filtered_data = self.current_data.copy()
                # Example: filter by status or registration date
                if 'status' in self.current_data.columns:
                    self.filtered_data = self.filtered_data[
                        self.filtered_data['status'].str.contains('active', case=False, na=False)
                    ]
                elif 'registration_date' in self.current_data.columns:
                    # Show recent registrations (last 30 days)
                    recent_date = pd.Timestamp.now() - pd.Timedelta(days=30)
                    self.filtered_data = self.filtered_data[
                        pd.to_datetime(self.filtered_data['registration_date'], errors='coerce') >= recent_date
                    ]
                
            elif filter_type == "pending":
                # Filter for pending review (customize based on your data structure)
                self.filtered_data = self.current_data.copy()
                if 'status' in self.current_data.columns:
                    self.filtered_data = self.filtered_data[
                        self.filtered_data['status'].str.contains('pending', case=False, na=False)
                    ]
                
            elif filter_type == "completed":
                # Filter for completed registrations (customize based on your data structure)
                self.filtered_data = self.current_data.copy()
                if 'status' in self.current_data.columns:
                    self.filtered_data = self.filtered_data[
                        self.filtered_data['status'].str.contains('completed', case=False, na=False)
                    ]

            # Update the display
            self.update_display_with_filtered_data()
            
        except Exception as e:
            logger.error(f"Error applying filter: {e}")
            messagebox.showerror("Error", f"Failed to apply filter: {str(e)}")

    def apply_custom_filter(self):
        """Apply custom filter based on user input."""
        if self.current_data is None:
            messagebox.showwarning("Warning", "No data to filter")
            return

        column = self.column_var.get()
        value = self.filter_value_var.get()

        if not column or not value:
            messagebox.showwarning("Warning", "Please select a column and enter a value")
            return

        try:
            # Apply the filter
            self.filtered_data = self.current_data[
                self.current_data[column].astype(str).str.contains(value, case=False, na=False)
            ]
            
            # Update the display
            self.update_display_with_filtered_data()
            
        except Exception as e:
            logger.error(f"Error applying custom filter: {e}")
            messagebox.showerror("Error", f"Failed to apply filter: {str(e)}")

    def clear_filters(self):
        """Clear all filters and show all data."""
        if self.current_data is not None:
            self.filtered_data = self.current_data.copy()
            self.update_display_with_filtered_data()
            self.filter_value_var.set("")

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
        detail_window.title("Record Details")
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

    def export_filtered_data(self):
        """Export the filtered data to a file."""
        if self.filtered_data is None or self.filtered_data.empty:
            messagebox.showwarning("Warning", "No data to export")
            return

        # Ask user for export format and location
        file_path = filedialog.asksaveasfilename(
            title="Export Filtered Data",
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
                    messagebox.showinfo("Success", f"Filtered data exported successfully to:\n{output_path}")
                else:
                    messagebox.showerror("Error", "Failed to export data")
                    
            except Exception as e:
                logger.error(f"Export error: {e}")
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def refresh(self):
        """Refresh the view and check for data."""
        # Try to load data from config first
        if hasattr(self.config, 'current_master_data') and self.config.current_master_data is not None:
            self.current_data = self.config.current_master_data
            self.current_file_path = getattr(self.config, 'current_master_file_path', None)
            self.populate_table()
        else:
            self.data_status_var.set("No data loaded")
            self.record_count_var.set("")
            self.export_filtered_btn.config(state="disabled") 