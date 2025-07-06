import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk

class NavigationPanel(ttk.Frame):
    def __init__(self, master, on_select, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_select = on_select
        self.selected = tk.StringVar()
        # Set background color to a slightly darker grey
        self.configure(style="secondary.TFrame")
        # Set fixed width to prevent resizing
        self.configure(width=200)
        self.pack_propagate(False)  # Prevent frame from resizing based on content
        self.build_menu()

    def build_menu(self):
        # Top-level menu items
        menu_items = [
            ("Home", ["Dashboard"]),
            ("Jersey", ["Single (Order)", "Batch (Orders)"]),
            ("USA Hockey", ["Sync", "Master"]),
            ("Utility", ["Configuration", "Logs"]),
        ]
        for section, subitems in menu_items:
            section_label = ttk.Label(self, text=section, font=("Helvetica", 12, "bold"))
            section_label.pack(anchor="w", pady=(10, 0), padx=10)
            for item in subitems:
                btn = ttk.Button(self, text=item, command=lambda i=item: self.select(i), width=16)
                btn.pack(anchor="w", padx=20, pady=2, fill="x")

    def select(self, item):
        self.selected.set(item)
        if self.on_select:
            self.on_select(item) 