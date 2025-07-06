# USA Hockey Integration

This document describes the USA Hockey integration feature that has been added to the Hyland Hockey Jersey Order Management System.

## Overview

The USA Hockey integration allows you to:
- Download master registration reports from the USA Hockey portal
- Process and clean the registration data
- Export data to various formats (CSV, Excel)
- View data summaries and statistics

## Features

### 🔐 Authentication
- Secure login to USA Hockey portal using environment variables
- Automatic association and season selection
- Graceful error handling for authentication failures

### 📊 Data Management
- Download master registration reports as CSV files
- Automatic data cleaning and validation
- Support for loading existing report files
- Data export to Excel and CSV formats

### 🖥️ User Interface
- Modern GUI with progress indicators
- Real-time status updates
- Data summary display
- File management capabilities

## Setup

### 1. Configuration

Add your USA Hockey credentials to the `config/config.yaml` file:

```yaml
usa_hockey:
  # Authentication - Add your USA Hockey credentials here
  username: "your_usa_hockey_username"
  password: "your_usa_hockey_password"
```

### 2. Dependencies

Install the required dependencies:

```bash
pip install -r requirements.txt
```

The USA Hockey integration requires:
- `playwright>=1.40.0` - Browser automation
- `pandas>=1.5.3` - Data processing
- `openpyxl>=3.1.0` - Excel export
- `python-dotenv>=1.0.0` - Environment variable loading

### 3. Playwright Setup

Install Playwright browsers:

```bash
playwright install
```

## Configuration

### Configuration File

The USA Hockey settings are configured in `config/config.yaml`:

```yaml
usa_hockey:
  # Authentication - Add your USA Hockey credentials here
  username: "your_usa_hockey_username"
  password: "your_usa_hockey_password"
  
  # Portal URLs
  login_url: "https://portal.usahockey.com/tool/login"
  base_url: "https://portal.usahockey.com"
  reports_url: "https://portal.usahockey.com/tool/reports"
  master_report_url: "https://portal.usahockey.com/tool/reports/master_registration.csv"
  
  # Association settings
  association:
    primary_selector: "a[onclick*='select_association']"
    alternative_selectors:
      - "a:has-text('NICE ICE HOCKEY ASSOCIATION')"
      - "li a:has-text('AAA0000')"
    target_association:
      code: "AAA0000"
      name: "NICE ICE HOCKEY ASSOCIATION"
  
  # Season settings
  season:
    selection_strategy: "latest"  # latest, specific, manual
    specific_season: null  # e.g., "20242025"
  
  # Browser settings
  browser:
    headless: true
    browser_type: "chromium"
    viewport:
      width: 1280
      height: 720
  
  # Download settings
  download:
    directory: "downloads/usa_hockey"
    filename_pattern: "master_registration_{timestamp}.csv"
    timeout: 300000  # 5 minutes
```

### Customization

You can customize the configuration for your specific USA Hockey association:

1. **Association Selection**: Update the `target_association` settings
2. **Season Strategy**: Choose between "latest", "specific", or "manual"
3. **Download Directory**: Change where files are saved
4. **Browser Settings**: Adjust headless mode and viewport size

## Usage

### Using the GUI

1. **Start the Application**:
   ```bash
   python main.py
   ```

2. **Navigate to USA Hockey Section**:
   - Click on "USA Hockey" in the navigation panel
   - Select "Master (USA)" tab

3. **Check Credentials**:
   - Click "Check Credentials" to verify your setup
   - Ensure credentials are available before proceeding

4. **Download Report**:
   - Click "Download Master Report"
   - Monitor progress in the status bar
   - Wait for completion (may take several minutes)

5. **View and Export Data**:
   - Review data summary information
   - Use "Export Data" to save in Excel or CSV format
   - Load existing reports with "Load Existing Report"

### Using the API

You can also use the USA Hockey integration programmatically:

```python
from config.config_manager import ConfigManager
from workflow.usa_hockey import MasterReportsWorkflow
import asyncio

# Initialize
config = ConfigManager(test=True)
workflow = MasterReportsWorkflow(config.usa_hockey)

# Download report
async def download_report():
    file_path = await workflow.download_master_report()
    if file_path:
        print(f"Downloaded to: {file_path}")
        
        # Process the data
        df = workflow.process_master_report(file_path)
        if df is not None:
            print(f"Processed {len(df)} records")

# Run the download
asyncio.run(download_report())
```

## Architecture

### Components

1. **Configuration Layer**
   - `config/usa_hockey_config.py` - USA Hockey specific configuration
   - `config/config_manager.py` - Main configuration manager

2. **Authentication Layer**
   - `auth/usa_hockey_auth.py` - USA Hockey portal authentication
   - Handles login, association selection, and season selection

3. **Core Business Logic**
   - `utils/usa_hockey_client.py` - Main client for portal operations
   - `workflow/usa_hockey/master_reports.py` - Workflow orchestration
   - `workflow/usa_hockey/data_processor.py` - Data processing and cleaning

4. **User Interface**
   - `ui/views/usa_master.py` - Master reports UI
   - Progress indicators, status updates, and data display

### Data Flow

1. **Authentication**: Login → Association Selection → Season Selection
2. **Download**: Navigate to Reports → Click Master Report → Save File
3. **Processing**: Load CSV → Clean Data → Validate → Display Summary
4. **Export**: Format Data → Save to Excel/CSV

## Error Handling

### Common Issues

1. **Authentication Failures**
   - Check credentials are set correctly
   - Verify USA Hockey portal is accessible
   - Check for account lockouts

2. **Download Failures**
   - USA Hockey portal may be slow
   - Network connectivity issues
   - Portal maintenance windows

3. **Data Processing Errors**
   - Corrupted CSV files
   - Encoding issues
   - Missing required fields

### Troubleshooting

1. **Check Logs**: Review `logs/hyland_hockey_errors.log`
2. **Test Credentials**: Use the "Check Credentials" button
3. **Verify Network**: Ensure portal.usahockey.com is accessible
4. **Check Configuration**: Verify settings in `config.yaml`

## Testing

### Run Integration Tests

```bash
python tests/test_usa_hockey_integration.py
```

This will test:
- Configuration loading
- Workflow components
- UI component imports
- Credential validation

### Manual Testing

1. **Test Authentication**:
   - Verify credentials are loaded
   - Check portal accessibility

2. **Test Download**:
   - Download a small report first
   - Monitor progress and completion

3. **Test Data Processing**:
   - Load downloaded file
   - Verify data summary
   - Test export functionality

## Security Considerations

1. **Credential Storage**: Credentials are stored in environment variables
2. **Network Security**: All communication uses HTTPS
3. **File Permissions**: Downloaded files use standard file permissions
4. **Session Management**: Browser sessions are properly cleaned up

## Performance

### Optimization Tips

1. **Headless Mode**: Enabled by default for faster operation
2. **Timeout Settings**: Configured for slow portal responses
3. **Memory Management**: Large files are processed efficiently
4. **Background Processing**: UI remains responsive during operations

### Expected Performance

- **Authentication**: 10-30 seconds
- **Report Download**: 2-10 minutes (depending on portal speed)
- **Data Processing**: 1-5 seconds per 1000 records
- **Export**: 1-10 seconds depending on file size

## Support

### Getting Help

1. **Check Documentation**: Review this file and other README files
2. **Review Logs**: Check application logs for detailed error information
3. **Test Components**: Use the integration test script
4. **Verify Setup**: Ensure all dependencies and credentials are correct

### Known Limitations

1. **Portal Dependencies**: Functionality depends on USA Hockey portal availability
2. **Rate Limiting**: Portal may have rate limits for downloads
3. **Browser Compatibility**: Uses Playwright for browser automation
4. **Data Format**: Depends on USA Hockey's CSV format

## Future Enhancements

Potential improvements for future versions:

1. **Batch Processing**: Process multiple reports simultaneously
2. **Data Synchronization**: Sync with local database systems
3. **Advanced Filtering**: More sophisticated data filtering options
4. **Report Scheduling**: Automated report downloads
5. **Data Analytics**: Built-in data analysis tools

## Changelog

### Version 1.0.0 (Initial Release)
- ✅ USA Hockey portal authentication
- ✅ Master report download functionality
- ✅ Data processing and cleaning
- ✅ Excel and CSV export
- ✅ Modern GUI interface
- ✅ Progress tracking and error handling
- ✅ Comprehensive logging
- ✅ Integration testing 