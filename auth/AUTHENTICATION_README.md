# Authentication System

This document explains the improved authentication system for the Hyland Hockey Jersey Order Management application.

## Overview

The application uses Google OAuth 2.0 for authentication to access Google Sheets and Gmail APIs. The authentication system has been enhanced to handle token expiration gracefully and provide better user feedback.

## Key Features

### 1. Automatic Token Management
- **Token Storage**: OAuth tokens are stored in `config/token.pickle` (production) or `config/token_test.pickle` (test mode)
- **Automatic Refresh**: Tokens are automatically refreshed when they expire (if a refresh token is available)
- **Graceful Degradation**: When tokens cannot be refreshed, the system provides clear error messages

### 2. Enhanced Error Handling
- **Specific Error Types**: Different exception types for different authentication scenarios:
  - `TokenExpiredError`: When tokens have expired and cannot be refreshed
  - `CredentialsNotFoundError`: When credentials file is missing
  - `AuthenticationError`: For other authentication-related errors

### 3. User-Friendly Interface
- **Status Indicators**: Real-time authentication status in the GUI
- **Action Buttons**: Easy-to-use buttons for authentication management
- **Clear Messages**: Descriptive error messages that guide users to solutions

## Authentication Flow

### Initial Setup
1. **Credentials File**: Place your Google API credentials in `config/credentials.json`
2. **Configuration**: Ensure your `config/config.yaml` has the correct scopes and settings
3. **First Run**: The application will prompt for OAuth authentication on first use

### Normal Operation
1. **Token Check**: Application checks if stored tokens are valid
2. **Automatic Refresh**: If tokens are expired but refreshable, they're automatically refreshed
3. **API Access**: Valid tokens are used for Google API calls

### Token Expiration Handling
1. **Detection**: System detects when tokens have expired and cannot be refreshed
2. **User Notification**: Clear error messages inform the user of the issue
3. **Recovery Options**: Users can easily re-authenticate using the GUI buttons

## GUI Authentication Features

### Configuration Tab
The configuration tab includes an "Authentication" section with the following buttons:

- **Check Auth Status**: Verifies current authentication status without attempting to refresh
- **Authenticate**: Initiates OAuth flow to obtain new credentials
- **Clear Tokens**: Removes stored tokens to force re-authentication
- **Test Connection**: Tests Google API access with current credentials

### Status Bar
The main status bar shows:
- Current authentication status
- Error messages when authentication fails
- Success messages when operations complete

## Error Scenarios and Solutions

### 1. "Token has expired and cannot be refreshed"
**Cause**: OAuth refresh token has expired or been revoked
**Solution**: 
1. Click "Clear Tokens" button
2. Click "Authenticate" button
3. Complete the OAuth flow in your browser

### 2. "Credentials file not found"
**Cause**: Missing `config/credentials.json` file
**Solution**:
1. Download credentials from Google Cloud Console
2. Save as `config/credentials.json`
3. Ensure the file has the correct permissions

### 3. "Authentication error"
**Cause**: Various authentication issues (network, API settings, etc.)
**Solution**:
1. Check your internet connection
2. Verify Google API project settings
3. Ensure the correct scopes are configured
4. Try clearing tokens and re-authenticating

## Configuration

### Required Scopes
The application requires the following Google API scopes:
```yaml
scopes:
  - "https://www.googleapis.com/auth/drive"
  - "https://www.googleapis.com/auth/gmail.send"
  - "https://www.googleapis.com/auth/gmail.compose"
  - "https://www.googleapis.com/auth/gmail.modify"
  - "https://www.googleapis.com/auth/spreadsheets"
```

### Test vs Production Mode
- **Test Mode**: Uses `credentials_test.json` and `token_test.pickle`
- **Production Mode**: Uses `credentials.json` and `token.pickle`
- Set test mode in the application configuration

## Testing Authentication

### Using the Test Script
Run the included test script to verify your authentication setup:

```bash
python tests/test_auth.py
```

This script will:
1. Check current authentication status
2. Test credential retrieval
3. Test token clearing functionality
4. Provide guidance on next steps

### Manual Testing
1. Start the application: `python main.py`
2. Check authentication status using the dashboard buttons
3. Test Google API access with the "Test Connection" button
4. Verify that data loads correctly in the Orders tab

## Troubleshooting

### Common Issues

1. **Browser Authentication Window Doesn't Open**
   - Check firewall settings
   - Ensure localhost ports are not blocked
   - Try running the application with elevated privileges

2. **"Invalid Grant" Errors**
   - Clear stored tokens using the "Clear Tokens" button
   - Re-authenticate using the "Authenticate" button
   - Check if your Google account has the necessary permissions

3. **"Access Denied" Errors**
   - Verify that your Google API project is enabled
   - Check that the OAuth consent screen is configured
   - Ensure the correct scopes are requested

4. **Token File Corruption**
   - Delete the token file manually: `rm config/token*.pickle`
   - Re-authenticate using the application

### Log Files
Authentication issues are logged in:
- `logs/hyland_hockey_errors.log`: Error-level messages
- `logs/hyland_hockey.log`: General application logs

Check these files for detailed error information when troubleshooting.

## Security Considerations

1. **Token Storage**: Tokens are stored locally in pickle files
2. **File Permissions**: Ensure token files have appropriate permissions (readable only by the application user)
3. **Credential Rotation**: Regularly rotate your Google API credentials
4. **Access Control**: Limit access to the application and configuration files

## Best Practices

1. **Regular Testing**: Test authentication periodically to catch issues early
2. **Backup Credentials**: Keep backup copies of your credentials files
3. **Monitor Logs**: Regularly check log files for authentication issues
4. **Update Dependencies**: Keep Google API libraries updated
5. **Use Test Mode**: Test changes in test mode before using production

## Support

If you encounter authentication issues:

1. Check this documentation first
2. Review the log files for detailed error messages
3. Test with the provided test script
4. Verify your Google API project configuration
5. Contact your system administrator if issues persist 