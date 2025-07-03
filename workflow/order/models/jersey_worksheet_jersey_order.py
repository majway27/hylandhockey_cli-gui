from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import pandas as pd
from record.sheets import read_google_sheet_by_id, update_cell
from config.config_manager import ConfigManager

class FieldAwareDateTime(datetime):
    """A datetime subclass that knows which field it belongs to."""
    def __new__(cls, *args, field_name=None, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)
        instance.field_name = field_name
        return instance

@dataclass
class ParentContact:
    name: str
    email: str
    phone: str
    volunteer: bool

class JerseyWorksheetJerseyOrder:
    # Column mappings
    COLUMN_MAPPINGS = {
        'registration_deep_link': 'Link',
        'last_name': 'Last',
        'first_name': 'First',
        'birthdate': 'Birthdate',
        'birth_year': 'Birth Year',
        'jersey_name': 'Jersey Name',
        'jersey_size': 'Jersey Size',
        'jersey_number': 'Jersey #',
        'jersey_type': 'Jersey Type',
        'pant_shell_size': 'Pant Shell Size',
        'sock_size': 'Sock Size',
        'sock_type': 'Sock Type',
        'contacted': 'Contacted',
        'fitting': 'Fitting',
        'confirmed': 'Confirmed',
        'parent1_name': 'Parent 1',
        'parent1_email': 'Email 1',
        'parent1_phone': 'Phone 1',
        'parent1_volunteer': 'Volunteer 1',
        'parent2_name': 'Parent 2',
        'parent2_email': 'Email 2',
        'parent2_phone': 'Phone 2',
        'parent2_volunteer': 'Volunteer 2',
        'parent3_name': 'Parent 3',
        'parent3_email': 'Email 3',
        'parent3_phone': 'Phone 3',
        'parent3_volunteer': 'Volunteer 3',
        'parent4_name': 'Parent 4',
        'parent4_email': 'Email 4',
        'parent4_phone': 'Phone 4',
        'parent4_volunteer': 'Volunteer 4',
        'address': 'Address',
        'city': 'City',
        'state': 'State',
        'zip': 'Zip',
        'membership': 'Membership',
        'registered': 'Registered'
    }

    def __init__(self, config_manager: ConfigManager, **kwargs):
        self.config_manager = config_manager
        
        # Link field
        self.registration_deep_link: str = kwargs.get('registration_deep_link', '')
        self._raw_link_value: str = kwargs.get('_raw_link_value', '')  # Store raw value
        
        # Required fields
        self.last_name: str = kwargs.get('last_name', '')
        self.first_name: str = kwargs.get('first_name', '')
        self.birthdate: datetime = kwargs.get('birthdate')
        self.birth_year: int = kwargs.get('birth_year')
        self.jersey_name: str = kwargs.get('jersey_name', '')
        self.jersey_size: str = kwargs.get('jersey_size', '')
        self.jersey_number: str = kwargs.get('jersey_number', '')
        self.jersey_type: str = kwargs.get('jersey_type', '')
        self.pant_shell_size: str = kwargs.get('pant_shell_size', '')
        self.sock_size: str = kwargs.get('sock_size', '')
        self.sock_type: str = kwargs.get('sock_type', '')
        
        # Status fields
        self.contacted: bool = kwargs.get('contacted', False)
        self.fitting: bool = kwargs.get('fitting', False)
        self.confirmed: bool = kwargs.get('confirmed', False)
        self.registered: bool = kwargs.get('registered', False)
        
        # Parent 1
        self.parent1_name: str = kwargs.get('parent1_name', '')
        self.parent1_email: str = kwargs.get('parent1_email', '')
        self.parent1_phone: str = kwargs.get('parent1_phone', '')
        self.parent1_volunteer: bool = kwargs.get('parent1_volunteer', False)
        
        # Parent 2
        self.parent2_name: str = kwargs.get('parent2_name', '')
        self.parent2_email: str = kwargs.get('parent2_email', '')
        self.parent2_phone: str = kwargs.get('parent2_phone', '')
        self.parent2_volunteer: bool = kwargs.get('parent2_volunteer', False)
        
        # Parent 3
        self.parent3_name: str = kwargs.get('parent3_name', '')
        self.parent3_email: str = kwargs.get('parent3_email', '')
        self.parent3_phone: str = kwargs.get('parent3_phone', '')
        self.parent3_volunteer: bool = kwargs.get('parent3_volunteer', False)
        
        # Parent 4
        self.parent4_name: str = kwargs.get('parent4_name', '')
        self.parent4_email: str = kwargs.get('parent4_email', '')
        self.parent4_phone: str = kwargs.get('parent4_phone', '')
        self.parent4_volunteer: bool = kwargs.get('parent4_volunteer', False)
        
        # Address
        self.address: str = kwargs.get('address', '')
        self.city: str = kwargs.get('city', '')
        self.state: str = kwargs.get('state', '')
        self.zip: str = kwargs.get('zip', '')
        self.membership: str = kwargs.get('membership', '')

    @property
    def worksheet_name(self) -> str:
        return self.config_manager.jersey_worksheet_jersey_orders_name

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def parent_contacts(self) -> List[ParentContact]:
        contacts = []
        for i in range(1, 5):
            name = getattr(self, f'parent{i}_name')
            if name:
                contacts.append(ParentContact(
                    name=name,
                    email=getattr(self, f'parent{i}_email'),
                    phone=getattr(self, f'parent{i}_phone'),
                    volunteer=getattr(self, f'parent{i}_volunteer')
                ))
        return contacts

    @property
    def active_parents(self) -> int:
        return len(self.parent_contacts)

    @property
    def volunteers(self) -> int:
        return sum(1 for parent in self.parent_contacts if parent.volunteer)

    @property
    def raw_link_value(self) -> str:
        """Get the raw link value from the sheet, preserving the HYPERLINK formula if present."""
        #print(f"Debug - _raw_link_value in property: {self._raw_link_value}")
        return self._raw_link_value

    @classmethod
    def all(cls, config_manager: ConfigManager) -> List['JerseyWorksheetJerseyOrder']:
        try:
            # Read the sheet data using the record module
            df = read_google_sheet_by_id(
                config_manager.jersey_spreadsheet_id,
                config_manager.jersey_worksheet_jersey_orders_gid,
                config_manager
            )
            
            if df.empty:
                return []
            
            #Eprint("Debug - Raw data from sheet:")
            #print(df[['Contacted']].head())
            
            orders = []
            for _, row in df.iterrows():
                # Create a dictionary of attributes
                attrs = {}
                for header in df.columns:
                    column_name = next(
                        (k for k, v in cls.COLUMN_MAPPINGS.items() if v == header),
                        None
                    )
                    if column_name:
                        # Store both processed and raw values for the link
                        if column_name == 'registration_deep_link':
                            attrs['_raw_link_value'] = row[header]  # Store raw value
                            attrs[column_name] = row[header]  # Store raw value for registration_deep_link too
                        else:
                            #print(f"Debug - Raw value for {column_name}: {row[header]}")
                            attrs[column_name] = cls._convert_value(column_name, row[header])
                            #print(f"Debug - Converted value for {column_name}: {attrs[column_name]}")
                
                orders.append(cls(config_manager=config_manager, **attrs))
            
            return orders
            
        except Exception as error:
            print(f"An error occurred: {error}")
            return []

    @classmethod
    def find_by(cls, config_manager: ConfigManager, **kwargs) -> Optional['JerseyWorksheetJerseyOrder']:
        orders = cls.all(config_manager)
        for order in orders:
            if all(getattr(order, key) == value for key, value in kwargs.items()):
                return order
        return None

    @staticmethod
    def _column_to_letter(column_index: int) -> str:
        """
        Convert a column index (0-based) to a Google Sheets column letter.
        Examples:
            0 -> 'A'
            25 -> 'Z'
            26 -> 'AA'
            27 -> 'AB'
        """
        result = ""
        while column_index >= 0:
            result = chr(65 + (column_index % 26)) + result
            column_index = (column_index // 26) - 1
        return result

    def save(self, fields_to_update: List[str] = None) -> bool:
        """
        Save the jersey order to the Google Sheet.
        
        Args:
            fields_to_update: List of field names to update. If None, updates all fields.
                            Field names should match the keys in COLUMN_MAPPINGS.
        
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # Get all orders to find the row index
            df = read_google_sheet_by_id(
                self.config_manager.jersey_spreadsheet_id,
                self.config_manager.jersey_worksheet_jersey_orders_gid,
                self.config_manager
            )
            if df.empty:
                row_index = 2  # First row after header
            else:
                # Find the row index for this order
                mask = (df['First'] == self.first_name) & (df['Last'] == self.last_name)
                if mask.any():
                    row_index = mask.idxmax() + 2  # +2 for header row and 1-based index
                else:
                    row_index = len(df) + 2  # +2 for header row and 1-based index
            
            # Determine which fields to update
            fields = fields_to_update if fields_to_update is not None else list(self.COLUMN_MAPPINGS.keys())
            
            # Update specified fields
            for field in fields:
                if field not in self.COLUMN_MAPPINGS:
                    print(f"Warning: Field '{field}' not found in COLUMN_MAPPINGS")
                    continue
                    
                cell_value = self._format_value_for_sheet(getattr(self, field))
                col_index = list(self.COLUMN_MAPPINGS.keys()).index(field)
                col_letter = self._column_to_letter(col_index)
                cell_ref = f"{col_letter}{row_index}"
                print(f"Updating cell {cell_ref} with value {cell_value}")
                
                if not update_cell(
                    self.config_manager.jersey_spreadsheet_id,
                    self.config_manager.jersey_worksheet_jersey_orders_gid,
                    cell_ref,
                    cell_value,
                    self.config_manager
                ):
                    return False
            
            return True
            
        except Exception as error:
            print(f"An error occurred: {error}")
            return False

    @staticmethod
    def _convert_value(column_name: str, value: str) -> any:
        if pd.isna(value) or value == '':
            return None
            
        if column_name == 'registration_deep_link':
            # For registration_deep_link, we want to preserve the raw value
            return value
            
        if column_name == 'birthdate':
            try:
                return datetime.strptime(str(value), '%Y-%m-%d')
            except ValueError:
                return None
        elif column_name == 'birth_year':
            try:
                return int(value)
            except ValueError:
                return None
        elif column_name in ['contacted', 'fitting', 'confirmed']:
            try:
                # Handle Excel serial numbers
                if isinstance(value, (int, float)):
                    # Convert Excel serial number to datetime
                    # Excel's epoch is 1900-01-01, but it incorrectly considers 1900 a leap year
                    # So we need to adjust for this by subtracting 1 day for dates after 1900-02-28
                    excel_epoch = datetime(1899, 12, 30)
                    days = int(value)
                    date = excel_epoch + timedelta(days=days)
                    return FieldAwareDateTime(date.year, date.month, date.day, field_name=column_name)
                # Handle MM/DD/YYYY format
                elif '/' in str(value):
                    parts = str(value).split('/')
                    if len(parts) == 3:  # MM/DD/YYYY format
                        month, day, year = parts
                        return FieldAwareDateTime(int(year), int(month), int(day), field_name=column_name)
                    elif len(parts) == 2:  # MM/DD format
                        month, day = parts
                        year = datetime.now().year
                        return FieldAwareDateTime(year, int(month), int(day), field_name=column_name)
                return None
            except (ValueError, TypeError):
                return None
        elif column_name == 'registered':
            try:
                dt = datetime.strptime(str(value), '%Y-%m-%d')
                return FieldAwareDateTime(dt.year, dt.month, dt.day, field_name=column_name)
            except ValueError:
                return None
        elif column_name in ['parent1_volunteer', 'parent2_volunteer',
                           'parent3_volunteer', 'parent4_volunteer']:
            if isinstance(value, bool):
                return value
            return str(value).lower() == 'true'
        return value

    @staticmethod
    def _format_value_for_sheet(value: any) -> str:
        if value is None:
            return ''
        elif isinstance(value, FieldAwareDateTime):
            if value.field_name in ['contacted', 'fitting', 'confirmed']:
                return value.strftime('%m/%d/%Y')
            elif value.field_name == 'registered':
                return value.strftime('%Y-%m-%d')
            # Default to MM/DD/YYYY for backward compatibility
            return value.strftime('%m/%d/%Y')
        elif isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, str) and value.startswith('http'):
            # Format URLs as HYPERLINK formulas
            return f'=HYPERLINK("{value}","Link")'
        return str(value) 