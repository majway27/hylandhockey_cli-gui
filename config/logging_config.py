#!/usr/bin/env python3
"""
Logging Configuration for Hyland Hockey Jersey Order Management System

This module provides centralized logging configuration for the entire application.
It sets up different log levels, formats, and handlers for various components.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


class ErrorLevelFilter(logging.Filter):
    """Filter to only allow ERROR and CRITICAL level messages."""
    
    def filter(self, record):
        return record.levelno >= logging.ERROR


class LoggingConfig:
    """Centralized logging configuration for the application."""
    
    def __init__(self, log_dir="logs", app_name="hyland_hockey"):
        """
        Initialize logging configuration.
        
        Args:
            log_dir (str): Directory to store log files
            app_name (str): Application name for log file naming
        """
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        
        # Ensure log directory exists
        self.log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup the main logging configuration."""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Note: Console handler removed to prevent STDOUT output
        # All logging now goes to log files only
        
        # File handler for all logs (DEBUG level and above)
        all_logs_file = self.log_dir / f"{self.app_name}_all.log"
        file_handler = logging.handlers.RotatingFileHandler(
            all_logs_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Error log file (ERROR level and above only)
        error_log_file = self.log_dir / f"{self.app_name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        # Add filter to ensure only ERROR and CRITICAL messages are logged
        error_handler.addFilter(ErrorLevelFilter())
        root_logger.addHandler(error_handler)
        
        # Daily log file
        daily_log_file = self.log_dir / f"{self.app_name}_{datetime.now().strftime('%Y-%m-%d')}.log"
        daily_handler = logging.handlers.TimedRotatingFileHandler(
            daily_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days of logs
            encoding='utf-8'
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(daily_handler)
        
        # Log startup message
        logging.info(f"Logging initialized. Log directory: {self.log_dir.absolute()}")
    
    def get_logger(self, name):
        """
        Get a logger instance for a specific module.
        
        Args:
            name (str): Logger name (usually __name__)
            
        Returns:
            logging.Logger: Configured logger instance
        """
        return logging.getLogger(name)
    
    def set_level(self, level):
        """
        Set the logging level for file handlers.
        
        Args:
            level (str): Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            # Update file handler levels
            for handler in logging.getLogger().handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.setLevel(level_map[level.upper()])
            logging.info(f"File logging level set to {level.upper()}")
        else:
            logging.warning(f"Invalid logging level: {level}. Using INFO level.")
    
    def cleanup_old_logs(self, days_to_keep=30):
        """
        Clean up old log files.
        
        Args:
            days_to_keep (int): Number of days to keep log files
        """
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
            
            deleted_count = 0
            for log_file in self.log_dir.glob(f"{self.app_name}_*.log"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logging.info(f"Cleaned up {deleted_count} old log files")
        except Exception as e:
            logging.error(f"Error cleaning up old logs: {e}")


# Global logging configuration instance
_logging_config = None


def get_logging_config():
    """Get the global logging configuration instance."""
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig()
    return _logging_config


def get_logger(name):
    """
    Get a logger instance for a specific module.
    
    Args:
        name (str): Logger name (usually __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return get_logging_config().get_logger(name)


def setup_logging(log_dir="logs", app_name="hyland_hockey", level="INFO"):
    """
    Setup logging for the application.
    
    Args:
        log_dir (str): Directory to store log files
        app_name (str): Application name for log file naming
        level (str): Initial console logging level
    """
    global _logging_config
    _logging_config = LoggingConfig(log_dir, app_name)
    _logging_config.set_level(level)
    return _logging_config 