import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk

def apply_treeview_styling(tree_widget):
    """
    Apply consistent styling to treeview widgets across the application.
    
    Args:
        tree_widget: The ttk.Treeview widget to style
    """
    try:
        # Get the current style
        style = ttk.Style()
        
        # Create a custom style for treeview headers
        style.configure(
            "Custom.Treeview.Heading",
            background="#2c3e50",  # Dark blue-gray
            foreground="white",
            font=("Helvetica", 9, "bold"),
            relief="flat",
            borderwidth=1
        )
        
        # Apply the custom style to the treeview
        tree_widget.configure(style="Custom.Treeview")
        
        # Also style the treeview itself for better contrast
        style.configure(
            "Custom.Treeview",
            background="white",
            foreground="black",
            fieldbackground="white",
            borderwidth=1,
            relief="solid"
        )
        
    except Exception as e:
        # Use a simple print since logger might not be available
        print(f"Failed to apply custom header styling: {e}")

def apply_alternating_row_colors(tree_widget):
    """
    Apply alternating row colors to a treeview widget.
    
    Args:
        tree_widget: The ttk.Treeview widget to style
    """
    try:
        # Configure row colors
        tree_widget.tag_configure('oddrow', background='#f0f0f0')
        tree_widget.tag_configure('evenrow', background='#ffffff')
    except Exception as e:
        print(f"Failed to apply alternating row colors: {e}")

def get_alternating_row_tags(row_index):
    """
    Get the appropriate tags for alternating row colors.
    
    Args:
        row_index: The index of the row (0-based)
        
    Returns:
        tuple: Tags for the row ('evenrow',) or ('oddrow',)
    """
    return ('evenrow',) if row_index % 2 == 0 else ('oddrow',)

def configure_column_with_styling(tree_widget, column_name, width=None, minwidth=None):
    """
    Configure a column with consistent styling including centering.
    
    Args:
        tree_widget: The ttk.Treeview widget
        column_name: Name of the column
        width: Column width (optional)
        minwidth: Minimum column width (optional)
    """
    try:
        # Set default values if not provided
        if width is None:
            width = 150
        if minwidth is None:
            minwidth = 100
            
        # Configure column with centering and consistent styling
        tree_widget.column(column_name, width=width, minwidth=minwidth, anchor="center")
        
    except Exception as e:
        print(f"Failed to configure column {column_name}: {e}")

def configure_columns_with_priority_styling(tree_widget, columns, priority_columns=None):
    """
    Configure multiple columns with priority-based styling.
    
    Args:
        tree_widget: The ttk.Treeview widget
        columns: List of column names
        priority_columns: Dict of column names to their priority settings
                         Format: {'column_name': {'width': 120, 'minwidth': 100}}
    """
    try:
        for col in columns:
            if priority_columns and col in priority_columns:
                # Use priority settings
                settings = priority_columns[col]
                width = settings.get('width', 150)
                minwidth = settings.get('minwidth', 100)
            else:
                # Use default settings
                width = 150
                minwidth = 100
                
            configure_column_with_styling(tree_widget, col, width, minwidth)
            
    except Exception as e:
        print(f"Failed to configure columns: {e}")

def apply_complete_treeview_styling(tree_widget):
    """
    Apply all treeview styling including headers and alternating row colors.
    This is a convenience function to apply all styling at once.
    
    Args:
        tree_widget: The ttk.Treeview widget to style
    """
    try:
        # Apply header styling
        apply_treeview_styling(tree_widget)
        
        # Apply alternating row colors
        apply_alternating_row_colors(tree_widget)
        
    except Exception as e:
        print(f"Failed to apply complete treeview styling: {e}")

def populate_treeview_with_styling(tree_widget, data, columns=None, priority_columns=None):
    """
    Populate a treeview with data and apply complete styling.
    This is a convenience function that combines data population and styling.
    
    Args:
        tree_widget: The ttk.Treeview widget
        data: List of dictionaries or pandas DataFrame rows
        columns: List of column names (optional, will be inferred from data)
        priority_columns: Dict of column priority settings (optional)
    """
    try:
        # Clear existing items
        for item in tree_widget.get_children():
            tree_widget.delete(item)
        
        # Determine columns if not provided
        if columns is None:
            if hasattr(data, 'columns'):  # DataFrame
                columns = list(data.columns)
            elif data and hasattr(data[0], 'keys'):  # List of dicts
                columns = list(data[0].keys())
            else:
                print("Could not determine columns from data")
                return
        
        # Configure columns
        configure_columns_with_priority_styling(tree_widget, columns, priority_columns)
        
        # Populate data with alternating row colors
        for i, row in enumerate(data):
            if hasattr(row, 'to_dict'):  # DataFrame row
                values = [str(row.get(col, "")) for col in columns]
            elif hasattr(row, 'keys'):  # Dictionary
                values = [str(row.get(col, "")) for col in columns]
            else:  # List/tuple
                values = [str(val) for val in row]
            
            # Insert with alternating row colors
            tags = get_alternating_row_tags(i)
            tree_widget.insert("", "end", values=values, tags=tags)
        
        # Apply complete styling
        apply_complete_treeview_styling(tree_widget)
        
    except Exception as e:
        print(f"Failed to populate treeview with styling: {e}") 