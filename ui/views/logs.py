import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
import threading
import time

class LogsView(ttk.Frame):
    def __init__(self, master, log_viewer, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.log_viewer = log_viewer
        self.log_file_var = tk.StringVar()
        self.log_level_var = tk.StringVar(value="ALL")
        self.log_search_var = tk.StringVar()
        self.log_status_var = tk.StringVar(value="Ready")
        self.search_after_id = None
        self.build_ui()
        self.refresh()

    def build_ui(self):
        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill=X, pady=(0, 10), padx=20)
        file_frame = ttk.Frame(controls_frame)
        file_frame.pack(side=LEFT, fill=X, expand=True)
        ttk.Label(file_frame, text="Log File:").pack(side=LEFT)
        self.log_file_combo = ttk.Combobox(
            file_frame,
            textvariable=self.log_file_var,
            width=30,
            state="readonly"
        )
        self.log_file_combo.pack(side=LEFT, padx=(10, 0))
        self.log_file_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh())
        filter_frame = ttk.Frame(controls_frame)
        filter_frame.pack(side=LEFT, padx=(20, 0))
        ttk.Label(filter_frame, text="Level:").pack(side=LEFT)
        level_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.log_level_var,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            width=10,
            state="readonly"
        )
        level_combo.pack(side=LEFT, padx=(10, 0))
        level_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh())
        
        ttk.Label(filter_frame, text="Search:").pack(side=LEFT, padx=(20, 0))
        search_entry = ttk.Entry(filter_frame, textvariable=self.log_search_var, width=20)
        search_entry.pack(side=LEFT, padx=(10, 0))
        search_entry.bind('<KeyRelease>', self.on_search_change)
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(side=RIGHT)
        ttk.Button(
            button_frame,
            text="Refresh",
            command=self.refresh,
            style="info.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        ttk.Button(
            button_frame,
            text="Clear Filters",
            command=self.clear_log_filters,
            style="secondary.TButton"
        ).pack(side=LEFT)
        display_frame = ttk.Frame(self)
        display_frame.pack(fill=BOTH, expand=True, padx=20)
        text_frame = ttk.Frame(display_frame)
        text_frame.pack(fill=BOTH, expand=True)
        self.log_text = tk.Text(
            text_frame,
            wrap=tk.NONE,
            font=("Consolas", 9),
            bg="#f8f9fa",
            fg="#212529"
        )
        v_scrollbar = ttk.Scrollbar(text_frame, orient=VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=v_scrollbar.set)
        h_scrollbar = ttk.Scrollbar(text_frame, orient=HORIZONTAL, command=self.log_text.xview)
        self.log_text.configure(xscrollcommand=h_scrollbar.set)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=X, pady=(10, 0), padx=20)
        log_status_label = ttk.Label(
            status_frame,
            textvariable=self.log_status_var,
            relief=SUNKEN,
            anchor=W
        )
        log_status_label.pack(fill=X)

    def refresh(self):
        """Load and display logs based on current filters."""
        try:
            # Clear the text widget
            self.log_text.delete(1.0, tk.END)
            
            # Update log file list
            log_files = self.log_viewer.list_log_files()
            if not log_files:
                self.log_text.insert(tk.END, "No log files found in the logs directory.\n")
                self.log_status_var.set("No log files available")
                return
            
            # Update combo box with available log files
            file_names = [f.name for f in log_files]
            self.log_file_combo['values'] = file_names
            
            # If no file is selected, select the most recent one
            if not self.log_file_var.get() or self.log_file_var.get() not in file_names:
                if file_names:
                    self.log_file_var.set(file_names[0])
            
            selected_file = self.log_file_var.get()
            if not selected_file:
                self.log_text.insert(tk.END, "Please select a log file to view.\n")
                self.log_status_var.set("No file selected")
                return
            
            # Get filter values
            level_filter = self.log_level_var.get()
            search_filter = self.log_search_var.get()
            
            # Apply level filter (convert "ALL" to None)
            level = None if level_filter == "ALL" else level_filter
            
            # Read and filter the log file directly
            log_file_path = self.log_viewer.log_dir / selected_file
            
            if not log_file_path.exists():
                self.log_text.insert(tk.END, f"Log file not found: {log_file_path}\n")
                self.log_status_var.set(f"File not found: {selected_file}")
                return
            
            try:
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    
                    # Apply filters
                    filtered_lines = []
                    for line in all_lines:
                        # Check level filter
                        if level and level.upper() not in line.upper():
                            continue
                        
                        # Check search filter
                        if search_filter and search_filter.lower() not in line.lower():
                            continue
                        
                        filtered_lines.append(line)
                    
                    # Display results
                    if not filtered_lines:
                        self.log_text.insert(tk.END, "No log entries match the specified filters.\n")
                        self.log_status_var.set(f"No matching entries in {selected_file}")
                    else:
                        # Insert all filtered lines
                        for line in filtered_lines:
                            self.log_text.insert(tk.END, line)
                        
                        # Add summary
                        summary = f"\n--- End of log (showing {len(filtered_lines)} of {len(all_lines)} lines) ---\n"
                        self.log_text.insert(tk.END, summary)
                        
                        self.log_status_var.set(f"Loaded {selected_file} - {len(filtered_lines)} of {len(all_lines)} lines")
                        
            except Exception as e:
                self.log_text.insert(tk.END, f"Error reading log file: {str(e)}\n")
                self.log_status_var.set(f"Error reading {selected_file}")
                
        except Exception as e:
            self.log_text.insert(tk.END, f"Error loading logs: {str(e)}\n")
            self.log_status_var.set(f"Error: {str(e)}")

    def on_search_change(self, event=None):
        """Handle search text changes with a small delay to avoid too frequent refreshes."""
        if self.search_after_id:
            self.after_cancel(self.search_after_id)
        self.search_after_id = self.after(500, self.refresh)  # 500ms delay

    def clear_log_filters(self):
        self.log_level_var.set("ALL")
        self.log_search_var.set("")
        self.refresh() 