# Hyland Hockey Jersey Order Management System

A modern GUI application for managing hockey jersey orders using Google Sheets and Gmail integration.

## Features

- **Modern GUI**: Built with Tkinter and ttkbootstrap for a professional look
- **Google Integration**: Seamless integration with Google Sheets and Gmail
- **Order Management**: View, verify, and process jersey orders
- **Email Automation**: Generate and send verification emails
- **USA Hockey Integration**: Download master registration reports and run saved reports
- **Test/Production Modes**: Separate configurations for testing and production use

## Installation

1. Clone the repository
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Install Playwright Browsers `playwright install`
6. Create and configure config/config.yaml based off of config.yaml.template

## Configuration

### Test vs Production Mode

The application supports two modes of operation:

- **TEST MODE**: Uses `credentials_test.json` and `token_test.pickle`
- **PRODUCTION MODE**: Uses `credentials.json` and `token.pickle`

#### Running the Application

```bash
# Run in TEST mode (default, recommended for development)
python main.py --test
# or simply
python main.py

# Run in PRODUCTION mode
python main.py --production

# Using the provided script
./run-nb.sh --test        # Test mode
./run-nb.sh --production  # Production mode
./run-nb.sh               # Test mode (default)
```

#### Configuration Tab

The Configuration tab provides a user-friendly interface for managing environment settings:

- **Environment Mode Selection**: Radio buttons to switch between Test and Production modes
- **Mode Description**: Clear explanation of what each mode does
- **Configuration Display**: Shows current file paths and settings
- **Spreadsheet Information**: Displays current Google Sheets configuration
- **Persistent Settings**: Mode selection is automatically saved and restored

**Features:**
- **Safe Mode Switching**: Confirmation dialog prevents accidental mode changes
- **Automatic Token Management**: Clears authentication tokens when switching modes
- **Visual Indicators**: Clear warnings when in production mode
- **Real-time Updates**: Configuration display updates immediately when mode changes

#### Token Renewal and Mode Respect

**Important**: The token renewal system fully respects the current mode setting:

- When running in **TEST MODE**: Token renewal will always use `token_test.pickle`
- When running in **PRODUCTION MODE**: Token renewal will always use `token.pickle`

This ensures that:
- Test and production credentials remain completely separate
- Token expiration and renewal won't accidentally cross-contaminate environments
- The application clearly indicates which mode it's running in via the window title and dashboard

#### Configuration Files

1. **Credentials**: Place your Google API credentials in the appropriate file:
   - Test: `config/credentials_test.json`
   - Production: `config/credentials.json`

2. **Configuration**: Copy `config/config.yaml.template` to `config/config.yaml` and update values

3. **Preferences**: Copy `config/preferences.yaml.template` to `config/preferences.yaml` to customize user settings (optional)

4. **Token Files**: These are automatically created during authentication:
   - Test: `config/token_test.pickle`
   - Production: `config/token.pickle`

## USA Hockey Integration

The application includes comprehensive USA Hockey portal integration for downloading registration data.

### Features

- **Master Report Download**: Download complete registration data
- **Saved Report**: Run the existing "Saved_Report_All_Fields" report with all fields
- **Colorado Filter**: Automatically filters for Colorado records only
- **CSV Format**: Downloads reports in CSV format
- **Progress Tracking**: Real-time progress updates during downloads

### Setup

1. **Configure Credentials**: Add your USA Hockey credentials to `config.yaml`:
   ```yaml
   usa_hockey:
     username: "your_username"
     password: "your_password"
   ```

2. **Test Connection**: Use the "Check Credentials" button to verify your setup

### Usage

1. **Navigate to USA Hockey Section**: Click "USA Hockey" in the navigation panel
2. **Import Tab**: Use the "Import (USA)" tab for downloading reports
3. **Master Report**: Click "Download Latest Master Report" for complete data
4. **Saved Report**: Click "Run Saved Report (All Fields)" for the predefined report

### Saved Report

The saved report feature runs the existing "Saved_Report_All_Fields" report which includes:
- All 49 available data fields
- Automatic filtering for Colorado (State = CO) records
- CSV format download
- No configuration required

**Report Fields Include:**
- Member Information (names, contact info, demographics)
- Credentials (CEP levels, SafeSport, screening)
- Team Information (team assignments, positions, status)
- Additional metadata (dates, notes, verification status)

For detailed information, see [Saved Report Documentation](record/CUSTOM_REPORTS_README.md).

## Usage

1. **Authentication**: Use the "Authenticate" button in the Configuration tab
2. **View Orders**: Check the Orders tab to see all jersey orders
3. **Process Orders**: Use the email functionality to contact customers
4. **Monitor Logs**: Check the Logs tab for detailed application logs

## Security

- Tokens are stored locally in pickle files
- Test and production environments are completely isolated
- Credentials should be kept secure and not committed to version control

## Troubleshooting

### Authentication Issues

1. **Token Expired**: Use "Clear Tokens" then "Authenticate" buttons
2. **Wrong Mode**: Ensure you're running in the correct mode for your credentials
3. **Missing Credentials**: Verify the appropriate credentials file exists

### Mode-Specific Issues

- **Test Mode**: Uses `*_test.*` files for all configuration
- **Production Mode**: Uses standard files without `_test` suffix
- **Mode Confusion**: The application title and dashboard clearly show the current mode

## Development

The application is designed with clear separation between test and production environments. When developing:

1. Always test changes in TEST MODE first
2. Use the provided command line arguments to switch modes
3. Verify that token renewal works correctly in both modes
4. Check that the correct credential files are being used

## License

See LICENSE file for details.