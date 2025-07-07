#!/usr/bin/env python3
"""
Custom Reports Workflow
Handles the workflow for downloading and managing USA Hockey custom reports.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable

from record.usa_hockey_client import USAHockeyClient, USAHockeyClientError
from config.usa_hockey_config import USAHockeyConfig
from config.logging_config import get_logger
from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class CustomReportsWorkflowError(Exception):
    """Base exception for custom reports workflow errors."""
    pass


class CustomReportsWorkflow:
    """Workflow for managing USA Hockey custom reports."""
    
    def __init__(self, config: USAHockeyConfig):
        """
        Initialize custom reports workflow.
        
        Args:
            config: USA Hockey configuration object
        """
        self.config = config
        self.client: Optional[USAHockeyClient] = None
        logger.info("CustomReportsWorkflow initialized")

    async def download_custom_report(
        self, 
        fields: List[str],
        filters: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
        format: str = "csv",
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Optional[Path]:
        """
        Download custom report with progress tracking.
        
        Args:
            fields: List of field names to include in the report
            filters: Optional dictionary of filters to apply
            filename: Optional custom filename for the download
            format: Report format ('csv' or 'xls')
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Optional[Path]: Path to downloaded file if successful, None otherwise
        """
        try:
            if progress_callback:
                progress_callback("Connecting to USA Hockey portal...", 0.1)
            
            # Connect to USA Hockey portal
            self.client = USAHockeyClient(self.config)
            await self.client.connect()
            
            if progress_callback:
                progress_callback("Authenticating...", 0.2)
            
            # Authenticate
            auth_success = await self.client.authenticate()
            if not auth_success:
                logger.error("Authentication failed")
                if progress_callback:
                    progress_callback("Authentication failed", 0.0)
                return None
            
            if progress_callback:
                progress_callback("Downloading custom report...", 0.5)
            
            # Download the custom report
            result = await self.client.download_custom_report(
                fields=fields,
                filters=filters,
                filename=filename,
                format=format
            )
            
            if progress_callback:
                progress_callback("Custom report download completed", 1.0)
            
            return result
            
        except Exception as e:
            logger.error(f"Error downloading custom report: {e}")
            if progress_callback:
                progress_callback(f"Error: {str(e)}", 0.0)
            return None
        finally:
            if self.client:
                await self.client.disconnect()
                self.client = None

    def get_available_fields(self) -> List[str]:
        """
        Get list of available fields for custom reports.
        
        Returns:
            List[str]: List of available field names
        """
        return [
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

    def validate_credentials(self) -> bool:
        """
        Validate that USA Hockey credentials are available.
        
        Returns:
            bool: True if credentials are available, False otherwise
        """
        return self.config.validate_credentials()

    def get_download_directory(self) -> Path:
        """
        Get the download directory path.
        
        Returns:
            Path: Download directory path
        """
        return self.config.download_directory

    def list_downloaded_reports(self) -> List[Path]:
        """
        List all downloaded custom report files.
        
        Returns:
            List[Path]: List of downloaded report files
        """
        try:
            download_dir = self.config.ensure_download_directory()
            csv_files = list(download_dir.glob("custom_report_*.csv"))
            # Sort by modification time (newest first)
            csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return csv_files
        except Exception as e:
            logger.error(f"Error listing downloaded custom reports: {e}")
            return []


async def main():
    """Test function to run custom report download."""
    config_manager = ConfigManager()
    config = USAHockeyConfig(config_manager.as_dict())
    workflow = CustomReportsWorkflow(config)
    
    # Define fields for the custom report
    fields = [
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
    
    # Define filters
    filters = {"State": {"type": "eq", "value": "CO"}}
    
    print("Starting custom report download test...")
    result = await workflow.download_custom_report(fields=fields, filters=filters)
    
    if result:
        print(f"✅ Successfully downloaded custom report to: {result}")
    else:
        print("❌ Failed to download custom report")


if __name__ == "__main__":
    asyncio.run(main()) 