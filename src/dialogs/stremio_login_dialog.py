# Copyright (C) 2025 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Stremio login dialog for authenticating users.
"""

import logging
from gettext import gettext as _
from gi.repository import Adw, Gio, GLib, GObject, Gtk

from .. import shared
from ..providers.stremio_auth import StremioAuthService


@Gtk.Template(resource_path=shared.PREFIX + '/ui/dialogs/stremio_login.ui')
class StremioLoginDialog(Adw.Dialog):
    """
    Dialog for logging into Stremio account.
    
    Signals:
        login-success: Emitted when login is successful
    """
    
    __gtype_name__ = 'StremioLoginDialog'
    __gsignals__ = {
        'login-success': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }
    
    _email_entry = Gtk.Template.Child()
    _password_entry = Gtk.Template.Child()
    _login_button = Gtk.Template.Child()
    _cancel_button = Gtk.Template.Child()
    _toast_overlay = Gtk.Template.Child()
    
    def __init__(self):
        """Initialize the login dialog."""
        super().__init__()
        self.auth_service = StremioAuthService()
        self._is_loading = False
    
    @Gtk.Template.Callback()
    def _on_entry_changed(self, *args):
        """
        Callback for entry text changed.
        Enables login button only when both fields have content.
        """
        email = self._email_entry.get_text().strip()
        password = self._password_entry.get_text()
        
        # Basic email validation
        has_email = len(email) > 0 and '@' in email
        has_password = len(password) > 0
        
        self._login_button.set_sensitive(has_email and has_password and not self._is_loading)
    
    @Gtk.Template.Callback()
    def _on_login_clicked(self, *args):
        """
        Callback for login button clicked.
        Attempts to login with provided credentials.
        """
        if self._is_loading:
            return
        
        email = self._email_entry.get_text().strip()
        password = self._password_entry.get_text()
        
        if not email or not password:
            return
        
        # Disable UI during login
        self._is_loading = True
        self._login_button.set_sensitive(False)
        self._email_entry.set_sensitive(False)
        self._password_entry.set_sensitive(False)
        self._cancel_button.set_sensitive(False)
        
        # Show loading state
        self._login_button.set_label(_("Signing In..."))
        
        # Perform login in background using GLib threading
        import threading
        
        def do_login_thread():
            try:
                result = self.auth_service.login(email, password)
                success = True
                data = result
            except Exception as e:
                success = False
                data = str(e)
            
            # Schedule UI update on main thread
            GLib.idle_add(self._on_login_complete, success, data)
        
        # Start background thread
        thread = threading.Thread(target=do_login_thread, daemon=True)
        thread.start()
    
    def _on_login_complete(self, success, data):
        """Handle login completion on main thread."""
        # Re-enable UI
        self._is_loading = False
        self._login_button.set_label(_("Sign In"))
        self._email_entry.set_sensitive(True)
        self._password_entry.set_sensitive(True)
        self._cancel_button.set_sensitive(True)
        self._on_entry_changed()
        
        if success:
            logging.info('Login successful')
            self._show_toast(_("Successfully signed in!"), 'success')
            
            # Wait a moment before closing so user sees success message
            GLib.timeout_add(500, self._on_success)
        else:
            logging.error(f'Login failed: {data}')
            error_message = self._format_error_message(data)
            self._show_toast(error_message, 'error')
            
            # Clear password on error
            self._password_entry.set_text('')
        
        return False  # Don't repeat
    
    def _format_error_message(self, error: str) -> str:
        """
        Format error message to be user-friendly.
        
        Args:
            error (str): Raw error message
            
        Returns:
            str: Formatted error message
        """
        error_lower = error.lower()
        
        if 'credentials' in error_lower or 'password' in error_lower or 'email' in error_lower:
            return _("Invalid email or password")
        elif 'connection' in error_lower or 'network' in error_lower:
            return _("Connection error. Please check your internet connection.")
        elif 'timeout' in error_lower:
            return _("Request timed out. Please try again.")
        else:
            return _("Login failed: {error}").format(error=error)
    
    def _show_toast(self, message: str, toast_type: str = 'normal'):
        """
        Show a toast notification.
        
        Args:
            message (str): Message to display
            toast_type (str): Type of toast ('success', 'error', 'normal')
        """
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        
        self._toast_overlay.add_toast(toast)
    
    def _on_success(self):
        """Handle successful login."""
        self.emit('login-success')
        self.close()
        return False  # Don't repeat timeout
    
    @Gtk.Template.Callback()
    def _on_cancel_clicked(self, *args):
        """Callback for cancel button clicked."""
        self.close()
