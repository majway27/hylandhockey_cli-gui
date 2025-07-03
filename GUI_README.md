# Hyland Hockey Jersey Order Management - GUI Application

This is the modern GUI replacement for the Jupyter notebook interface. Built with Tkinter + ttkbootstrap for a clean, professional appearance.

## Features

- **Dashboard**: Overview of pending orders and system statistics
- **Orders Management**: View and manage all jersey orders in a table format
- **Email Composition**: Generate and send verification emails to parents
- **Configuration**: View and test system configuration

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure your configuration is set up:
   - Copy `config/config.yaml.template` to `config/config.yaml`
   - Update the configuration values
   - Set up Google API credentials

## Running the Application

### Option 1: Direct execution
```bash
python main.py
```

### Option 2: Using the launcher script
```bash
python run_gui.py
```

## Application Structure

### Main Window
The application uses a tabbed interface with four main sections:

1. **Dashboard Tab**
   - Quick statistics overview
   - Pending orders count
   - Refresh functionality

2. **Orders Tab**
   - Table view of all pending orders
   - Order details panel
   - "Get Next Order" functionality
   - Refresh orders list

3. **Email Tab**
   - Email composition interface
   - Auto-population from order data
   - Gmail draft generation
   - Clear form functionality

4. **Configuration Tab**
   - System configuration display
   - Test mode indicator
   - Connection testing
   - Spreadsheet information

### Key Features

- **Modern UI**: Clean, professional appearance using ttkbootstrap
- **Responsive Design**: Adapts to window resizing
- **Status Bar**: Real-time feedback on operations
- **Error Handling**: Graceful error handling with user feedback
- **Data Integration**: Seamless integration with existing Google Sheets and Gmail APIs

## Usage Workflow

1. **Start the application** and check the Dashboard for pending orders
2. **Navigate to Orders tab** to view all pending orders in a table
3. **Select an order** or use "Get Next Order" to load order details
4. **Switch to Email tab** to compose verification emails
5. **Generate Gmail drafts** for order verification
6. **Use Configuration tab** to verify system setup

## Development Notes

- The application runs in test mode by default
- All existing business logic from the Jupyter notebook is preserved
- The GUI provides a more user-friendly interface for the same functionality
- Error handling provides clear feedback for troubleshooting

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Configuration Errors**: Check that `config.yaml` is properly configured
3. **Google API Errors**: Verify credentials and API access
4. **Display Issues**: Ensure your system supports Tkinter

### Getting Help

- Check the status bar for error messages
- Use the "Test Connection" button in the Configuration tab
- Review the console output for detailed error information

## Migration from Jupyter Notebook

This GUI application replaces the Jupyter notebook interface while maintaining all existing functionality:

- ✅ Order management and viewing
- ✅ Email template generation
- ✅ Gmail integration
- ✅ Google Sheets data access
- ✅ Configuration management
- ✅ Error handling and validation

The Jupyter notebook (`workflow/jersey.ipynb`) can be safely removed once you've verified the GUI application meets all your needs. 