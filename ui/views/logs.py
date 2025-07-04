import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk

class LogsView(ttk.Frame):
    def __init__(self, master, log_viewer, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.log_viewer = log_viewer
        self.log_file_var = tk.StringVar()
        self.log_level_var = tk.StringVar(value="ALL")
        self.log_search_var = tk.StringVar()
        self.log_status_var = tk.StringVar(value="Ready")
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
        ttk.Label(filter_frame, text="Search:").pack(side=LEFT, padx=(20, 0))
        search_entry = ttk.Entry(filter_frame, textvariable=self.log_search_var, width=20)
        search_entry.pack(side=LEFT, padx=(10, 0))
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
        # Placeholder for integration
        pass

    def clear_log_filters(self):
        self.log_level_var.set("ALL")
        self.log_search_var.set("")
        self.refresh() 