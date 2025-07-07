import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ui.navigation import NavigationPanel
from ui.views.dashboard import DashboardView
from ui.views.orders import OrdersView
from ui.views.batch_orders import BatchOrdersView
from ui.views.email import EmailView
from ui.views.configuration import ConfigurationView
from ui.views.logs import LogsView
from ui.views.usa_import import UsaImportView
from ui.views.usa_master import UsaMasterView
from ui.views.usa_vbd import UsaVbdView
from ui.views.usa_safe import UsaSafeView

class RegistrarApp:
    def __init__(self, config, order_verification, log_viewer):
        self.config = config
        self.order_verification = order_verification
        self.log_viewer = log_viewer
        self.root = ttk.Window(
            title=f"Registrar Operations Center: {self.config.organization_name}",
            themename="united",
            size=(1800, 1200),
            resizable=(True, True)
        )
        self.status_var = tk.StringVar(value="Ready")
        self.views = {}
        self.current_view = None
        self.setup_ui()

    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding=0)
        main_frame.pack(fill=BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=X, pady=(0, 0))
        title_label = ttk.Label(
            header_frame,
            text=f"Registrar Operations Center: {self.config.organization_name}",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(18, 18), padx=10)

        # Two-column layout
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=BOTH, expand=True)
        content_frame.columnconfigure(0, weight=1, minsize=192)
        content_frame.columnconfigure(1, weight=17)
        content_frame.rowconfigure(0, weight=1)

        # Navigation panel (left)
        nav_panel = NavigationPanel(content_frame, on_select=self.show_view)
        nav_panel.grid(row=0, column=0, sticky="nswe")

        # Content area (right)
        self.content_area = ttk.Frame(content_frame)
        self.content_area.grid(row=0, column=1, sticky="nswe")
        self.content_area.rowconfigure(0, weight=1)
        self.content_area.columnconfigure(0, weight=1)

        # Instantiate all views but don't pack them yet
        self.views = {
            "Dashboard": DashboardView(self.content_area, self.config, self.order_verification),
            "Single (Order)": OrdersView(self.content_area, self.config, self.order_verification, on_order_select=self.show_email_view),
            "Batch (Orders)": BatchOrdersView(self.content_area, self.config, self.order_verification),
            "Import (USA)": UsaImportView(self.content_area, self.config, on_navigate=self.show_view),
            "Master (USA)": UsaMasterView(self.content_area, self.config, on_navigate=self.show_view),
            "VBD (USA)": UsaVbdView(self.content_area, self.config, on_navigate=self.show_view),
            "Safe Sport (USA)": UsaSafeView(self.content_area, self.config, on_navigate=self.show_view),
            "Email": EmailView(self.content_area, self.config, self.order_verification),
            "Configuration": ConfigurationView(self.content_area, self.config),
            "Logs": LogsView(self.content_area, self.log_viewer),
        }
        # Show Dashboard by default
        self.show_view("Dashboard")

        # Status bar
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=SUNKEN,
            anchor=W
        )
        status_bar.pack(side=BOTTOM, fill=X, pady=(0, 0))

    def show_view(self, view_name):
        if self.current_view:
            self.current_view.pack_forget()
        view = self.views.get(view_name)
        if view:
            view.pack(fill=BOTH, expand=True)
            self.current_view = view
            self.status_var.set(f"Viewing: {view_name}")
            
            # Refresh data when switching to views that display order information
            if view_name in ["Dashboard", "Single (Order)", "Batch (Orders)", "Master (USA)", "VBD (USA)", "Safe Sport (USA)"] and hasattr(view, 'refresh'):
                view.refresh()

    def show_email_view(self, order=None):
        """Switch to email view, optionally with order details populated."""
        if self.current_view:
            self.current_view.pack_forget()
        
        email_view = self.views.get("Email")
        if email_view:
            email_view.pack(fill=BOTH, expand=True)
            self.current_view = email_view
            self.status_var.set("Viewing: Email")
            
            # If an order was provided, populate the email view
            if order and hasattr(email_view, 'populate_from_order'):
                email_view.populate_from_order(order)

    def run(self):
        self.root.mainloop() 