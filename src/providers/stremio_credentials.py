# Copyright (C) 2025 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Secure storage for Stremio authentication credentials using GSettings.
"""

from gi.repository import Gio
from .. import shared


class StremioCredentials:
    """Handles secure storage of Stremio authentication credentials."""
    
    @staticmethod
    def save_auth_key(auth_key: str) -> None:
        """
        Save the authentication key securely.
        
        Args:
            auth_key (str): The authentication key to save
        """
        shared.schema.set_string('stremio-auth-key', auth_key)
    
    @staticmethod
    def get_auth_key() -> str:
        """
        Get the stored authentication key.
        
        Returns:
            str: The stored authentication key or empty string if not found
        """
        return shared.schema.get_string('stremio-auth-key')
    
    @staticmethod
    def save_user_data(user: dict) -> None:
        """
        Save user data securely.
        
        Args:
            user (dict): User data from Stremio API
        """
        if user:
            shared.schema.set_string('stremio-user-email', user.get('email', ''))
            shared.schema.set_string('stremio-user-id', user.get('_id', ''))
    
    @staticmethod
    def get_user_email() -> str:
        """
        Get the stored user email.
        
        Returns:
            str: The stored user email or empty string
        """
        return shared.schema.get_string('stremio-user-email')
    
    @staticmethod
    def get_user_id() -> str:
        """
        Get the stored user ID.
        
        Returns:
            str: The stored user ID or empty string
        """
        return shared.schema.get_string('stremio-user-id')
    
    @staticmethod
    def clear() -> None:
        """Clear all stored credentials."""
        shared.schema.set_string('stremio-auth-key', '')
        shared.schema.set_string('stremio-user-email', '')
        shared.schema.set_string('stremio-user-id', '')
    
    @staticmethod
    def is_logged_in() -> bool:
        """
        Check if user is logged in.
        
        Returns:
            bool: True if user has valid auth key
        """
        return len(shared.schema.get_string('stremio-auth-key')) > 0
