#!/usr/bin/env python3
"""
Master Reports Workflow
Handles the workflow for downloading and processing USA Hockey master registration reports.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
import pandas as pd

from record.usa_hockey_client import USAHockeyClient, USAHockeyClientError
from config.usa_hockey_config import USAHockeyConfig
from config.logging_config import get_logger
from .data_processor import DataProcessor

logger = get_logger(__name__)


class MasterReportsWorkflowError(Exception):
    """Base exception for master reports workflow errors."""
    pass


class MasterReportsWorkflow:
    """Workflow for managing USA Hockey master registration reports."""
    
    def __init__(self, config: USAHockeyConfig):
        """
        Initialize master reports workflow.
        
        Args:
            config: USA Hockey configuration object
        """
        self.config = config
        self.client: Optional[USAHockeyClient] = None
        self.data_processor = DataProcessor()
        
        logger.info("MasterReportsWorkflow initialized")
    
    async def download_master_report(
        self, 
        filename: Optional[str] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Optional[Path]:
        """
        Download master registration report with progress tracking.
        
        Args:
            filename: Optional custom filename for the download
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
                progress_callback("Downloading master report...", 0.5)
            
            # Download the report
            download_path = await self.client.download_master_report(filename)
            
            if progress_callback:
                progress_callback("Download completed", 1.0)
            
            return download_path
            
        except Exception as e:
            logger.error(f"Error in download workflow: {e}")
            if progress_callback:
                progress_callback(f"Error: {str(e)}", 0.0)
            return None
        finally:
            if self.client:
                await self.client.disconnect()
                self.client = None
    
    async def get_available_seasons(self) -> List[Dict[str, Any]]:
        """
        Get list of available seasons.
        
        Returns:
            List[Dict[str, Any]]: List of available seasons
        """
        try:
            self.client = USAHockeyClient(self.config)
            await self.client.connect()
            
            # Authenticate
            auth_success = await self.client.authenticate()
            if not auth_success:
                logger.error("Authentication failed")
                return []
            
            # Get available seasons
            seasons = await self.client.get_available_seasons()
            return seasons
            
        except Exception as e:
            logger.error(f"Error getting available seasons: {e}")
            return []
        finally:
            if self.client:
                await self.client.disconnect()
                self.client = None
    
    async def get_association_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current association information.
        
        Returns:
            Optional[Dict[str, Any]]: Association information if available
        """
        try:
            self.client = USAHockeyClient(self.config)
            await self.client.connect()
            
            # Authenticate
            auth_success = await self.client.authenticate()
            if not auth_success:
                logger.error("Authentication failed")
                return None
            
            # Get association info
            association_info = await self.client.get_association_info()
            return association_info
            
        except Exception as e:
            logger.error(f"Error getting association info: {e}")
            return None
        finally:
            if self.client:
                await self.client.disconnect()
                self.client = None
    
    def process_master_report(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Process a downloaded master report file.
        
        Args:
            file_path: Path to the downloaded CSV file
            
        Returns:
            Optional[pd.DataFrame]: Processed data as DataFrame if successful, None otherwise
        """
        try:
            if not file_path.exists():
                logger.error(f"File does not exist: {file_path}")
                return None
            
            # Process the CSV file
            df = self.data_processor.load_csv(file_path)
            if df is None:
                return None
            
            # Clean and validate the data
            df = self.data_processor.clean_data(df)
            
            logger.info(f"Successfully processed master report: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error processing master report: {e}")
            return None
    
    def export_to_excel(self, df: pd.DataFrame, output_path: Path) -> bool:
        """
        Export processed data to Excel format.
        
        Args:
            df: DataFrame to export
            output_path: Path for the output Excel file
            
        Returns:
            bool: True if export successful, False otherwise
        """
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export to Excel
            df.to_excel(output_path, index=False, engine='openpyxl')
            
            logger.info(f"Successfully exported data to Excel: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False
    
    def get_report_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a summary of the master report data.
        
        Args:
            df: DataFrame containing the master report data
            
        Returns:
            Dict[str, Any]: Summary statistics and information
        """
        try:
            if df is None or df.empty:
                return {
                    "total_records": 0,
                    "columns": [],
                    "summary": "No data available"
                }
            
            summary = {
                "total_records": len(df),
                "columns": list(df.columns),
                "column_count": len(df.columns),
                "data_types": df.dtypes.to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
                "unique_values": {}
            }
            
            # Add unique value counts for categorical columns
            for col in df.columns:
                if df[col].dtype == 'object':
                    summary["unique_values"][col] = df[col].nunique()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating report summary: {e}")
            return {
                "total_records": 0,
                "columns": [],
                "summary": f"Error generating summary: {str(e)}"
            }
    
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
        List all downloaded master report files.
        
        Returns:
            List[Path]: List of downloaded report files
        """
        try:
            download_dir = self.config.ensure_download_directory()
            csv_files = list(download_dir.glob("*.csv"))
            
            # Sort by modification time (newest first)
            csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            return csv_files
            
        except Exception as e:
            logger.error(f"Error listing downloaded reports: {e}")
            return [] 