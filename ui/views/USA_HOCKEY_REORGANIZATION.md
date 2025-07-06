# USA Hockey Views Reorganization

## Overview

The USA Hockey functionality has been reorganized to better separate concerns between data acquisition and data viewing/filtering.

## Changes Made

### 1. UsaImportView (`usa_import.py`)

**Purpose**: Data acquisition and synchronization with USA Hockey systems.

**Responsibilities**:
- ✅ USA Hockey credentials validation
- ✅ Connection management and authentication
- ✅ Download progress tracking
- ✅ Master report download initiation
- ✅ Data metadata display (row count, timestamp, etc.)
- ✅ Export functionality for downloaded data
- ✅ Navigation to data viewing

**Key Features**:
- Progress bar for download operations
- Credentials status checking
- Data information display
- "View Data" button to navigate to master view
- Export capabilities for downloaded data

### 2. UsaMasterView (`usa_master.py`)

**Purpose**: Data viewing, filtering, and analysis of master registration records.

**Responsibilities**:
- ✅ Table view of all registration records
- ✅ Pre-built process-oriented filters
- ✅ Custom filtering capabilities
- ✅ Column sorting
- ✅ Row detail viewing
- ✅ Export of filtered data

**Key Features**:
- **Pre-built Filters**:
  - Active Registrations (green button)
  - Pending Review (yellow button)
  - Completed (blue button)
  - Clear Filters (gray button)

- **Custom Filtering**:
  - Column selector dropdown
  - Value entry field
  - Apply filter button

- **Table Features**:
  - Sortable columns (click headers)
  - Scrollable data display
  - Row detail popup (double-click)
  - Performance optimized (shows first 1000 rows)

## Data Flow

1. **Import View**: User downloads or loads master report data
2. **Data Storage**: Data is stored in `config.current_master_data`
3. **Navigation**: "View Data" button navigates to Master view
4. **Master View**: Displays data in table format with filtering options

## Navigation Integration

The views communicate through the main app's navigation system:
- Import view stores data in config object
- Master view retrieves data from config on load
- Navigation uses the existing `show_view()` method

## Filter Implementation

### Pre-built Filters
The pre-built filters are designed to be process-oriented and can be customized based on your specific data structure:

```python
# Active Registrations
if 'status' in self.current_data.columns:
    self.filtered_data = self.filtered_data[
        self.filtered_data['status'].str.contains('active', case=False, na=False)
    ]
elif 'registration_date' in self.current_data.columns:
    # Show recent registrations (last 30 days)
    recent_date = pd.Timestamp.now() - pd.Timedelta(days=30)
    self.filtered_data = self.filtered_data[
        pd.to_datetime(self.filtered_data['registration_date'], errors='coerce') >= recent_date
    ]
```

### Custom Filters
Users can filter by any column using text search:
- Column selection from dropdown
- Value entry for search term
- Case-insensitive partial matching

## Performance Considerations

- Table displays limited to first 1000 rows for performance
- Filtering operations work on full dataset
- Export functionality works with filtered data
- Column widths auto-calculated based on content

## Future Enhancements

1. **Advanced Filtering**: Date ranges, numeric ranges, multiple conditions
2. **Saved Filters**: User-defined filter presets
3. **Data Visualization**: Charts and graphs for data analysis
4. **Bulk Operations**: Actions on filtered data sets
5. **Real-time Updates**: Automatic refresh of data from USA Hockey

## Usage Workflow

1. Navigate to "Import (USA)" view
2. Check credentials status
3. Download master report or load existing file
4. Review data metadata (record count, timestamp)
5. Click "View Data" to see records in table format
6. Use pre-built or custom filters to find specific records
7. Export filtered data as needed
8. Double-click rows to see detailed information 