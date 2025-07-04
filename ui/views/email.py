import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk

class EmailView(ttk.Frame):
    def __init__(self, master, config, order_verification, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config = config
        self.order_verification = order_verification
        self.current_order = None
        self.recipient_var = tk.StringVar()
        self.subject_var = tk.StringVar()
        self.build_ui()

    def build_ui(self):
        instructions_frame = ttk.LabelFrame(self, text="Instructions", padding=10)
        instructions_frame.pack(fill=X, pady=(0, 10), padx=20)
        instructions_text = (
            "1. Select an order from the Orders tab, or use 'Get Next Order' below\n"
            "2. Review the generated email content\n"
            "3. Click 'Generate Draft' to create a Gmail draft and update the contacted field\n"
            "4. The draft will be created in your Gmail account"
        )
        instructions_label = ttk.Label(
            instructions_frame,
            text=instructions_text,
            font=("Helvetica", 9),
            justify=tk.LEFT
        )
        instructions_label.pack(anchor=W)
        
        # Actions frame - moved up to replace Order Selection
        actions_frame = ttk.LabelFrame(self, text="Actions", padding=10)
        actions_frame.pack(fill=X, pady=(0, 10), padx=20)
        
        # Get Next Order button
        ttk.Button(
            actions_frame,
            text="Get Next Order",
            command=self.get_next_order,
            style="info.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
        # Generate Draft button
        generate_draft_btn = ttk.Button(
            actions_frame,
            text="Generate Draft",
            command=self.generate_email_draft,
            style="primary.TButton",
            width=15
        )
        generate_draft_btn.pack(side=LEFT, padx=(0, 10))
        
        # Clear button
        clear_btn = ttk.Button(
            actions_frame,
            text="Clear",
            command=self.clear_email_form,
            style="secondary.TButton",
            width=10
        )
        clear_btn.pack(side=LEFT, padx=(0, 10))
        
        # Current order display
        self.current_order_var = tk.StringVar(value="No order selected")
        current_order_label = ttk.Label(
            actions_frame,
            textvariable=self.current_order_var,
            font=("Helvetica", 9),
            foreground="gray"
        )
        current_order_label.pack(side=LEFT, padx=(20, 0))
        
        # Store button references for debugging
        self.generate_draft_btn = generate_draft_btn
        self.clear_btn = clear_btn
        compose_frame = ttk.LabelFrame(self, text="Email Composition", padding=10)
        compose_frame.pack(fill=BOTH, expand=True, padx=20)
        recipient_frame = ttk.Frame(compose_frame)
        recipient_frame.pack(fill=X, pady=(0, 10))
        ttk.Label(recipient_frame, text="To:").pack(side=LEFT)
        recipient_entry = ttk.Entry(recipient_frame, textvariable=self.recipient_var, width=50)
        recipient_entry.pack(side=LEFT, padx=(10, 0))
        subject_frame = ttk.Frame(compose_frame)
        subject_frame.pack(fill=X, pady=(0, 10))
        ttk.Label(subject_frame, text="Subject:").pack(side=LEFT)
        subject_entry = ttk.Entry(subject_frame, textvariable=self.subject_var, width=50)
        subject_entry.pack(side=LEFT, padx=(10, 0))
        content_frame = ttk.Frame(compose_frame)
        content_frame.pack(fill=BOTH, expand=True)
        ttk.Label(content_frame, text="Content:").pack(anchor=W)
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill=BOTH, expand=True, pady=(5, 0))
        self.email_text = tk.Text(text_frame, wrap=tk.WORD)
        email_scrollbar = ttk.Scrollbar(text_frame, orient=VERTICAL, command=self.email_text.yview)
        self.email_text.configure(yscrollcommand=email_scrollbar.set)
        self.email_text.pack(side=LEFT, fill=BOTH, expand=True)
        email_scrollbar.pack(side=RIGHT, fill=Y)

    def get_next_order(self):
        """Get the next order and populate the email form.
        This method is called when the user clicks 'Get Next Order' in the email view."""
        try:
            next_order = self.order_verification.get_next_pending_order()
            if next_order:
                self.populate_from_order(next_order)
            else:
                # Show message that no pending orders are available
                import tkinter.messagebox as messagebox
                messagebox.showinfo("Info", "No pending orders available.")
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Error getting next order: {str(e)}")

    def generate_email_draft(self):
        """Generate a Gmail draft and update the contacted status in the sheet."""
        if not self.current_order:
            # Show error message
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", "No order selected. Please select an order first.")
            return
        
        try:
            # Call the order verification system to generate the email draft
            # This mirrors the legacy jupyter notebook functionality:
            # result = verification.OrderVerification(config).generate_verification_email(next_possible_pending_order)
            draft_id = self.order_verification.generate_verification_email(self.current_order)
            
            if draft_id:
                # Show success message
                import tkinter.messagebox as messagebox
                messagebox.showinfo(
                    "Success", 
                    f"Gmail draft created successfully!\n\nDraft ID: {draft_id}\n\n"
                    f"The draft has been created in your Gmail account and the 'contacted' "
                    f"field has been updated in the spreadsheet."
                )
                
                # Clear the form after successful generation
                self.clear_email_form()
            else:
                # Show error message
                import tkinter.messagebox as messagebox
                messagebox.showerror("Error", "Failed to create Gmail draft. Please try again.")
                
        except Exception as e:
            # Show error message with details
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Failed to generate email draft:\n\n{str(e)}")

    def clear_email_form(self):
        self.recipient_var.set("")
        self.subject_var.set("")
        self.email_text.delete(1.0, tk.END)
        self.current_order = None
        if hasattr(self, 'current_order_var'):
            self.current_order_var.set("No order selected")

    def populate_from_order(self, order):
        """Populate the email form with order details."""
        self.current_order = order
        
        # Update the order display
        if hasattr(self, 'current_order_var'):
            self.current_order_var.set(f"Order: {order.participant_full_name} - {order.jersey_name} #{order.jersey_number}")
        
        # Set recipient (use first available parent email)
        recipient = order.parent1_email or order.parent2_email or order.parent3_email or order.parent4_email
        if recipient:
            self.recipient_var.set(recipient)
        
        # Set subject
        subject = f"Good morning, here is what you ordered for {order.participant_first_name} during registration:"
        self.subject_var.set(subject)
        
        # Generate email content using the order verification system
        try:
            email_content = self.order_verification.build_notification_template(order)
            self.email_text.delete(1.0, tk.END)
            self.email_text.insert(1.0, email_content)
        except Exception as e:
            # Fallback content if template generation fails
            fallback_content = f"""Good morning,

Here is what you ordered for {order.participant_first_name} during registration:

- Jersey Name: {order.jersey_name}
- Jersey #: {order.jersey_number}
- Jersey Size: {order.jersey_size}
- Jersey Type: {order.jersey_type}
- Sock Size: {order.sock_size}
- Sock Type: {order.sock_type}
- Pant Shell Size: {order.pant_shell_size}

{order.link}

We do have samples available if you need to check the sizing but otherwise if everything looks good let me know and we'll get the order placed.

Best regards,
Registrar Team"""
            self.email_text.delete(1.0, tk.END)
            self.email_text.insert(1.0, fallback_content) 