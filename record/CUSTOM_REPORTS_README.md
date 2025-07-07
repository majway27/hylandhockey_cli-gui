# Saved Report Feature

This document explains how to use the saved report functionality in the USA Hockey integration.

## Overview

The saved report feature allows you to download the "Saved_Report_All_Fields" report from the USA Hockey portal. This report includes all available data fields and is filtered to show only Colorado (CO) records.

## How It Works

The saved report system works by:

1. **Predefined Report**: Uses the existing "Saved_Report_All_Fields" report configuration
2. **Field Selection**: Includes all 49 available data fields
3. **Filtering**: Automatically filters for Colorado (State = CO)
4. **Format**: Downloads in CSV format
5. **Download**: Submits the request to USA Hockey and downloads the generated report

## Report Configuration

The "Saved_Report_All_Fields" report includes:

### All Available Fields (49 total)
- **Member Information**: Member Type, Last Name, First Name, Middle Initial, DOB, DOB Verified, Citizenship, Citizenship Verified, Transfer Status, Gender, Email, Confirmation Number, Address, City, State, Zip, Phone 1, Phone 2, Parental Guardian 1, Parental Guardian 2
- **Credentials**: CEP Level, CEP #, CEP Expires, Total Credit Earned, Modules, Safe Sport, Date to Expire, Screening, Season to Renew
- **Team Information**: Team Member Position, Team Member Type, Team Member Redlined Note, Home Number, Away Number, Date Rostered, Team Name, Team ID, Team Type, Team Season Type, Classification, Division, Category, Team Submitted Date, Team Approved Date, Public Link URL, Team Notes, NT Bound, Team Status, Original Approved Date

### Filter Configuration
- **State Filter**: State = CO (Colorado only)

## Using the Saved Report Feature

### Through the GUI

1. **Start the Application**:
   ```bash
   python main.py
   ```

2. **Navigate to USA Hockey Section**:
   - Click on "USA Hockey" in the navigation panel
   - Select "Import (USA)" tab

3. **Run Saved Report**:
   - Click the "Run Saved Report (All Fields)" button
   - The system will authenticate and download the report automatically

4. **Download Progress**:
   - Progress is shown in the status bar and progress bar
   - The report will be saved to the downloads directory

### Programmatically

You can also use the saved report functionality in your own code:

```python
from config.config_manager import ConfigManager
from workflow.usa_hockey.custom_reports import CustomReportsWorkflow
import asyncio

# Initialize
config = ConfigManager()
workflow = CustomReportsWorkflow(config.usa_hockey)

# Define the saved report configuration
saved_report_fields = [
    "Member Type", "Last Name", "First Name", "Middle Initial", "DOB", 
    "DOB Verified", "Citizenship", "Citizenship Verified", "Transfer Status", 
    "Gender", "Email", "Confirmation Number", "Address", "City", "State", 
    "Zip", "Phone 1", "Phone 2", "Parental Guardian 1", "Parental Guardian 2", 
    "CEP Level", "CEP #", "CEP Expires", "Total Credit Earned", "Modules", 
    "Safe Sport", "Date to Expire", "Screening", "Season to Renew", 
    "Team Member Position", "Team Member Type", "Team Member Redlined Note", 
    "Home Number", "Away Number", "Date Rostered", "Team Name", "Team ID", 
    "Team Type", "Team Season Type", "Classification", "Division", "Category", 
    "Team Submitted Date", "Team Approved Date", "Public Link URL", 
    "Team Notes", "NT Bound", "Team Status", "Original Approved Date"
]

saved_report_filters = {
    "State": {"type": "eq", "value": "CO"}
}

# Download the saved report
async def download_saved_report():
    result = await workflow.download_custom_report(
        fields=saved_report_fields,
        filters=saved_report_filters,
        format="csv"
    )
    if result:
        print(f"Report downloaded to: {result}")
    else:
        print("Download failed")

# Run the download
asyncio.run(download_saved_report())
```

## File Management

### Download Location
Reports are downloaded to the configured download directory (default: `downloads/`)

### File Naming
Files are automatically named with timestamps:
- Format: `custom_report_YYYYMMDD_HHMMSS.csv`
- Example: `custom_report_20250115_143022.csv`

### File Management Features
- **Preview**: Click "Load Selected File" to preview report contents
- **Delete**: Select a file and click "Delete Selected File" to remove it
- **Refresh**: Click "Refresh Files" to update the file list

## Error Handling

### Common Issues
1. **Authentication Errors**: Check USA Hockey credentials in config.yaml
2. **Network Issues**: Ensure stable internet connection
3. **Permission Errors**: Verify write access to download directory

### Logging
- Check logs for detailed error information
- Look for messages starting with "Saved report"
- Authentication and download progress is logged
- Any errors will include specific details

## Best Practices

1. **Regular Downloads**: Run the saved report regularly to get updated data
2. **File Management**: Clean up old reports periodically
3. **Backup**: Keep important reports backed up
4. **Verification**: Always preview downloaded reports to ensure data quality

## Technical Details

### Report Structure
- **Format**: CSV (Comma-Separated Values)
- **Encoding**: UTF-8
- **Delimiter**: Comma
- **Headers**: Included in first row

### Data Filtering
- **State Filter**: Automatically applied to show only Colorado records
- **No Additional Filters**: Report includes all records matching the state filter

### Performance
- **Download Time**: Varies based on data size and network speed
- **File Size**: Typically 1-10 MB depending on number of records
- **Memory Usage**: Minimal - downloads directly to file 