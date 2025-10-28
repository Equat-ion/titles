# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import logging
import os
from gettext import gettext as _
from gettext import pgettext as C_
from pathlib import Path

from gi.repository import Adw, Gio, GLib, GObject, Gtk, Gdk

from . import shared  # type: ignore
from .background_queue import ActivityType, BackgroundActivity, BackgroundQueue
from .models.language_model import LanguageModel
from .providers.local_provider import LocalProvider as local
from .providers.stremio_addon_service import StremioAddonService
from .providers.stremio_auth import StremioAuthService


@Gtk.Template(resource_path=shared.PREFIX + '/ui/preferences.ui')
class PreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = 'PreferencesDialog'

    _language_comborow = Gtk.Template.Child()
    _language_model = Gtk.Template.Child()
    _update_freq_comborow = Gtk.Template.Child()
    _offline_group = Gtk.Template.Child()
    _offline_switch = Gtk.Template.Child()
    _housekeeping_group = Gtk.Template.Child()
    _exit_cache_switch = Gtk.Template.Child()
    _cache_row = Gtk.Template.Child()
    _data_row = Gtk.Template.Child()
    
    # Addon-related widgets
    _addons_group = Gtk.Template.Child()
    _login_prompt_row = Gtk.Template.Child()
    _addons_loading_row = Gtk.Template.Child()
    _addons_error_row = Gtk.Template.Child()
    _addons_empty_row = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.language_change_handler = self._language_comborow.connect(
            'notify::selected', self._on_language_changed)
        self._update_freq_comborow.connect(
            'notify::selected', self._on_freq_changed)

        shared.schema.bind('offline-mode', self._offline_switch,
                           'active', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('exit-remove-cache', self._exit_cache_switch,
                           'active', Gio.SettingsBindFlags.DEFAULT)

        self._offline_switch.connect('notify::active', lambda pspec, user_data: logging.debug(
            f'Toggled offline mode: {self._offline_switch.get_active()}'))
        self._exit_cache_switch.connect('notify::active', lambda pspec, user_data: logging.debug(
            f'Toggled clear cache on exit: {self._exit_cache_switch.get_active()}'))
        
        # Initialize addon service
        self.addon_service = StremioAddonService()
        self.auth_service = StremioAuthService()
        self.current_addons = []
        self.addon_rows = []

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for the "map" signal.
        Populates dropdowns and checks if an automatic update of the content is due.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        self._setup_languages()

        # Update frequency dropdown
        match shared.schema.get_string('update-freq'):
            case 'never':
                self._update_freq_comborow.set_selected(0)
            case 'day':
                self._update_freq_comborow.set_selected(1)
            case 'week':
                self._update_freq_comborow.set_selected(2)
            case 'month':
                self._update_freq_comborow.set_selected(3)

        # Update occupied space
        self._update_occupied_space()
        
        # Load addons
        self._load_addons()

    def _setup_languages(self):
        self._language_comborow.handler_block(self.language_change_handler)

        languages = local.get_all_languages()
        if len(languages) > 6:
            languages.pop(len(languages)-6)    # remove 'no language'
        for language in languages:
            self._language_model.append(language.name)

        self._language_comborow.set_selected(0)  # Default to first language
        self._language_comborow.handler_unblock(self.language_change_handler)

    def _on_language_changed(self, pspec: GObject.ParamSpec, user_data: object | None) -> None:
        """
        Callback for "notify::selected" signal.
        Updates the preferred language in GSettings.

        Args:
            pspec (GObject.ParamSpec): The GParamSpec of the property which changed
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        language = self._get_selected_language(
            self._language_comborow.get_selected_item().get_string())
        logging.debug(f'Changed language to {language}')

    def _on_freq_changed(self, pspec, user_data: object | None) -> None:
        """
        Callback for "notify::selected" signal.
        Updates the frequency for content updates in GSettings.

        Args:
            pspec (GObject.ParamSpec): The GParamSpec of the property which changed
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        freq = self._update_freq_comborow.get_selected()
        match freq:
            case 0:
                shared.schema.set_string('update-freq', 'never')
                logging.debug(f'Changed update frequency to never')
            case 1:
                shared.schema.set_string('update-freq', 'day')
                logging.debug(f'Changed update frequency to day')
            case 2:
                shared.schema.set_string('update-freq', 'week')
                logging.debug(f'Changed update frequency to week')
            case 3:
                shared.schema.set_string('update-freq', 'month')
                logging.debug(f'Changed update frequency to month')

    def _get_selected_language_index(self, iso_name: str) -> int:
        """
        Loops all available languages and returns the index of the one with the specified iso name. If a result is not found, it returns the index for English (37).

        Args:
            iso_name: a language's iso name

        Return:
            int with the index
        """

        for idx, language in enumerate(local.get_all_languages()):
            if language.iso_name == iso_name:
                return idx
        return 37

    def _get_selected_language(self, name: str) -> str:
        """
        Loops all available languages and returns the iso name of the one with the specified name. If a result is not found, it returns the iso name for English (en).

        Args:
            name: a language's name

        Return:
            str with the iso name
        """

        for language in local.get_all_languages():
            if language.name == name:
                return language.iso_name
        return 'en'

    @Gtk.Template.Callback('_on_clear_cache_activate')
    def _on_clear_cache_activate(self, user_data: object | None) -> None:
        """
        Callback for "activated" signal.
        Shows a confirmation dialog to the user.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        logging.debug('Show cache clear dialog')
        builder = Gtk.Builder.new_from_resource(
            shared.PREFIX + '/ui/dialogs/message_dialogs.ui')
        _clear_cache_dialog = builder.get_object('_clear_cache_dialog')
        _clear_cache_dialog.choose(self,
            None, self._on_cache_message_dialog_choose, None)

    def _on_cache_message_dialog_choose(self,
                                        source: GObject.Object | None,
                                        result: Gio.AsyncResult,
                                        user_data: object | None) -> None:
        """
        Callback for the message dialog.
        Finishes the async operation and retrieves the user response. If the later is positive, adds a background activity to delete the cache.

        Args:
            source (Gtk.Widget): object that started the async operation
            result (Gio.AsyncResult): a Gio.AsyncResult
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        result = Adw.AlertDialog.choose_finish(source, result)
        if result == 'cache_cancel':
            logging.debug('Cache clear dialog: cancel, aborting')
            return

        logging.debug('Cache clear dialog: sel, aborting')
        BackgroundQueue.add(
            activity=BackgroundActivity(
                activity_type=ActivityType.REMOVE,
                title=C_('Background activity title', 'Clear cache'),
                task_function=self._clear_cache),
            on_done=self._on_cache_clear_done)

    def _clear_cache(self, activity: BackgroundActivity) -> None:
        """
        Clears the cache.

        Args:
            activity (BackgroundActivity): the calling activity

        Returns:
            None
        """

        logging.info('Deleting cache')
        files = glob.glob('*.jpg', root_dir=shared.cache_dir)
        for file in files:
            os.remove(shared.cache_dir / file)
            logging.debug(f'Deleted {shared.cache_dir / file}')

    def _on_cache_clear_done(self,
                             source: GObject.Object,
                             result: Gio.AsyncResult,
                             cancellable: Gio.Cancellable,
                             activity: BackgroundActivity):
        self._update_occupied_space()
        activity.end()

    @Gtk.Template.Callback('_on_clear_activate')
    def _on_clear_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for "activated" signal.
        Shows a confirmation dialog to the user.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        logging.debug('Show data clear dialog')
        builder = Gtk.Builder.new_from_resource(
            shared.PREFIX + '/ui/dialogs/message_dialogs.ui')
        _clear_data_dialog = builder.get_object('_clear_data_dialog')
        _movies_row = builder.get_object('_movies_row')
        _series_row = builder.get_object('_series_row')
        self._movies_checkbtn = builder.get_object('_movies_checkbtn')
        self._series_checkbtn = builder.get_object('_series_checkbtn')

        # TRANSLATORS: {number} is the number of titles
        _movies_row.set_subtitle(_('{number} Titles').format(
            number=len(local.get_all_movies())))
        _series_row.set_subtitle(_('{number} Titles').format(
            number=len(local.get_all_series())))

        _clear_data_dialog.choose(self,
            None, self._on_data_message_dialog_choose, None)

    def _on_data_message_dialog_choose(self,
                                       source: GObject.Object | None,
                                       result: Gio.AsyncResult,
                                       user_data: object | None) -> None:
        """
        Callback for the message dialog.
        Finishes the async operation and retrieves the user response. If the later is positive, adds background activities to delete the selected data.

        Args:
            source (Gtk.Widget): object that started the async operation
            result (Gio.AsyncResult): a Gio.AsyncResultresult = Adw.AlertDialog.choose_finish(source, result)
        if result == 'data_cancel':
            return

            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        result = Adw.AlertDialog.choose_finish(source, result)
        if result == 'data_cancel':
            logging.debug('Data clear dialog: cancel, aborting')
            return

        # Movies
        if self._movies_checkbtn.get_active():
            logging.debug('Data clear dialog: movies selected')
            BackgroundQueue.add(
                activity=BackgroundActivity(
                    activity_type=ActivityType.REMOVE,
                    title=C_('Background activity title', 'Delete all movies'),
                    task_function=self._clear_movies),
                on_done=self._on_data_clear_done)

        # TV Series
        if self._series_checkbtn.get_active():
            logging.debug('Data clear dialog: tv series selected')
            BackgroundQueue.add(
                activity=BackgroundActivity(
                    activity_type=ActivityType.REMOVE,
                    title=C_('Background activity title',
                             'Delete all TV Series'),
                    task_function=self._clear_series),
                on_done=self._on_data_clear_done)

    def _clear_movies(self, activity: BackgroundActivity) -> None:
        """
        Clears all movies.

        Args:
            activity (BackgroundActivity): the calling activity

        Returns:
            None
        """

        logging.info('Deleting all movies')
        for movie in local.get_all_movies():    # type: ignore
            local.delete_movie(movie.id)
            logging.debug(f'Deleted ({movie.id}) {movie.title}')

    def _on_data_clear_done(self,
                            source: GObject.Object,
                            result: Gio.AsyncResult,
                            cancellable: Gio.Cancellable,
                            activity: BackgroundActivity):
        """Callback to complete async activity"""

        self._update_occupied_space()
        self.get_parent().activate_action('win.refresh', None)
        activity.end()

    def _clear_series(self, activity: BackgroundActivity) -> None:
        """
        Clears all TV series.

        Args:
            activity (BackgroundActivity): the calling activity

        Returns:
            None
        """

        logging.info('Deleting all TV series')
        for serie in local.get_all_series():    # type: ignore
            local.delete_series(serie.id)
            logging.debug(f'Deleted ({serie.id}) {serie.title}')

    def _calculate_space(self, directory: Path) -> float:
        """
        Given a directory, calculates the total space occupied on disk.

        Args:
            directory (Path): the directory to measure

        Returns:
            float with space occupied in MegaBytes (MB)
        """

        return sum(file.stat().st_size for file in directory.rglob('*'))/1024.0/1024.0

    def _update_occupied_space(self) -> None:
        """
        After calculating space occupied by cache and data, updates the ui labels to reflect the values.

        Args:
            None

        Returns:
            None
        """

        cache_space = self._calculate_space(shared.cache_dir)
        data_space = self._calculate_space(shared.data_dir)

        self._housekeeping_group.set_description(  # TRANSLATORS: {total_space:.2f} is the total occupied space
            _('Ticket Booth is currently using {total_space:.2f} MB. Use the options below to free some space.').format(total_space=cache_space+data_space))

        # TRANSLATORS: {space:.2f} is the occupied space
        self._cache_row.set_subtitle(
            _('{space:.2f} MB occupied').format(space=cache_space))
        self._data_row.set_subtitle(
            _('{space:.2f} MB occupied').format(space=data_space))

    # ==================== Addon Management Methods ====================
    
    def _load_addons(self) -> None:
        """
        Load addons from Stremio API.
        Shows appropriate UI state based on login status and fetch result.
        """
        # Check if user is logged in
        if not self.addon_service.is_logged_in():
            self._show_addon_login_prompt()
            return
        
        # Show loading state
        self._show_addon_loading()
        
        # Fetch addons in background
        def fetch_task(activity: BackgroundActivity) -> None:
            try:
                self.current_addons = self.addon_service.get_addon_collection()
            except Exception as e:
                logging.error(f'Failed to fetch addons: {str(e)}')
                raise
        
        BackgroundQueue.add(
            activity=BackgroundActivity(
                activity_type=ActivityType.UPDATE,
                title=_('Loading Addons'),
                task_function=fetch_task),
            on_done=self._on_addons_loaded)
    
    def _on_addons_loaded(self,
                          source: GObject.Object,
                          result: Gio.AsyncResult,
                          cancellable: Gio.Cancellable,
                          activity: BackgroundActivity) -> None:
        """Callback when addons are loaded."""
        try:
            activity.end()
            
            if len(self.current_addons) == 0:
                self._show_addon_empty_state()
            else:
                self._display_addons()
                
        except Exception as e:
            logging.error(f'Error in addon loading callback: {str(e)}')
            self._show_addon_error()
            activity.end()
    
    def _show_addon_login_prompt(self) -> None:
        """Show the login prompt for addons."""
        self._login_prompt_row.set_visible(True)
        self._addons_loading_row.set_visible(False)
        self._addons_error_row.set_visible(False)
        self._addons_empty_row.set_visible(False)
    
    def _show_addon_loading(self) -> None:
        """Show loading state for addons."""
        self._login_prompt_row.set_visible(False)
        self._addons_loading_row.set_visible(True)
        self._addons_error_row.set_visible(False)
        self._addons_empty_row.set_visible(False)
    
    def _show_addon_error(self) -> None:
        """Show error state for addons."""
        self._login_prompt_row.set_visible(False)
        self._addons_loading_row.set_visible(False)
        self._addons_error_row.set_visible(True)
        self._addons_empty_row.set_visible(False)
    
    def _show_addon_empty_state(self) -> None:
        """Show empty state when no addons are installed."""
        self._login_prompt_row.set_visible(False)
        self._addons_loading_row.set_visible(False)
        self._addons_error_row.set_visible(False)
        self._addons_empty_row.set_visible(True)
    
    def _display_addons(self) -> None:
        """Display the list of addons as ExpanderRows."""
        # Clear existing rows
        self._clear_addon_rows()
        
        # Hide state rows
        self._login_prompt_row.set_visible(False)
        self._addons_loading_row.set_visible(False)
        self._addons_error_row.set_visible(False)
        self._addons_empty_row.set_visible(False)
        
        # Create ExpanderRow for each addon
        for index, addon in enumerate(self.current_addons):
            manifest = addon.get('manifest', {})
            transport_url = addon.get('transportUrl', '')
            is_enabled = addon.get('enabled', True)
            
            # Get addon details from manifest
            addon_name = manifest.get('name', 'Unknown Addon')
            addon_id = manifest.get('id', 'unknown')
            addon_version = manifest.get('version', 'N/A')
            addon_description = manifest.get('description', 'No description available')
            
            # Create expander row
            expander = Adw.ExpanderRow()
            expander.set_title(addon_name)
            
            # Build subtitle
            expander.set_subtitle(f'v{addon_version}')
            
            # Enable/Disable switch as a suffix (outside the expander)
            enable_switch = Gtk.Switch()
            enable_switch.set_active(is_enabled)
            enable_switch.set_valign(Gtk.Align.CENTER)
            enable_switch.connect('notify::active', self._on_addon_toggle, index)
            expander.add_suffix(enable_switch)
            
            # Addon details
            id_row = Adw.ActionRow()
            id_row.set_title(_('ID'))
            id_row.set_subtitle(addon_id)
            id_row.add_css_class('property')
            expander.add_row(id_row)
            
            version_row = Adw.ActionRow()
            version_row.set_title(_('Version'))
            version_row.set_subtitle(addon_version)
            version_row.add_css_class('property')
            expander.add_row(version_row)
            
            description_row = Adw.ActionRow()
            description_row.set_title(_('Description'))
            description_row.set_subtitle(addon_description)
            description_row.set_subtitle_lines(3)
            description_row.add_css_class('property')
            expander.add_row(description_row)
            
            url_row = Adw.ActionRow()
            url_row.set_title(_('URL'))
            url_row.set_subtitle(transport_url)
            url_row.add_css_class('property')
            expander.add_row(url_row)
            
            # Configure button (if addon supports configuration)
            if manifest.get('behaviorHints', {}).get('configurable', False):
                configure_row = Adw.ActionRow()
                configure_row.set_title(_('Configure Addon'))
                configure_row.set_activatable(True)
                
                configure_btn = Gtk.Button()
                configure_btn.set_label(_('Configure'))
                configure_btn.set_valign(Gtk.Align.CENTER)
                configure_btn.connect('clicked', self._on_addon_configure, index, transport_url)
                configure_row.add_suffix(configure_btn)
                
                expander.add_row(configure_row)
            
            # Remove button
            remove_row = Adw.ActionRow()
            remove_row.set_title(_('Remove Addon'))
            remove_row.set_activatable(True)
            
            remove_btn = Gtk.Button()
            remove_btn.set_label(_('Remove'))
            remove_btn.set_valign(Gtk.Align.CENTER)
            remove_btn.add_css_class('destructive-action')
            remove_btn.connect('clicked', self._on_addon_remove, index)
            remove_row.add_suffix(remove_btn)
            
            expander.add_row(remove_row)
            
            # Add to main group
            self._addons_group.add(expander)
            self.addon_rows.append(expander)
    
    def _clear_addon_rows(self) -> None:
        """Clear all addon rows from the list."""
        for row in self.addon_rows:
            self._addons_group.remove(row)
        self.addon_rows.clear()
    
    def _on_addon_toggle(self, switch: Gtk.Switch, pspec: GObject.ParamSpec, index: int) -> None:
        """Handle addon enable/disable toggle."""
        is_enabled = switch.get_active()
        
        logging.info(f'Toggling addon {index} to {"enabled" if is_enabled else "disabled"}')
        
        if is_enabled:
            self.current_addons = self.addon_service.enable_addon(self.current_addons, index)
        else:
            self.current_addons = self.addon_service.disable_addon(self.current_addons, index)
        
        # Save changes
        self._save_addon_changes()
    
    def _on_addon_configure(self, button: Gtk.Button, index: int, transport_url: str) -> None:
        """Handle addon configuration button click."""
        # Open addon configuration page in browser
        configure_url = f'{transport_url.rstrip("/")}/configure'
        logging.info(f'Opening addon configuration: {configure_url}')
        
        Gtk.show_uri(self, configure_url, Gdk.CURRENT_TIME)
    
    def _on_addon_remove(self, button: Gtk.Button, index: int) -> None:
        """Handle addon removal button click."""
        addon_name = self.current_addons[index].get('manifest', {}).get('name', 'this addon')
        
        # Show confirmation dialog
        dialog = Adw.AlertDialog.new(
            _('Remove Addon?'),
            _('Are you sure you want to remove "{}"? This action cannot be undone.').format(addon_name)
        )
        
        dialog.add_response('cancel', _('Cancel'))
        dialog.add_response('remove', _('Remove'))
        dialog.set_response_appearance('remove', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response('cancel')
        dialog.set_close_response('cancel')
        
        dialog.connect('response', self._on_remove_addon_response, index)
        dialog.present(self)
    
    def _on_remove_addon_response(self, dialog: Adw.AlertDialog, response: str, index: int) -> None:
        """Handle addon removal confirmation response."""
        if response == 'remove':
            logging.info(f'Removing addon {index}')
            self.current_addons = self.addon_service.remove_addon(self.current_addons, index)
            
            # Save changes and refresh display
            self._save_addon_changes()
            self._display_addons()
    
    def _save_addon_changes(self) -> None:
        """Save addon collection changes to Stremio API."""
        def save_task(activity: BackgroundActivity) -> None:
            try:
                self.addon_service.set_addon_collection(self.current_addons)
            except Exception as e:
                logging.error(f'Failed to save addon changes: {str(e)}')
                raise
        
        BackgroundQueue.add(
            activity=BackgroundActivity(
                activity_type=ActivityType.UPDATE,
                title=_('Saving Changes'),
                task_function=save_task),
            on_done=self._on_addon_changes_saved)
    
    def _on_addon_changes_saved(self,
                                source: GObject.Object,
                                result: Gio.AsyncResult,
                                cancellable: Gio.Cancellable,
                                activity: BackgroundActivity) -> None:
        """Callback when addon changes are saved."""
        activity.end()
        logging.info('Addon changes saved successfully')
    
    @Gtk.Template.Callback('_on_addon_login_clicked')
    def _on_addon_login_clicked(self, user_data: object | None) -> None:
        """Handle login button click in addons tab."""
        logging.debug('Addon login button clicked')
        
        # Import and show login dialog
        try:
            from .dialogs.stremio_login_dialog import StremioLoginDialog
            
            logging.debug('Creating StremioLoginDialog')
            login_dialog = StremioLoginDialog()
            
            # Get the parent window from the preferences dialog
            parent_window = self.get_root()
            logging.debug(f'Parent window: {parent_window}')
            
            if parent_window:
                logging.debug('Presenting dialog with parent window')
                login_dialog.present(parent_window)
            else:
                logging.debug('Presenting dialog with self as parent')
                login_dialog.present(self)
            
            # Connect to login success signal
            logging.debug('Connecting to login-success signal')
            login_dialog.connect('login-success', self._on_login_success)
            logging.debug('Login dialog presented successfully')
                
        except ImportError as e:
            logging.error(f'StremioLoginDialog import failed: {e}')
            # Fallback: just reload addons (in case user logged in elsewhere)
            self._load_addons()
        except Exception as e:
            logging.error(f'Failed to show login dialog: {e}', exc_info=True)
    
    def _on_login_success(self, dialog, user_data=None) -> None:
        """Handle successful login from dialog."""
        logging.info('Login successful, reloading addons')
        self._load_addons()
    
    @Gtk.Template.Callback('_on_addon_retry_clicked')
    def _on_addon_retry_clicked(self, user_data: object | None) -> None:
        """Handle retry button click in error state."""
        logging.debug('Addon retry button clicked')
        self._load_addons()


