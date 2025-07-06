#!/usr/bin/env python3
"""
USA Hockey Configuration Manager
Handles USA Hockey portal specific configuration settings.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from .logging_config import get_logger

logger = get_logger(__name__)


class USAHockeyConfig:
    """Manages USA Hockey portal specific configuration settings."""
    
    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize USA Hockey configuration.
        
        Args:
            config_data: Configuration dictionary containing usa_hockey section
        """
        self._config = config_data.get('usa_hockey', {})
        logger.info("USAHockeyConfig initialized")
    
    @property
    def username(self) -> Optional[str]:
        """Get USA Hockey username from config file."""
        return self._config.get('username')
    
    @property
    def password(self) -> Optional[str]:
        """Get USA Hockey password from config file."""
        return self._config.get('password')
    
    @property
    def login_url(self) -> str:
        """Get USA Hockey login URL."""
        return self._config.get('login_url', 'https://portal.usahockey.com/tool/login')
    
    @property
    def base_url(self) -> str:
        """Get USA Hockey base URL."""
        return self._config.get('base_url', 'https://portal.usahockey.com')
    
    @property
    def reports_url(self) -> str:
        """Get USA Hockey reports URL."""
        return self._config.get('reports_url', 'https://portal.usahockey.com/tool/reports')
    
    @property
    def master_report_url(self) -> str:
        """Get USA Hockey master report URL."""
        return self._config.get('master_report_url', 'https://portal.usahockey.com/tool/reports/master_registration.csv')
    
    @property
    def association_config(self) -> Dict[str, Any]:
        """Get association selection configuration."""
        return self._config.get('association', {})
    
    @property
    def season_config(self) -> Dict[str, Any]:
        """Get season selection configuration."""
        return self._config.get('season', {})
    
    @property
    def browser_config(self) -> Dict[str, Any]:
        """Get browser configuration."""
        return self._config.get('browser', {})
    
    @property
    def download_config(self) -> Dict[str, Any]:
        """Get download configuration."""
        return self._config.get('download', {})
    
    @property
    def rate_limiting_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration."""
        return self._config.get('rate_limiting', {})
    
    @property
    def download_directory(self) -> Path:
        """Get download directory path."""
        download_dir = self.download_config.get('directory', 'downloads/usa_hockey')
        return Path(download_dir)
    
    @property
    def filename_pattern(self) -> str:
        """Get filename pattern for downloads."""
        return self.download_config.get('filename_pattern', 'master_registration_{timestamp}.csv')
    
    @property
    def download_timeout(self) -> int:
        """Get download timeout in milliseconds."""
        return self.download_config.get('timeout', 300000)
    
    @property
    def page_load_timeout(self) -> int:
        """Get page load timeout in milliseconds."""
        return self.rate_limiting_config.get('page_load_timeout', 300000)
    
    @property
    def retry_attempts(self) -> int:
        """Get number of retry attempts."""
        return self.rate_limiting_config.get('retry_attempts', 3)
    
    @property
    def base_delay(self) -> float:
        """Get base delay for retries in seconds."""
        return self.rate_limiting_config.get('base_delay', 1.0)
    
    @property
    def max_delay(self) -> float:
        """Get maximum delay for retries in seconds."""
        return self.rate_limiting_config.get('max_delay', 60.0)
    
    @property
    def use_exponential_backoff(self) -> bool:
        """Get whether to use exponential backoff."""
        return self.rate_limiting_config.get('use_exponential_backoff', True)
    
    @property
    def headless(self) -> bool:
        """Get whether to run browser in headless mode."""
        return self.browser_config.get('headless', True)
    
    @property
    def browser_type(self) -> str:
        """Get browser type."""
        return self.browser_config.get('browser_type', 'chromium')
    
    @property
    def viewport(self) -> Dict[str, int]:
        """Get viewport configuration."""
        return self.browser_config.get('viewport', {'width': 1280, 'height': 720})
    
    @property
    def association_selector(self) -> str:
        """Get primary association selector."""
        return self.association_config.get('primary_selector', "a[onclick*='select_association']")
    
    @property
    def alternative_selectors(self) -> List[str]:
        """Get alternative association selectors."""
        return self.association_config.get('alternative_selectors', [])
    
    @property
    def target_association(self) -> Dict[str, str]:
        """Get target association details."""
        return self.association_config.get('target_association', {})
    
    @property
    def season_selectors(self) -> Dict[str, str]:
        """Get season selection selectors."""
        return self.season_config.get('selectors', {})
    
    @property
    def season_selection_strategy(self) -> str:
        """Get season selection strategy."""
        return self.season_config.get('selection_strategy', 'latest')
    
    @property
    def specific_season(self) -> Optional[str]:
        """Get specific season to select."""
        return self.season_config.get('specific_season')
    
    @property
    def take_screenshots(self) -> bool:
        """Get whether to take screenshots for debugging."""
        return self.association_config.get('take_screenshots', False)
    
    def validate_credentials(self) -> bool:
        """
        Validate that USA Hockey credentials are available.
        
        Returns:
            bool: True if credentials are available, False otherwise
        """
        has_username = self.username is not None and self.username.strip() != ""
        has_password = self.password is not None and self.password.strip() != ""
        
        if not has_username:
            logger.warning("USA Hockey username not found in config file")
        
        if not has_password:
            logger.warning("USA Hockey password not found in config file")
        
        return has_username and has_password
    
    def ensure_download_directory(self) -> Path:
        """
        Ensure the download directory exists.
        
        Returns:
            Path: Path to the download directory
        """
        download_dir = self.download_directory
        download_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Download directory ensured: {download_dir}")
        return download_dir
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        return self._config.copy() 