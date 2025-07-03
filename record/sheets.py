"""
Google Sheets operations for the record module.
"""

import pandas as pd
import gspread

from auth.google_auth import get_credentials
from config.config_manager import ConfigManager


def read_google_sheet(sheet_name, config_manager: ConfigManager):
    """
    Deprecated: Use read_google_sheet_by_id instead.
    
    Read data from a Google Sheet and return it as a pandas DataFrame.
    
    Args:
        sheet_name (str): Name of the Google Sheet to read
        config_manager (ConfigManager): ConfigManager instance
        
    Returns:
        pandas.DataFrame: The sheet data as a DataFrame
    """
    creds = get_credentials(config_manager)
    gc = gspread.authorize(creds)

    # Open the spreadsheet
    spreadsheet = gc.open(sheet_name)

    # Get the first worksheet
    worksheet = spreadsheet.get_worksheet(0)

    # Get all values and convert to pandas DataFrame
    data = worksheet.get_all_values()
    headers = data[0]
    df = pd.DataFrame(data[1:], columns=headers)

    return df

def read_google_sheet_by_id(spreadsheet_id, worksheet_gid, config_manager: ConfigManager):
    """
    Read data from a specific worksheet in a Google Sheet using IDs and return it as a pandas DataFrame.
    
    Args:
        spreadsheet_id (str): The ID of the Google Spreadsheet
        worksheet_gid (str): The ID (gid) of the specific worksheet
        config_manager (ConfigManager): ConfigManager instance
        
    Returns:
        pandas.DataFrame: The sheet data as a DataFrame
    """
    creds = get_credentials(config_manager)
    gc = gspread.authorize(creds)

    # Open the spreadsheet by ID
    spreadsheet = gc.open_by_key(spreadsheet_id)

    # Get the specific worksheet by gid
    worksheet = spreadsheet.get_worksheet_by_id(int(worksheet_gid))

    # Get all values with formulas and convert to pandas DataFrame
    data = worksheet.get_all_records(value_render_option='UNFORMATTED_VALUE')
    df = pd.DataFrame(data)

    return df

def update_cell(spreadsheet_id, worksheet_gid, cell_reference, value, config_manager: ConfigManager):
    """
    Update a single cell in a Google Sheet.
    
    Args:
        spreadsheet_id (str): The ID of the Google Spreadsheet
        worksheet_gid (str): The ID (gid) of the specific worksheet
        cell_reference (str): The cell reference (e.g., 'A1', 'B2')
        value: The value to write to the cell
        config_manager (ConfigManager): ConfigManager instance
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        creds = get_credentials(config_manager)
        gc = gspread.authorize(creds)

        # Open the spreadsheet by ID
        spreadsheet = gc.open_by_key(spreadsheet_id)

        # Get the specific worksheet by gid
        worksheet = spreadsheet.get_worksheet_by_id(int(worksheet_gid))

        # Update the cell with the value in a list format as required by the API
        # Use valueInputOption='USER_ENTERED' to allow Google Sheets to parse the values
        worksheet.update(cell_reference, [[value]], value_input_option='USER_ENTERED')
        
        # Extract column letter from cell reference (e.g., 'A1' -> 'A')
        column_letter = ''.join(filter(str.isalpha, cell_reference))
        
        # Get the header row to find column names
        headers = worksheet.row_values(1)
        column_index = ord(column_letter.upper()) - ord('A')
        column_name = headers[column_index] if column_index < len(headers) else None
        
        # Only apply date formatting to specific columns
        if column_name in ['Contacted', 'Fitting', 'Confirmed']:
            worksheet.format(cell_reference, {
                "numberFormat": {
                    "type": "DATE",
                    "pattern": "M/d"
                }
            })
        
        return True
    except Exception as e:
        print(f"Error updating cell: {str(e)}")
        return False