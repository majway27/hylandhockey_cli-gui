import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk

class DashboardView(ttk.Frame):
    def __init__(self, master, config, order_verification, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config = config
        self.order_verification = order_verification
        self.pending_orders_var = tk.StringVar(value="Loading...")
        self.total_orders_var = tk.StringVar(value="Loading...")
        self.mode_label = None
        self.build_ui()
        self.refresh()

    def build_ui(self):
        welcome_label = ttk.Label(
            self,
            text="Welcome to the Registrar Operations System",
            font=("Helvetica", 12)
        )
        welcome_label.pack(pady=(20, 5))
        self.mode_label = ttk.Label(
            self,
            text="",
            font=("Helvetica", 10, "bold"),
            foreground="red"
        )
        self.mode_label.pack(pady=(0, 20))
        stats_frame = ttk.LabelFrame(self, text="Quick Statistics", padding=10)
        stats_frame.pack(fill=X, pady=10)
        ttk.Label(stats_frame, text="Pending Orders:").grid(row=0, column=0, sticky=W, padx=(0, 10))
        ttk.Label(stats_frame, textvariable=self.pending_orders_var).grid(row=0, column=1, sticky=W)
        ttk.Label(stats_frame, text="Total Orders:").grid(row=1, column=0, sticky=W, padx=(0, 10))
        ttk.Label(stats_frame, textvariable=self.total_orders_var).grid(row=1, column=1, sticky=W)
        actions_frame = ttk.Frame(self)
        actions_frame.pack(pady=20)
        refresh_btn = ttk.Button(
            actions_frame,
            text="Refresh Dashboard",
            command=self.refresh,
            style="primary.TButton"
        )
        refresh_btn.pack(side=LEFT, padx=(0, 10))

    def refresh(self):
        mode_text = "TEST MODE" if self.config.is_test_mode else "PRODUCTION MODE"
        self.mode_label.config(
            text=f"Running in: {mode_text}",
            foreground="red" if self.config.is_test_mode else "green"
        )
        pending_orders = self.order_verification.get_pending_orders()
        self.pending_orders_var.set(str(len(pending_orders)))
        self.total_orders_var.set(str(len(pending_orders))) 