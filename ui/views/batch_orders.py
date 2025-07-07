import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
import threading
import time

from utils.rate_limiting import RateLimitExceededError
from ui.utils.styling import apply_treeview_styling, configure_columns_with_priority_styling, apply_alternating_row_colors, get_alternating_row_tags

class BatchOrdersView(ttk.Frame):
    def __init__(self, master, config, order_verification, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config = config
        self.order_verification = order_verification
        self.orders_tree = None
        self.orders_list = []
        self.order_item_map = {}
        # Load the persisted batch size or default to 1
        saved_batch_size = self.config.get_batch_order_size()
        self.batch_size_var = tk.StringVar(value=str(saved_batch_size))
        self.is_processing = False
        self.build_ui()
        self.refresh()

    def build_ui(self):
        # Control panel
        control_frame = ttk.LabelFrame(self, text="Batch Processing Controls", padding=10)
        control_frame.pack(fill=X, pady=(0, 10), padx=20)
        
        # Batch size input
        batch_input_frame = ttk.Frame(control_frame)
        batch_input_frame.pack(fill=X, pady=(0, 10))
        ttk.Label(batch_input_frame, text="Batch Size:").pack(side=LEFT)
        batch_size_entry = ttk.Entry(batch_input_frame, textvariable=self.batch_size_var, width=10)
        batch_size_entry.pack(side=LEFT, padx=(10, 0))
        # Bind the entry to save preference when user changes the value
        batch_size_entry.bind('<FocusOut>', self.save_batch_size_preference)
        batch_size_entry.bind('<Return>', self.save_batch_size_preference)
        ttk.Label(batch_input_frame, text="(Number of orders to process)").pack(side=LEFT, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=X)
        ttk.Button(
            button_frame,
            text="Refresh Orders",
            command=self.refresh,
            style="info.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        self.start_batch_btn = ttk.Button(
            button_frame,
            text="Start Batch Processing",
            command=self.start_batch_processing,
            style="success.TButton"
        )
        self.start_batch_btn.pack(side=LEFT, padx=(0, 10))
        self.stop_batch_btn = ttk.Button(
            button_frame,
            text="Stop Processing",
            command=self.stop_batch_processing,
            style="danger.TButton",
            state="disabled"
        )
        self.stop_batch_btn.pack(side=LEFT, padx=(0, 10))
        
        # Progress display
        progress_frame = ttk.LabelFrame(control_frame, text="Processing Progress", padding=10)
        progress_frame.pack(fill=X, pady=(10, 0))
        self.progress_var = tk.StringVar(value="Ready to process")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.pack(anchor=W)
        
        # Orders table
        table_frame = ttk.LabelFrame(self, text="Eligible Orders", padding=10)
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
        
        # Output log
        log_frame = ttk.LabelFrame(self, text="Processing Output", padding=10)
        log_frame.pack(fill=X, pady=(10, 0), padx=20)
        self.output_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        output_scrollbar = ttk.Scrollbar(log_frame, orient=VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scrollbar.set)
        self.output_text.pack(side=LEFT, fill=BOTH, expand=True)
        output_scrollbar.pack(side=RIGHT, fill=Y)



    def refresh(self):
        """Refresh the orders list."""
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
        
        self.log_output(f"Found {len(pending_orders)} eligible orders for processing")

    def start_batch_processing(self):
        """Start the batch processing in a separate thread."""
        if self.is_processing:
            return
        
        try:
            batch_size = int(self.batch_size_var.get())
            if batch_size <= 0:
                self.log_output("Error: Batch size must be greater than 0")
                return
        except ValueError:
            self.log_output("Error: Batch size must be a valid number")
            return
        
        self.is_processing = True
        self.start_batch_btn.config(state="disabled")
        self.stop_batch_btn.config(state="normal")
        self.progress_var.set("Processing...")
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.process_batch, args=(batch_size,))
        thread.daemon = True
        thread.start()

    def stop_batch_processing(self):
        """Stop the batch processing."""
        self.is_processing = False
        self.start_batch_btn.config(state="normal")
        self.stop_batch_btn.config(state="disabled")
        self.progress_var.set("Processing stopped by user")

    def process_batch(self, total_count_limit):
        """Process the batch of orders."""
        run = 0
        
        self.log_output(f"Starting batch processing of {total_count_limit} orders...")
        
        while run < total_count_limit and self.is_processing:
            try:
                # Update progress
                self.progress_var.set(f"Processing order {run + 1} of {total_count_limit}")
                
                # Get next pending order
                next_possible_pending_order = self.order_verification.get_next_pending_order()
                
                if next_possible_pending_order is None:
                    self.log_output("No more pending orders available")
                    break
                
                # Log the order being processed
                self.log_output(f"Processing order {run + 1}: {next_possible_pending_order.participant_full_name} - {next_possible_pending_order.jersey_name} #{next_possible_pending_order.jersey_number}")
                
                # Generate verification email
                result = self.order_verification.generate_verification_email(next_possible_pending_order)
                
                if result:
                    self.log_output(f"✓ Successfully processed order {run + 1}. Draft ID: {result}")
                else:
                    self.log_output(f"✗ Failed to process order {run + 1}")
                
                run += 1
                self.log_output(f"Processed {run} orders\n")
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.5)
                
            except RateLimitExceededError as e:
                self.log_output(f"⚠ Rate limit exceeded during batch processing: {str(e)}")
                self.log_output("Batch processing paused due to rate limiting. Please wait a moment and try again.")
                self.log_output("You can resume processing by clicking 'Start Batch Processing' again.")
                break
            except Exception as e:
                self.log_output(f"✗ Error processing order {run + 1}: {str(e)}")
                self.log_output("Batch processing halted due to error")
                break
        
        # Processing complete
        self.is_processing = False
        self.start_batch_btn.config(state="normal")
        self.stop_batch_btn.config(state="disabled")
        
        if run >= total_count_limit:
            self.progress_var.set(f"Completed processing {run} orders")
            self.log_output(f"Batch processing completed successfully. Processed {run} orders.")
        else:
            self.progress_var.set(f"Processing stopped. Processed {run} orders")
        
        # Refresh the orders list to show updated status
        self.after(100, self.refresh)

    def log_output(self, message):
        """Add a message to the output log."""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # Update the text widget in the main thread
        self.after(0, lambda: self._update_output_text(log_message))

    def _update_output_text(self, message):
        """Update the output text widget (called from main thread)."""
        self.output_text.insert(tk.END, message)
        self.output_text.see(tk.END)  # Auto-scroll to bottom
    
    def save_batch_size_preference(self, event=None):
        """Save the batch size preference when user changes the value."""
        try:
            batch_size = int(self.batch_size_var.get())
            if batch_size > 0:
                self.config.set_batch_order_size(batch_size)
        except ValueError:
            # If the value is not a valid integer, don't save it
            pass 