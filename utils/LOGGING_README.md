# Logging System Documentation

This document provides comprehensive documentation for the logging system in the Hyland Hockey Jersey Order Management System, including quick reference guides and detailed information.

## Overview

The logging system provides comprehensive logging capabilities with multiple output destinations and configurable log levels. It automatically creates log files in the `logs/` directory and provides both console and file-based logging.

## Quick Start

### View Logs
```bash
# List all log files
python utils/log_viewer.py --list

# View recent logs
python utils/log_viewer.py --file hyland_hockey_all.log --lines 50

# Tail logs (last 20 lines)
python utils/log_viewer.py --file hyland_hockey_all.log --tail 20
```

### Filter Logs
```bash
# Show only errors
python utils/log_viewer.py --file hyland_hockey_all.log --level ERROR

# Search for specific text
python utils/log_viewer.py --file hyland_hockey_all.log --search "dashboard"

# Show logs since a date
python utils/log_viewer.py --file hyland_hockey_all.log --since "2024-01-15"
```

## Log Files

The system creates several types of log files:

- **`hyland_hockey_all.log`** - Contains all log messages (DEBUG level and above)
- **`hyland_hockey_errors.log`** - Contains only ERROR and CRITICAL messages
- **`hyland_hockey_YYYY-MM-DD.log`** - Daily log files with INFO level and above
- **`hyland_hockey_YYYY-MM-DD.log.1`, `hyland_hockey_YYYY-MM-DD.log.2`, etc.** - Rotated daily logs (kept for 30 days)

| File | Purpose | Level | Rotation |
|------|---------|-------|----------|
| `hyland_hockey_all.log` | All messages | DEBUG+ | 10MB, 5 backups |
| `hyland_hockey_errors.log` | Errors only | ERROR+ | 5MB, 3 backups |
| `hyland_hockey_YYYY-MM-DD.log` | Daily logs | INFO+ | Daily, 30 days |

## Log Levels

The system supports the following log levels (in order of increasing severity):

- **DEBUG** - Detailed information for debugging
- **INFO** - General information about program execution
- **WARNING** - Warning messages for potentially problematic situations
- **ERROR** - Error messages for serious problems
- **CRITICAL** - Critical errors that may prevent the program from running

## Configuration

### Console Logging
- Default level: INFO
- Format: `YYYY-MM-DD HH:MM:SS - LEVEL - MESSAGE`

### File Logging
- All logs: DEBUG level and above
- Error logs: ERROR level and above
- Daily logs: INFO level and above
- Format: `YYYY-MM-DD HH:MM:SS - MODULE - LEVEL - FUNCTION:LINE - MESSAGE`

## Usage

### In Your Code

```python
from config.logging_config import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Use the logger
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")
```

### Log Viewer Utility

The system includes a log viewer utility (`utils/log_viewer.py`) for viewing and filtering log files:

```bash
# List all log files
python utils/log_viewer.py --list

# View a specific log file
python utils/log_viewer.py --file hyland_hockey_all.log

# View last 20 lines
python utils/log_viewer.py --file hyland_hockey_all.log --lines 20

# Filter by log level
python utils/log_viewer.py --file hyland_hockey_all.log --level ERROR

# Search for specific text
python utils/log_viewer.py --file hyland_hockey_all.log --search "dashboard"

# Show logs since a specific date
python utils/log_viewer.py --file hyland_hockey_all.log --since "2024-01-15"

# Tail a log file
python utils/log_viewer.py --file hyland_hockey_all.log --tail 50
```

## Log Viewer Options

| Option | Description | Example |
|--------|-------------|---------|
| `--list` | List all log files | `--list` |
| `--file` | Specify log file | `--file hyland_hockey_all.log` |
| `--lines` | Number of lines to show | `--lines 100` |
| `--level` | Filter by log level | `--level ERROR` |
| `--search` | Search for text | `--search "dashboard"` |
| `--since` | Show logs since date | `--since "2024-01-15"` |
| `--tail` | Show last N lines | `--tail 50` |

## Log Rotation

### All Logs File
- Maximum size: 10MB
- Backup count: 5 files
- When the file reaches 10MB, it's rotated and a new file is created

### Error Logs File
- Maximum size: 5MB
- Backup count: 3 files

### Daily Logs
- Rotated at midnight
- Kept for 30 days
- Automatically deleted after 30 days

## Common Patterns

### Logging Exceptions
```python
try:
    # Your code here
    pass
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
```

### Logging with Context
```python
logger.info(f"Processing order {order_id} for {participant_name}")
```

### Conditional Debug Logging
```python
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"Expensive debug info: {expensive_operation()}")
```

## Best Practices

1. **Use appropriate log levels**:
   - DEBUG for detailed debugging information
   - INFO for general program flow
   - WARNING for potential issues
   - ERROR for actual errors
   - CRITICAL for severe problems

2. **Include context in log messages**:
   ```python
   logger.info(f"Processing order for {participant_name} (ID: {order_id})")
   ```

3. **Log exceptions with full context**:
   ```python
   try:
       # Some operation
       pass
   except Exception as e:
       logger.error(f"Failed to process order: {e}", exc_info=True)
   ```

4. **Use structured logging for complex data**:
   ```python
   logger.info("Order details", extra={
       'order_id': order_id,
       'participant': participant_name,
       'status': status
   })
   ```

## Integration

The logging system is automatically initialized when the main application starts. The following modules have been integrated with logging:

- **main.py** - Main application logging
- **config/config_manager.py** - Configuration management logging
- **workflow/order/verification.py** - Order verification logging

## Troubleshooting

### Log Files Not Created
- Ensure the `logs/` directory exists
- Check file permissions
- Verify the application has write access to the directory
- Ensure logging is initialized in main.py

### Large Log Files
- Log files are automatically rotated when they reach size limits
- Old daily logs are automatically cleaned up after 30 days
- You can manually clean up old logs using the cleanup function
- Check rotation settings in `config/logging_config.py`

### Performance Issues
- DEBUG logging can impact performance in production
- Consider setting console logging to INFO or WARNING in production
- Monitor log file sizes and rotation
- Use conditional debug logging for expensive operations

## Configuration Options

You can customize logging behavior by modifying the `LoggingConfig` class in `config/logging_config.py`:

- Log directory location
- File size limits
- Backup counts
- Log formats
- Log levels

## Security Considerations

- Log files may contain sensitive information
- Ensure log files are not accessible to unauthorized users
- Consider encrypting log files in production environments
- Regularly review and clean up old log files 