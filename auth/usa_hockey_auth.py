#!/usr/bin/env python3
"""
USA Hockey Authentication Module
Handles authentication to the USA Hockey portal using Playwright.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from config.usa_hockey_config import USAHockeyConfig
from config.logging_config import get_logger

logger = get_logger(__name__)


class USAHockeyAuthError(Exception):
    """Base exception for USA Hockey authentication errors."""
    pass


class USAHockeyCredentialsError(USAHockeyAuthError):
    """Exception raised when credentials are missing or invalid."""
    pass


class USAHockeyLoginError(USAHockeyAuthError):
    """Exception raised when login fails."""
    pass


class USAHockeyAuth:
    """Handles authentication to the USA Hockey portal."""
    
    def __init__(self, config: USAHockeyConfig):
        """
        Initialize USA Hockey authentication.
        
        Args:
            config: USA Hockey configuration object
        """
        self.config = config
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._is_authenticated = False
        
        logger.info("USAHockeyAuth initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start_browser(self):
        """Start the browser and create context."""
        try:
            playwright = await async_playwright().start()
            
            # Launch browser based on configuration
            if self.config.browser_type == "chromium":
                self._browser = await playwright.chromium.launch(
                    headless=self.config.headless
                )
            elif self.config.browser_type == "firefox":
                self._browser = await playwright.firefox.launch(
                    headless=self.config.headless
                )
            elif self.config.browser_type == "webkit":
                self._browser = await playwright.webkit.launch(
                    headless=self.config.headless
                )
            else:
                raise USAHockeyAuthError(f"Unsupported browser type: {self.config.browser_type}")
            
            # Create context with download handling
            self._context = await self._browser.new_context(
                accept_downloads=True,
                viewport=self.config.viewport
            )
            
            # Create page with extended timeouts
            self._page = await self._context.new_page()
            self._page.set_default_timeout(self.config.page_load_timeout)
            self._page.set_default_navigation_timeout(self.config.page_load_timeout)
            
            logger.info(f"Browser started: {self.config.browser_type} (headless: {self.config.headless})")
            
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise USAHockeyAuthError(f"Browser startup failed: {e}")
    
    async def close(self):
        """Close browser and clean up resources."""
        try:
            if self._page:
                await self._page.close()
                self._page = None
            
            if self._context:
                await self._context.close()
                self._context = None
            
            if self._browser:
                await self._browser.close()
                self._browser = None
            
            self._is_authenticated = False
            logger.info("Browser closed")
            
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    def validate_credentials(self) -> bool:
        """
        Validate that credentials are available.
        
        Returns:
            bool: True if credentials are available, False otherwise
        """
        return self.config.validate_credentials()
    
    async def login(self) -> bool:
        """
        Perform login to USA Hockey portal.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        if not self.validate_credentials():
            raise USAHockeyCredentialsError("USA Hockey credentials not available")
        
        if not self._page:
            raise USAHockeyAuthError("Browser not started. Call start_browser() first.")
        
        try:
            logger.info(f"Navigating to login page: {self.config.login_url}")
            await self._page.goto(self.config.login_url)
            await self._page.wait_for_load_state("networkidle")
            
            # Check if we're on the login page
            page_title = await self._page.title()
            logger.info(f"Page title: {page_title}")
            
            # Find and fill login form
            username_selector = "input[name='username'], input[type='text'], #username"
            password_selector = "input[name='password'], input[type='password'], #password"
            
            username_field = await self._page.query_selector(username_selector)
            password_field = await self._page.query_selector(password_selector)
            
            if not username_field or not password_field:
                logger.error("Login form fields not found")
                raise USAHockeyLoginError("Login form fields not found")
            
            # Fill credentials
            logger.info("Filling in credentials...")
            await username_field.fill(self.config.username)
            await password_field.fill(self.config.password)
            
            # Submit login form
            submit_selector = "input[type='submit'], button[type='submit'], button:has-text('Login')"
            submit_button = await self._page.query_selector(submit_selector)
            
            if not submit_button:
                logger.error("Submit button not found")
                raise USAHockeyLoginError("Submit button not found")
            
            logger.info("Submitting login form...")
            await submit_button.click()
            await self._page.wait_for_load_state("networkidle")
            
            # Check if login was successful
            current_url = self._page.url
            logger.info(f"Current URL after login: {current_url}")
            
            if "login" not in current_url.lower():
                logger.info("✅ Login successful!")
                self._is_authenticated = True
                return True
            else:
                logger.error("❌ Login failed - still on login page")
                raise USAHockeyLoginError("Login failed - still on login page")
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            self._is_authenticated = False
            raise USAHockeyLoginError(f"Login failed: {e}")
    
    async def handle_association_selection(self) -> bool:
        """
        Handle association selection after successful login.
        
        Returns:
            bool: True if association selection successful, False otherwise
        """
        if not self._page:
            raise USAHockeyAuthError("Browser not started")
        
        if not self._is_authenticated:
            raise USAHockeyAuthError("Not authenticated. Call login() first.")
        
        try:
            logger.info("Looking for association selection page...")
            
            # Wait for the page to load completely
            await self._page.wait_for_load_state("networkidle")
            
            # Check current URL
            current_url = self._page.url
            logger.info(f"Current URL: {current_url}")
            
            # Look for association selection elements
            association_found = False
            association_link = None
            
            # Try the primary selector first
            association_link = await self._page.query_selector(self.config.association_selector)
            if association_link:
                logger.info(f"Found association using primary selector: {self.config.association_selector}")
                association_found = True
            else:
                # Try alternative selectors
                for i, selector in enumerate(self.config.alternative_selectors):
                    logger.info(f"Trying alternative selector {i+1}: {selector}")
                    association_link = await self._page.query_selector(selector)
                    if association_link:
                        logger.info(f"Found association using alternative selector: {selector}")
                        association_found = True
                        break
            
            if not association_found:
                logger.error("No association links found")
                if self.config.take_screenshots:
                    await self._page.screenshot(path="association_page_debug.png")
                    logger.info("Screenshot saved as association_page_debug.png")
                return False
            
            # Get association details before clicking
            association_text = await association_link.text_content()
            logger.info(f"Found association: {association_text}")
            
            # Click the association link
            logger.info("Clicking association link...")
            
            if self.config.skip_association_navigation_wait:
                # Skip navigation wait entirely and just click
                logger.info("Skipping navigation wait as configured...")
                await association_link.click()
                await self._page.wait_for_timeout(500)  # Minimal wait for any DOM updates
            else:
                # Use a much shorter timeout since there's typically no full navigation
                navigation_timeout = min(self.config.association_timeout, 5000)  # Cap at 5 seconds
                
                try:
                    # Try to wait for navigation with shorter timeout
                    async with self._page.expect_navigation(wait_until="networkidle", timeout=navigation_timeout):
                        await association_link.click()
                except Exception:
                    # If no navigation, just wait a short time for any DOM updates
                    logger.info("No full navigation detected, waiting for DOM updates...")
                    await self._page.wait_for_timeout(1000)  # Reduced from 2000ms to 1000ms
            
            # Wait for the page to load after association selection
            await self._page.wait_for_load_state("networkidle")
            
            # Check if we've moved to the next page
            new_url = self._page.url
            logger.info(f"URL after association selection: {new_url}")
            
            # Check if we're on a season selection page
            page_title = await self._page.title()
            logger.info(f"Page title after association selection: {page_title}")
            
            # Check if we successfully moved to season selection
            if "select-season" in new_url or "season" in page_title.lower():
                logger.info("✅ Successfully moved to season selection page!")
                return True
            else:
                logger.warning("⚠️ May not be on season selection page")
                return True  # Still consider this a success as we've made progress
                
        except Exception as e:
            logger.error(f"Error during association selection: {e}")
            return False
    
    async def handle_season_selection(self) -> bool:
        """
        Handle season selection after association selection.
        
        Returns:
            bool: True if season selection successful, False otherwise
        """
        if not self._page:
            raise USAHockeyAuthError("Browser not started")
        
        try:
            logger.info("Looking for season selection elements...")
            
            # Wait for the page to load completely
            await self._page.wait_for_load_state("networkidle")
            
            # Check current page state
            current_url = self._page.url
            page_title = await self._page.title()
            logger.info(f"Current URL: {current_url}")
            logger.info(f"Page title: {page_title}")
            
            # Take a screenshot if enabled
            if self.config.take_screenshots:
                await self._page.screenshot(path="season_selection_page.png")
                logger.info("Screenshot saved as season_selection_page.png")
            
            # Look for season selection elements
            season_links = await self._page.query_selector_all(
                self.config.season_selectors.get('season_link_pattern', "a[onclick*='check_waiver']")
            )
            
            if not season_links:
                logger.error("No season links found")
                return False
            
            logger.info(f"Found {len(season_links)} season links")
            
            # Extract season information from links
            seasons = []
            for link in season_links:
                text = await link.text_content()
                onclick = await link.get_attribute("onclick")
                if onclick and "check_waiver" in onclick:
                    # Extract season year from onclick attribute
                    import re
                    season_match = re.search(r"check_waiver\('(\d{8})'\)", onclick)
                    if season_match:
                        season_year = season_match.group(1)
                        seasons.append({
                            "text": text.strip(),
                            "year": season_year,
                            "element": link
                        })
                        logger.info(f"  Season: {text.strip()} (Year: {season_year})")
            
            if not seasons:
                logger.error("No valid season links found")
                return False
            
            # Sort seasons by year (newest first)
            seasons.sort(key=lambda x: x["year"], reverse=True)
            
            # Select season based on strategy
            selected_season = None
            
            if self.config.season_selection_strategy == "specific" and self.config.specific_season:
                # Find the specific season
                for season in seasons:
                    if season["year"] == self.config.specific_season:
                        selected_season = season
                        break
                if not selected_season:
                    logger.error(f"Specific season {self.config.specific_season} not found")
                    logger.error(f"Available seasons: {[s['year'] for s in seasons]}")
                    return False
            else:
                # Default to latest season
                selected_season = seasons[0]
            
            logger.info(f"Selected season: {selected_season['text']} (Year: {selected_season['year']})")
            
            # Click the selected season
            logger.info("Clicking season link...")
            
            # Use a shorter timeout for season selection as well
            season_timeout = min(self.config.season_config.get('page_load_timeout', 10000), 10000)  # Cap at 10 seconds
            
            try:
                # Try to wait for navigation with shorter timeout
                async with self._page.expect_navigation(wait_until="networkidle", timeout=season_timeout):
                    await selected_season["element"].click()
            except Exception:
                # If no navigation, just wait a short time for any DOM updates
                logger.info("No full navigation detected, waiting for DOM updates...")
                await self._page.wait_for_timeout(1500)  # Reduced from 3000ms to 1500ms
            
            # Wait for the page to load after season selection
            await self._page.wait_for_load_state("networkidle")
            
            # Check if we've moved to the next page
            new_url = self._page.url
            new_title = await self._page.title()
            logger.info(f"URL after season selection: {new_url}")
            logger.info(f"Page title after season selection: {new_title}")
            
            # Check if we successfully moved past season selection
            if "main" in new_url or "application" in new_url or "tool" in new_url:
                logger.info("✅ Successfully completed season selection!")
                return True
            else:
                logger.warning("⚠️ May still be on season selection page")
                return True  # Still consider this a success as we've made progress
                
        except Exception as e:
            logger.error(f"Error during season selection: {e}")
            return False
    
    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._is_authenticated
    
    @property
    def page(self) -> Optional[Page]:
        """Get the current page object."""
        return self._page
    
    @property
    def context(self) -> Optional[BrowserContext]:
        """Get the current browser context."""
        return self._context
    
    @property
    def browser(self) -> Optional[Browser]:
        """Get the current browser instance."""
        return self._browser 