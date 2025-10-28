# Copyright (C) 2025 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Account button widget for Stremio authentication.
Shows user avatar and provides login/logout functionality.
"""

import logging
from gettext import gettext as _
from gi.repository import Adw, Gtk

from .. import shared
from ..providers.stremio_auth import StremioAuthService
from ..dialogs.stremio_login_dialog import StremioLoginDialog


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/account_button.ui')
class AccountButton(Adw.Bin):
    """
    Account button widget for header bar.
    
    Shows user avatar when logged in, provides login/logout functionality.
    """
    
    __gtype_name__ = 'AccountButton'
    
    _menu_button = Gtk.Template.Child()
    _avatar = Gtk.Template.Child()
    _popover_avatar = Gtk.Template.Child()
    _user_email = Gtk.Template.Child()
    _logged_in_box = Gtk.Template.Child()
    _logged_out_box = Gtk.Template.Child()
    _login_button = Gtk.Template.Child()
    _logout_button = Gtk.Template.Child()
    
    def __init__(self):
        """Initialize the account button."""
        super().__init__()
        self.auth_service = StremioAuthService()
        self._update_ui()
    
    def _update_ui(self):
        """Update UI based on login state."""
        is_logged_in = self.auth_service.is_logged_in()
        
        self._logged_in_box.set_visible(is_logged_in)
        self._logged_out_box.set_visible(not is_logged_in)
        
        if is_logged_in:
            email = self.auth_service.get_stored_email()
            self._user_email.set_label(email)
            
            # Set avatar text - try to get initials from email
            initials = self._get_initials_from_email(email)
            self._avatar.set_text(email)
            self._avatar.set_show_initials(True)
            self._popover_avatar.set_text(email)
            self._popover_avatar.set_show_initials(True)
            
            logging.debug(f'Updated UI for logged in user: {email}')
        else:
            # Show a generic account icon when logged out
            self._avatar.set_text("")
            self._avatar.set_show_initials(False)
            self._avatar.set_icon_name("avatar-default-symbolic")
            logging.debug('Updated UI for logged out state')
    
    def _get_initials_from_email(self, email: str) -> str:
        """
        Get initials from email address.
        
        If email has a name part (before @), use first 2 characters.
        Otherwise use first character of email.
        
        Args:
            email (str): Email address
            
        Returns:
            str: Initials (1-2 characters)
        """
        if not email:
            return "?"
        
        # Get part before @
        local_part = email.split('@')[0] if '@' in email else email
        
        # Try to split by common separators
        parts = local_part.replace('.', ' ').replace('_', ' ').split()
        
        if len(parts) >= 2:
            # Use first letter of first two parts
            return (parts[0][0] + parts[1][0]).upper()
        elif len(parts) == 1 and len(parts[0]) >= 2:
            # Use first two letters
            return parts[0][:2].upper()
        elif len(parts) == 1:
            # Use first letter capitalized
            return parts[0][0].upper()
        else:
            # Fallback
            return email[0].upper()
    
    @Gtk.Template.Callback()
    def _on_login_clicked(self, button):
        """
        Callback for login button clicked.
        Opens the login dialog.
        """
        logging.info('Opening login dialog')
        
        dialog = StremioLoginDialog()
        dialog.connect('login-success', self._on_login_success)
        
        # Get the parent window
        parent = self.get_root()
        if parent:
            dialog.present(parent)
    
    def _on_login_success(self, dialog):
        """
        Callback for successful login.
        Updates the UI to show logged in state.
        
        Args:
            dialog: The login dialog
        """
        logging.info('Login successful, updating UI')
        self._update_ui()
        
        # Show a toast notification in the main window
        parent = self.get_root()
        if parent and hasattr(parent, 'show_toast'):
            parent.show_toast(_("Successfully signed in to Stremio!"))
    
    @Gtk.Template.Callback()
    def _on_logout_clicked(self, button):
        """
        Callback for logout button clicked.
        Logs out the user and updates UI.
        """
        logging.info('Logging out user')
        
        try:
            self.auth_service.logout()
            self._update_ui()
            
            # Show toast notification
            parent = self.get_root()
            if parent and hasattr(parent, 'show_toast'):
                parent.show_toast(_("Signed out from Stremio"))
            
            logging.info('Logout successful')
            
        except Exception as e:
            logging.error(f'Logout error: {str(e)}')
            # Still update UI since credentials are cleared locally
            self._update_ui()
    
    def refresh(self):
        """Refresh the account button state."""
        self._update_ui()
