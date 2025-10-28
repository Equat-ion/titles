# Copyright (C) 2025 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Stremio API authentication service using HTTP requests.
Based on the stremio-api-client implementation.
"""

import logging
import requests
from typing import Optional, Dict, Any
from .stremio_credentials import StremioCredentials


class StremioAuthService:
    """
    Service for authenticating with Stremio API.
    Implements the same login flow as the official stremio-api-client.
    """
    
    ENDPOINT = 'https://api.strem.io'
    
    def __init__(self):
        """Initialize the Stremio authentication service."""
        self.endpoint = self.ENDPOINT
        self.auth_key = StremioCredentials.get_auth_key()
    
    def _request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Stremio API.
        
        Args:
            method (str): API method name (e.g., 'login', 'logout')
            params (dict): Parameters to send with the request
        
        Returns:
            dict: Response result from API
            
        Raises:
            Exception: If request fails or returns an error
        """
        url = f'{self.endpoint}/api/{method}'
        
        # Add auth key if available
        body = {'authKey': self.auth_key} if self.auth_key else {}
        body.update(params)
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, json=body, headers=headers, timeout=10)
            
            if response.status_code != 200:
                raise Exception(f'Request failed with status code {response.status_code}')
            
            data = response.json()
            
            if 'error' in data:
                error_msg = data['error']
                if isinstance(error_msg, dict):
                    error_msg = error_msg.get('message', str(error_msg))
                raise Exception(error_msg)
            
            if 'result' not in data:
                raise Exception('Response has no result')
            
            return data['result']
            
        except requests.exceptions.Timeout:
            raise Exception('Request timed out')
        except requests.exceptions.ConnectionError:
            raise Exception('Connection error. Please check your internet connection.')
        except requests.exceptions.RequestException as e:
            raise Exception(f'Request failed: {str(e)}')
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login to Stremio with email and password.
        
        Args:
            email (str): User email
            password (str): User password
        
        Returns:
            dict: User data from API
            
        Raises:
            Exception: If login fails
        """
        logging.info(f'Attempting to login with email: {email}')
        
        params = {
            'email': email,
            'password': password
        }
        
        try:
            result = self._request('login', params)
            
            # Store auth key and user data
            if 'authKey' in result:
                self.auth_key = result['authKey']
                StremioCredentials.save_auth_key(self.auth_key)
                logging.info('Auth key saved successfully')
            
            if 'user' in result:
                StremioCredentials.save_user_data(result['user'])
                logging.info(f"User logged in: {result['user'].get('email', 'unknown')}")
            
            return result
            
        except Exception as e:
            logging.error(f'Login failed: {str(e)}')
            raise
    
    def logout(self) -> None:
        """
        Logout from Stremio and clear stored credentials.
        
        Raises:
            Exception: If logout API call fails (credentials are still cleared)
        """
        logging.info('Attempting to logout')
        
        try:
            # Try to call logout API
            if self.auth_key:
                self._request('logout', {})
                logging.info('Logout API call successful')
        except Exception as e:
            logging.warning(f'Logout API call failed: {str(e)}')
            # Continue to clear local credentials even if API call fails
        finally:
            # Always clear local credentials
            self.auth_key = None
            StremioCredentials.clear()
            logging.info('Local credentials cleared')
    
    def get_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current user data from API.
        
        Returns:
            dict: User data or None if not logged in
            
        Raises:
            Exception: If request fails
        """
        if not self.auth_key:
            return None
        
        try:
            result = self._request('getUser', {})
            
            # Update stored user data
            if 'user' in result:
                StremioCredentials.save_user_data(result['user'])
            
            return result.get('user')
            
        except Exception as e:
            logging.error(f'Failed to get user: {str(e)}')
            raise
    
    @staticmethod
    def is_logged_in() -> bool:
        """
        Check if user is currently logged in.
        
        Returns:
            bool: True if user has valid credentials
        """
        return StremioCredentials.is_logged_in()
    
    @staticmethod
    def get_stored_email() -> str:
        """
        Get the stored user email.
        
        Returns:
            str: User email or empty string
        """
        return StremioCredentials.get_user_email()
