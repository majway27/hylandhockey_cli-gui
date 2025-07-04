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
        instructions_frame.pack(fill=X, pady=(0, 10))
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
        order_frame = ttk.LabelFrame(self, text="Order Selection", padding=10)
        order_frame.pack(fill=X, pady=(0, 10))
        ttk.Button(
            order_frame,
            text="Get Next Order",
            command=self.get_next_order,
            style="info.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        self.current_order_var = tk.StringVar(value="No order selected")
        current_order_label = ttk.Label(
            order_frame,
            textvariable=self.current_order_var,
            font=("Helvetica", 9),
            foreground="gray"
        )
        current_order_label.pack(side=LEFT)
        compose_frame = ttk.LabelFrame(self, text="Email Composition", padding=10)
        compose_frame.pack(fill=BOTH, expand=True)
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
        button_frame = ttk.Frame(compose_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        ttk.Button(
            button_frame,
            text="Generate Draft",
            command=self.generate_email_draft,
            style="primary.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        ttk.Button(
            button_frame,
            text="Clear",
            command=self.clear_email_form,
            style="secondary.TButton"
        ).pack(side=LEFT)

    def get_next_order(self):
        # Placeholder for integration
        pass

    def generate_email_draft(self):
        # Placeholder for integration
        pass

    def clear_email_form(self):
        self.recipient_var.set("")
        self.subject_var.set("")
        self.email_text.delete(1.0, tk.END)
        self.current_order = None
        if hasattr(self, 'current_order_var'):
            self.current_order_var.set("No order selected") 