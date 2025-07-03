import os.path
import pickle
import logging
from pathlib import Path
from typing import Optional, Tuple

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Custom exception for authentication-related errors."""
    pass

class TokenExpiredError(AuthenticationError):
    """Exception raised when OAuth tokens have expired and cannot be refreshed."""
    pass

class CredentialsNotFoundError(AuthenticationError):
    """Exception raised when credentials file is not found."""
    pass

def get_credentials(config_manager: ConfigManager) -> Credentials:
    """
    Get Google API credentials, either from existing token or by initiating OAuth flow.
    Uses different credential files when in test mode.
    
    Args:
        config_manager: ConfigManager instance
    
    Returns:
        google.oauth2.credentials.Credentials: The credentials object for Google API access
        
    Raises:
        TokenExpiredError: When tokens have expired and cannot be refreshed
        CredentialsNotFoundError: When credentials file is not found
        AuthenticationError: For other authentication-related errors
    """
    creds = None
    
    # Get the config directory path
    config_dir = Path(__file__).parent.parent / 'config'
    
    # Use different files based on test mode
    suffix = '_test' if config_manager.is_test_mode else ''
    token_path = config_dir / f'token{suffix}.pickle'
    credentials_path = config_dir / f'credentials{suffix}.json'
    
    # Check if credentials file exists
    if not credentials_path.exists():
        error_msg = f"Credentials file not found: {credentials_path}"
        logger.error(error_msg)
        raise CredentialsNotFoundError(error_msg)
    
    # The file token.pickle stores the user's access and refresh tokens
    if token_path.exists():
        try:
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
            logger.debug("Loaded existing credentials from token file")
        except Exception as e:
            logger.warning(f"Failed to load existing token file: {e}")
            # Remove corrupted token file
            try:
                token_path.unlink()
                logger.info("Removed corrupted token file")
            except Exception:
                pass
            creds = None
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired credentials...")
                creds.refresh(Request())
                logger.info("Credentials refreshed successfully")
            except RefreshError as e:
                logger.error(f"Failed to refresh credentials: {e}")
                # Remove the expired token file
                try:
                    token_path.unlink()
                    logger.info("Removed expired token file")
                except Exception:
                    pass
                raise TokenExpiredError(f"OAuth tokens have expired and cannot be refreshed. Please re-authenticate. Error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error refreshing credentials: {e}")
                raise AuthenticationError(f"Failed to refresh credentials: {e}")
        else:
            logger.info("No valid credentials found, initiating OAuth flow...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), config_manager.scopes)
                creds = flow.run_local_server(port=0)
                logger.info("OAuth flow completed successfully")
            except Exception as e:
                logger.error(f"OAuth flow failed: {e}")
                raise AuthenticationError(f"Failed to complete OAuth authentication: {e}")
        
        # Save the credentials for the next run
        try:
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
            logger.info("Credentials saved successfully")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            # Don't raise here as the credentials are still valid for this session
            
    return creds

def check_credentials_status(config_manager: ConfigManager) -> Tuple[bool, str]:
    """
    Check the status of credentials without attempting to refresh them.
    
    Args:
        config_manager: ConfigManager instance
    
    Returns:
        Tuple[bool, str]: (is_valid, status_message)
    """
    try:
        # Get the config directory path
        config_dir = Path(__file__).parent.parent / 'config'
        
        # Use different files based on test mode
        suffix = '_test' if config_manager.is_test_mode else ''
        token_path = config_dir / f'token{suffix}.pickle'
        credentials_path = config_dir / f'credentials{suffix}.json'
        
        # Check if credentials file exists
        if not credentials_path.exists():
            return False, f"Credentials file not found: {credentials_path}"
        
        # Check if token file exists
        if not token_path.exists():
            return False, "No authentication token found. Please authenticate."
        
        # Try to load and check token
        try:
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
            
            if not creds:
                return False, "Invalid token file (empty). Please re-authenticate."
            
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    return False, "Token has expired but can be refreshed. Please try again."
                else:
                    return False, "Token is invalid and cannot be refreshed. Please re-authenticate."
            
            return True, "Authentication token is valid."
            
        except Exception as e:
            return False, f"Error reading token file: {e}"
            
    except Exception as e:
        return False, f"Error checking credentials: {e}"

def clear_credentials(config_manager: ConfigManager) -> bool:
    """
    Clear stored credentials to force re-authentication.
    
    Args:
        config_manager: ConfigManager instance
    
    Returns:
        bool: True if credentials were cleared successfully, False otherwise
    """
    try:
        # Get the config directory path
        config_dir = Path(__file__).parent.parent / 'config'
        
        # Use different files based on test mode
        suffix = '_test' if config_manager.is_test_mode else ''
        token_path = config_dir / f'token{suffix}.pickle'
        
        if token_path.exists():
            token_path.unlink()
            logger.info(f"Cleared credentials for {'test' if config_manager.is_test_mode else 'production'} mode")
            return True
        else:
            logger.info("No credentials file found to clear")
            return True
            
    except Exception as e:
        logger.error(f"Failed to clear credentials: {e}")
        return False

def get_credentials_with_retry(config_manager: ConfigManager, max_retries: int = 1) -> Credentials:
    """
    Get credentials with automatic retry on token expiration.
    
    Args:
        config_manager: ConfigManager instance
        max_retries: Maximum number of retry attempts
    
    Returns:
        google.oauth2.credentials.Credentials: The credentials object for Google API access
        
    Raises:
        AuthenticationError: When all retry attempts fail
    """
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            return get_credentials(config_manager)
        except TokenExpiredError as e:
            last_error = e
            logger.warning(f"Token expired on attempt {attempt + 1}/{max_retries + 1}")
            if attempt < max_retries:
                # Don't clear credentials on TokenExpiredError since get_credentials() 
                # already handles token expiration and cleanup properly
                logger.info("Retrying authentication without clearing credentials")
                continue
        except Exception as e:
            last_error = e
            logger.error(f"Authentication error on attempt {attempt + 1}/{max_retries + 1}: {e}")
            if attempt < max_retries:
                continue
    
    # If we get here, all attempts failed
    raise AuthenticationError(f"Failed to authenticate after {max_retries + 1} attempts. Last error: {last_error}") 