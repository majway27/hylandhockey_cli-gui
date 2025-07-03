"""
Configuration manager for the jersey order management system.
Provides a class-based interface to access configuration settings.
"""

import os
from pathlib import Path
from ruamel.yaml import YAML
from typing import Any, Dict, List, Optional


class ConfigManager:
    """Manages configuration settings loaded from YAML files."""
    
    def __init__(self, config_file: Optional[str] = None, test: bool = False):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Optional path to a specific config file. If not provided,
                        will look for config.yaml in the config directory.
            test: If True, will use test configuration values instead of production ones.
        """
        self._config: Dict[str, Any] = {}
        self._test = test
        self._load_config(config_file)
        print(f"Test mode: {self._test}")
    
    def _load_config(self, config_file: Optional[str] = None) -> None:
        """Load configuration from YAML file."""
        if config_file is None:
            # Get the directory where this file is located
            current_dir = Path(__file__).parent
            config_path = current_dir / 'config.yaml'
        else:
            config_path = Path(config_file)
        
        if not config_path.exists():
            template_path = config_path.parent / 'config.yaml.template'
            if template_path.exists():
                raise FileNotFoundError(
                    f"config.yaml not found at {config_path}. Please copy "
                    f"config.yaml.template to config.yaml and update the values."
                )
            else:
                raise FileNotFoundError(
                    f"Neither config.yaml nor config.yaml.template found in {config_path.parent}"
                )
        
        yaml = YAML(typ='safe')
        with open(config_path) as f:
            self._config = yaml.load(f)
    
    def _get_value(self, key: str) -> Any:
        """Get a configuration value, respecting test mode."""
        if self._test:
            test_key = f"{key}_test"
            if test_key not in self._config:
                raise KeyError(f"Test configuration value '{test_key}' not found")
            return self._config[test_key]
        return self._config[key]
    
    @property
    def is_test_mode(self) -> bool:
        """Check if the config object is in test mode.
        
        Returns:
            bool: True if the config object was created with test=True, False otherwise.
        """
        return self._test
    
    # Auth
    @property
    def scopes(self) -> List[str]:
        """Get Google API scopes."""
        return self._get_value('scopes')
    
    # Record
    @property
    def demo_spreadsheet_name(self) -> str:
        """Get demo spreadsheet name."""
        return self._get_value('demo_spreadsheet_name')
    
    @property
    def jersey_spreadsheet_name(self) -> str:
        """Get jersey spreadsheet name."""
        return self._get_value('jersey_spreadsheet_name')
    
    @property
    def demo_spreadsheet_id(self) -> str:
        """Get demo spreadsheet ID."""
        return self._get_value('demo_spreadsheet_id')
    
    @property
    def jersey_spreadsheet_id(self) -> str:
        """Get jersey spreadsheet ID."""
        return self._get_value('jersey_spreadsheet_id')

    @property
    def demo_worksheet_form_responses_gid(self) -> str:
        """Get demo worksheet form responses GID."""
        return self._get_value('demo_worksheet_form_responses_gid')
    
    @property
    def demo_worksheet_jersey_orders_gid(self) -> str:
        """Get demo worksheet jersey orders GID."""
        return self._get_value('demo_worksheet_jersey_orders_gid')
    
    @property
    def jersey_worksheet_jersey_orders_gid(self) -> str:
        """Get jersey worksheet jersey orders GID."""
        return self._get_value('jersey_worksheet_jersey_orders_gid')
    
    @property
    def jersey_worksheet_jersey_orders_name(self) -> str:
        """Get jersey worksheet jersey orders name."""
        return self._get_value('jersey_worksheet_jersey_orders_name')
    
    # Message
    @property
    def demo_sender_email(self) -> str:
        """Get demo sender email."""
        return self._get_value('demo_sender_email')
    
    @property
    def demo_default_to_email(self) -> str:
        """Get demo default recipient email."""
        return self._get_value('demo_default_to_email')
    
    @property
    def jersey_sender_email(self) -> str:
        """Get jersey sender email."""
        return self._get_value('jersey_sender_email')
    
    @property
    def jersey_default_to_email(self) -> str:
        """Get jersey default recipient email."""
        return self._get_value('jersey_default_to_email')
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: The configuration key to look up
            default: Default value to return if key is not found
            
        Returns:
            The configuration value or default if not found
            
        Raises:
            KeyError: If in test mode and the test key is not found
        """
        if self._test:
            test_key = f"{key}_test"
            if test_key not in self._config:
                raise KeyError(f"Test configuration value '{test_key}' not found")
            return self._config[test_key]
        return self._config.get(key, default) 