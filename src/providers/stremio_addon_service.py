# Copyright (C) 2025 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Stremio Addon Service for managing user's installed addons.
Based on the stremio-api-client AddonCollection implementation.
"""

import logging
import requests
from typing import List, Dict, Any, Optional
from .stremio_credentials import StremioCredentials


class StremioAddonService:
    """
    Service for managing Stremio addons.
    Handles fetching, enabling, disabling, and removing addons.
    """
    
    ENDPOINT = 'https://api.strem.io'
    
    def __init__(self):
        """Initialize the Stremio addon service."""
        self.endpoint = self.ENDPOINT
        self.auth_key = StremioCredentials.get_auth_key()
    
    def _request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Stremio API.
        
        Args:
            method (str): API method name
            params (dict): Parameters to send with the request
        
        Returns:
            dict: Response result from API
            
        Raises:
            Exception: If request fails or returns an error
        """
        url = f'{self.endpoint}/api/{method}'
        
        # Add auth key
        body = {'authKey': self.auth_key}
        body.update(params)
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, json=body, headers=headers, timeout=15)
            
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
    
    def get_addon_collection(self) -> List[Dict[str, Any]]:
        """
        Get the user's installed addon collection from Stremio API.
        
        Returns:
            list: List of addon descriptors
            
        Raises:
            Exception: If not logged in or request fails
        """
        if not self.auth_key:
            raise Exception('User must be logged in to fetch addons')
        
        logging.info('Fetching addon collection from Stremio API')
        
        params = {
            'update': True,
            'addFromURL': []
        }
        
        try:
            result = self._request('addonCollectionGet', params)
            
            if not isinstance(result.get('addons'), list):
                raise Exception('Invalid addon collection response')
            
            addons = result['addons']
            logging.info(f'Successfully fetched {len(addons)} addons')
            
            return addons
            
        except Exception as e:
            logging.error(f'Failed to get addon collection: {str(e)}')
            raise
    
    def set_addon_collection(self, addons: List[Dict[str, Any]]) -> None:
        """
        Update the user's addon collection on Stremio API.
        
        Args:
            addons (list): List of addon descriptors to save
            
        Raises:
            Exception: If not logged in or request fails
        """
        if not self.auth_key:
            raise Exception('User must be logged in to update addons')
        
        logging.info(f'Updating addon collection with {len(addons)} addons')
        
        params = {
            'addons': addons
        }
        
        try:
            self._request('addonCollectionSet', params)
            logging.info('Successfully updated addon collection')
            
        except Exception as e:
            logging.error(f'Failed to update addon collection: {str(e)}')
            raise
    
    def fetch_addon_manifest(self, transport_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the manifest from an addon's transport URL.
        
        Args:
            transport_url (str): The addon's transport URL
        
        Returns:
            dict: Addon manifest or None if fetch fails
        """
        try:
            # Clean up URL and append /manifest.json
            url = transport_url.rstrip('/')
            if not url.endswith('/manifest.json'):
                url = f'{url}/manifest.json'
            
            logging.debug(f'Fetching manifest from: {url}')
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logging.warning(f'Failed to fetch manifest from {url}: status {response.status_code}')
                return None
            
            manifest = response.json()
            return manifest
            
        except Exception as e:
            logging.warning(f'Error fetching manifest from {transport_url}: {str(e)}')
            return None
    
    def enable_addon(self, addons: List[Dict[str, Any]], addon_index: int) -> List[Dict[str, Any]]:
        """
        Enable an addon in the collection.
        
        Args:
            addons (list): Current addon collection
            addon_index (int): Index of addon to enable
        
        Returns:
            list: Updated addon collection
        """
        if 0 <= addon_index < len(addons):
            addons[addon_index]['enabled'] = True
            logging.info(f"Enabled addon: {addons[addon_index].get('manifest', {}).get('name', 'Unknown')}")
        return addons
    
    def disable_addon(self, addons: List[Dict[str, Any]], addon_index: int) -> List[Dict[str, Any]]:
        """
        Disable an addon in the collection.
        
        Args:
            addons (list): Current addon collection
            addon_index (int): Index of addon to disable
        
        Returns:
            list: Updated addon collection
        """
        if 0 <= addon_index < len(addons):
            addons[addon_index]['enabled'] = False
            logging.info(f"Disabled addon: {addons[addon_index].get('manifest', {}).get('name', 'Unknown')}")
        return addons
    
    def remove_addon(self, addons: List[Dict[str, Any]], addon_index: int) -> List[Dict[str, Any]]:
        """
        Remove an addon from the collection.
        
        Args:
            addons (list): Current addon collection
            addon_index (int): Index of addon to remove
        
        Returns:
            list: Updated addon collection
        """
        if 0 <= addon_index < len(addons):
            removed = addons.pop(addon_index)
            logging.info(f"Removed addon: {removed.get('manifest', {}).get('name', 'Unknown')}")
        return addons
    
    @staticmethod
    def is_logged_in() -> bool:
        """
        Check if user is logged in and can access addons.
        
        Returns:
            bool: True if user is logged in
        """
        return StremioCredentials.is_logged_in()
