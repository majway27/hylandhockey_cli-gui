import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from ui.utils.styling import apply_treeview_styling, configure_columns_with_priority_styling, apply_alternating_row_colors, get_alternating_row_tags

class OrdersView(ttk.Frame):
    def __init__(self, master, config, order_verification, on_order_select=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config = config
        self.order_verification = order_verification
        self.on_order_select = on_order_select
        self.orders_tree = None
        self.details_text = None
        self.orders_list = []
        self.order_item_map = {}
        self.build_ui()
        self.refresh()

    def build_ui(self):
        toolbar_frame = ttk.Frame(self)
        toolbar_frame.pack(fill=X, pady=(0, 10), padx=20)
        ttk.Button(
            toolbar_frame,
            text="Refresh Orders",
            command=self.refresh,
            style="info.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        ttk.Button(
            toolbar_frame,
            text="Get Next Order",
            command=self.get_next_order,
            style="success.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        ttk.Button(
            toolbar_frame,
            text="Preview Email",
            command=self.preview_email,
            style="warning.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=BOTH, expand=True, padx=20)
        columns = (
            'name', 'jersey_name', 'jersey_number', 'jersey_size', 
            'jersey_type', 'contacted', 'confirmed'
        )
        self.orders_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            height=15
        )
        for col in columns:
            self.orders_tree.heading(col, text=col.replace('_', ' ').title())
        
        # Configure columns with global styling
        configure_columns_with_priority_styling(self.orders_tree, columns)
        scrollbar = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.orders_tree.yview)
        self.orders_tree.configure(yscrollcommand=scrollbar.set)
        self.orders_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Apply custom styling to headers
        apply_treeview_styling(self.orders_tree)
        
        self.orders_tree.bind('<<TreeviewSelect>>', self.handle_order_select)
        details_frame = ttk.LabelFrame(self, text="Order Details", padding=10)
        details_frame.pack(fill=X, pady=(10, 0), padx=20)
        self.details_text = tk.Text(details_frame, height=8, wrap=tk.WORD)
        self.details_text.pack(fill=X)



    def refresh(self):
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
        pending_orders = self.order_verification.get_pending_orders()
        self.orders_list = pending_orders
        self.order_item_map = {}
        for i, order in enumerate(pending_orders):
            contacted_status = "Yes" if order.contacted else "No"
            confirmed_status = "Yes" if order.confirmed else "No"
            
            # Insert with alternating row colors
            tags = get_alternating_row_tags(i)
            item_id = self.orders_tree.insert('', END, values=(
                order.participant_full_name,
                order.jersey_name,
                order.jersey_number,
                order.jersey_size,
                order.jersey_type,
                contacted_status,
                confirmed_status
            ), tags=tags)
            self.order_item_map[item_id] = order
        
        # Apply alternating row colors
        apply_alternating_row_colors(self.orders_tree)

    def handle_order_select(self, event):
        selection = self.orders_tree.selection()
        if selection:
            item_id = selection[0]
            order = self.order_item_map.get(item_id)
            if order:
                details = f"Participant: {order.participant_full_name}\n"
                details += f"Jersey Name: {order.jersey_name}\n"
                details += f"Jersey Number: {order.jersey_number}\n"
                details += f"Jersey Size: {order.jersey_size}\n"
                details += f"Jersey Type: {order.jersey_type}\n"
                details += f"Contacted: {order.contacted}\n"
                details += f"Confirmed: {order.confirmed}\n"
                self.details_text.delete(1.0, tk.END)
                self.details_text.insert(1.0, details)
                # Automatically switch to email view when order is selected
                if self.on_order_select:
                    self.on_order_select(order)

    def preview_email(self):
        """Preview email for the currently selected order."""
        selection = self.orders_tree.selection()
        if selection:
            item_id = selection[0]
            order = self.order_item_map.get(item_id)
            if order and self.on_order_select:
                self.on_order_select(order)
        else:
            # If no order is selected, try to get the next order
            self.get_next_order()

    def get_next_order(self):
        """Get the next pending order and select it in the treeview."""
        try:
            # Get the next pending order
            next_order = self.order_verification.get_next_pending_order()
            
            if next_order is None:
                # Show message that no pending orders are available
                self.details_text.delete(1.0, tk.END)
                self.details_text.insert(1.0, "No pending orders available.")
                return
            
            # Refresh the orders list to ensure we have the latest data
            self.refresh()
            
            # Find the order in the treeview and select it
            for item_id, order in self.order_item_map.items():
                if (order.participant_full_name == next_order.participant_full_name and
                    order.jersey_name == next_order.jersey_name and
                    order.jersey_number == next_order.jersey_number):
                    
                    # Select the item in the treeview
                    self.orders_tree.selection_set(item_id)
                    self.orders_tree.see(item_id)  # Ensure the item is visible
                    
                    # Update the details text
                    self.handle_order_select(None)
                    
                    # Call the callback if provided (this will switch to email view)
                    if self.on_order_select:
                        self.on_order_select(order)
                    
                    break
            else:
                # If we couldn't find the order in the treeview, show it in details
                self.details_text.delete(1.0, tk.END)
                details = f"Next Order Found:\n\n"
                details += f"Participant: {next_order.participant_full_name}\n"
                details += f"Jersey Name: {next_order.jersey_name}\n"
                details += f"Jersey Number: {next_order.jersey_number}\n"
                details += f"Jersey Size: {next_order.jersey_size}\n"
                details += f"Jersey Type: {next_order.jersey_type}\n"
                details += f"Contacted: {next_order.contacted}\n"
                details += f"Confirmed: {next_order.confirmed}\n"
                self.details_text.insert(1.0, details)
                
        except Exception as e:
            # Show error in details text
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, f"Error getting next order: {str(e)}") 