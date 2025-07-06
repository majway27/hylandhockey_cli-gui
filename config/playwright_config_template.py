#!/usr/bin/env python3
"""
Playwright configuration file for USA Hockey Portal automation
"""

# Association selection configuration
ASSOCIATION_CONFIG = {
    # Primary selector for association links
    "primary_selector": "a[onclick*='select_association']",
    
    # Alternative selectors to try if primary fails
    "alternative_selectors": [
        "a:has-text('HYLAND HILLS JR HOCKEY ASSOCIATION')",
        "li a:has-text('COH1035')",
        ".registry_association a",
        "ul li a"
    ],
    
    # Specific association to target (if you want to select a specific one)
    "target_association": {
        "code": "COH1035",
        "name": "NICE ICE HOCKEY ASSOCIATION"
    },
    
    # Wait time for page loads (in milliseconds)
    "page_load_timeout": 30000,
    
    # Whether to take screenshots for debugging
    "take_screenshots": False,
    
    # Screenshot file names
    "screenshot_files": {
        "association_page_debug": "association_page_debug.png",
        "after_association_selection": "after_association_selection.png",
        "after_login": "after_login.png"
    }
}

# Login configuration
LOGIN_CONFIG = {
    "login_url": "https://portal.usahockey.com/tool/login",
    "base_url": "https://portal.usahockey.com",
    
    # Form selectors
    "selectors": {
        "username": "input[name='username'], input[type='text'], #username",
        "password": "input[name='password'], input[type='password'], #password",
        "submit": "input[type='submit'], button[type='submit'], button:has-text('Login')"
    }
}

# Browser configuration
BROWSER_CONFIG = {
    "headless": True,
    "browser_type": "chromium",
    "viewport": {
        "width": 1280,
        "height": 720
    }
}

# Season selection configuration
SEASON_CONFIG = {
    # Selectors for season elements
    "selectors": {
        "season_list": "#season-select",
        "season_link": "#season-select li a",
        "season_link_pattern": "a[onclick*='check_waiver']"
    },
    
    # Season selection strategy
    "selection_strategy": "latest",  # Options: "latest", "specific", "manual"
    
    # Specific season to select (if strategy is "specific")
    "specific_season": None,  # e.g., "20232024" for 2023-2024 season
    
    # Whether to take screenshots for debugging
    "take_screenshots": False,
    
    # Screenshot file names
    "screenshot_files": {
        "season_page": "season_selection_page.png",
        "after_season_selection": "after_season_selection.png",
        "after_association_selection": "after_association_selection.png",
        "final_page": "final_page.png"
    },
    
    # Wait time for page loads (in milliseconds)
    "page_load_timeout": 30000
} 