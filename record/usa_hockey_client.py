#!/usr/bin/env python3
"""
USA Hockey Client
Core client for interacting with USA Hockey portal and downloading reports.
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from playwright.async_api import Page

from auth.usa_hockey_auth import USAHockeyAuth, USAHockeyAuthError
from config.usa_hockey_config import USAHockeyConfig
from config.logging_config import get_logger

logger = get_logger(__name__)


class USAHockeyClientError(Exception):
    """Base exception for USA Hockey client errors."""
    pass


class USAHockeyDownloadError(USAHockeyClientError):
    """Exception raised when download fails."""
    pass


class USAHockeyClient:
    """Core client for USA Hockey portal operations."""
    
    def __init__(self, config: USAHockeyConfig):
        """
        Initialize USA Hockey client.
        
        Args:
            config: USA Hockey configuration object
        """
        self.config = config
        self.auth: Optional[USAHockeyAuth] = None
        
        logger.info("USAHockeyClient initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self):
        """Connect to USA Hockey portal."""
        try:
            self.auth = USAHockeyAuth(self.config)
            await self.auth.start_browser()
            logger.info("Connected to USA Hockey portal")
        except Exception as e:
            logger.error(f"Failed to connect to USA Hockey portal: {e}")
            raise USAHockeyClientError(f"Connection failed: {e}")
    
    async def disconnect(self):
        """Disconnect from USA Hockey portal."""
        if self.auth:
            await self.auth.close()
            self.auth = None
            logger.info("Disconnected from USA Hockey portal")
    
    async def authenticate(self) -> bool:
        """
        Perform complete authentication flow.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        if not self.auth:
            raise USAHockeyClientError("Not connected. Call connect() first.")
        
        try:
            # Step 1: Login
            logger.info("Starting authentication flow...")
            login_success = await self.auth.login()
            if not login_success:
                logger.error("Login failed")
                return False
            
            # Step 2: Handle association selection
            logger.info("Handling association selection...")
            association_success = await self.auth.handle_association_selection()
            if not association_success:
                logger.error("Association selection failed")
                return False
            
            # Step 3: Handle season selection
            logger.info("Handling season selection...")
            season_success = await self.auth.handle_season_selection()
            if not season_success:
                logger.error("Season selection failed")
                return False
            
            logger.info("✅ Authentication flow completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Authentication flow failed: {e}")
            return False
    
    async def download_master_report(self, filename: Optional[str] = None) -> Optional[Path]:
        """
        Download master registration report.
        
        Args:
            filename: Optional custom filename for the download
            
        Returns:
            Optional[Path]: Path to downloaded file if successful, None otherwise
        """
        if not self.auth or not self.auth.is_authenticated:
            raise USAHockeyClientError("Not authenticated. Call authenticate() first.")
        
        try:
            # Ensure download directory exists
            download_dir = self.config.ensure_download_directory()
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = self.config.filename_pattern.format(timestamp=timestamp)
            
            # Ensure filename has .csv extension
            if not filename.endswith('.csv'):
                filename += '.csv'
            
            # Set the download path
            download_path = download_dir / filename
            
            logger.info(f"Starting master report download to: {download_path}")
            
            # Navigate to reports page
            page = self.auth.page
            if not page:
                raise USAHockeyClientError("No page available")
            
            logger.info(f"Navigating to reports page: {self.config.reports_url}")
            await page.goto(self.config.reports_url)
            await page.wait_for_load_state("networkidle")
            
            # Take screenshot for debugging if enabled
            if self.config.take_screenshots:
                await page.screenshot(path="reports_page.png")
                logger.info("Screenshot saved as reports_page.png")
            
            # Look for master registration report link
            master_link = await page.query_selector(
                "a[href*='master_registration.csv'], a:has-text('Master Registration')"
            )
            
            if not master_link:
                logger.error("Master registration report link not found on reports page")
                return None
            
            logger.info("Found master registration report link, clicking...")
            
            # Set up download handling BEFORE clicking
            async with page.expect_download(timeout=self.config.download_timeout) as download_info:
                logger.info("Clicking master registration link (this may take several minutes due to slow backend)...")
                await master_link.click()
                
                # Wait for download
                logger.info("Waiting for download to start...")
                download = await download_info.value
            
            logger.info(f"Download started: {download.suggested_filename}")
            
            # Save the file
            await download.save_as(download_path)
            
            logger.info(f"✅ Successfully downloaded master report to: {download_path}")
            
            # Verify the file was downloaded and has content
            if download_path.exists():
                file_size = download_path.stat().st_size
                logger.info(f"File size: {file_size} bytes")
                
                if file_size > 0:
                    logger.info("✅ File downloaded successfully with content!")
                    return download_path
                else:
                    logger.warning("⚠️ File downloaded but appears to be empty")
                    return download_path
            else:
                logger.error("❌ File was not saved properly")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading master report: {e}")
            raise USAHockeyDownloadError(f"Download failed: {e}")
    
    async def get_available_seasons(self) -> List[Dict[str, Any]]:
        """
        Get list of available seasons.
        
        Returns:
            List[Dict[str, Any]]: List of available seasons with details
        """
        if not self.auth or not self.auth.is_authenticated:
            raise USAHockeyClientError("Not authenticated. Call authenticate() first.")
        
        try:
            page = self.auth.page
            if not page:
                raise USAHockeyClientError("No page available")
            
            # Navigate to season selection page if not already there
            current_url = page.url
            if "select-season" not in current_url and "season" not in current_url.lower():
                logger.info("Navigating to season selection page...")
                # This would need to be implemented based on the actual portal structure
                pass
            
            # Look for season selection elements
            season_links = await page.query_selector_all(
                self.config.season_selectors.get('season_link_pattern', "a[onclick*='check_waiver']")
            )
            
            if not season_links:
                logger.warning("No season links found")
                return []
            
            # Extract season information from links
            seasons = []
            for link in season_links:
                text = await link.text_content()
                onclick = await link.get_attribute("onclick")
                if onclick and "check_waiver" in onclick:
                    # Extract season year from onclick attribute
                    season_match = re.search(r"check_waiver\('(\d{8})'\)", onclick)
                    if season_match:
                        season_year = season_match.group(1)
                        seasons.append({
                            "text": text.strip(),
                            "year": season_year,
                            "display_name": f"{season_year[:4]}-{season_year[4:]}"
                        })
            
            # Sort seasons by year (newest first)
            seasons.sort(key=lambda x: x["year"], reverse=True)
            
            logger.info(f"Found {len(seasons)} available seasons")
            return seasons
            
        except Exception as e:
            logger.error(f"Error getting available seasons: {e}")
            return []
    
    async def get_association_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current association information.
        
        Returns:
            Optional[Dict[str, Any]]: Association information if available
        """
        if not self.auth or not self.auth.is_authenticated:
            raise USAHockeyClientError("Not authenticated. Call authenticate() first.")
        
        try:
            page = self.auth.page
            if not page:
                raise USAHockeyClientError("No page available")
            
            # Look for association information on the current page
            association_element = await page.query_selector(self.config.association_selector)
            if association_element:
                association_text = await association_element.text_content()
                return {
                    "name": association_text.strip(),
                    "selector": self.config.association_selector
                }
            
            # Try alternative selectors
            for selector in self.config.alternative_selectors:
                association_element = await page.query_selector(selector)
                if association_element:
                    association_text = await association_element.text_content()
                    return {
                        "name": association_text.strip(),
                        "selector": selector
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting association info: {e}")
            return None
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to USA Hockey portal."""
        return self.auth is not None and self.auth.browser is not None
    
    @property
    def is_authenticated(self) -> bool:
        """Check if authenticated with USA Hockey portal."""
        return self.auth is not None and self.auth.is_authenticated 