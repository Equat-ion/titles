# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from datetime import datetime, timedelta
from gettext import gettext as _
from gettext import pgettext as C_
from gettext import ngettext as N_

from gi.repository import Adw, Gio, GObject, Gtk

from .. import shared  # type: ignore
from ..background_queue import (ActivityType, BackgroundActivity,
                                BackgroundQueue)
from ..models.movie_model import MovieModel
from ..models.series_model import SeriesModel
from ..providers.local_provider import LocalProvider as local
from ..views.content_view import ContentView
from ..widgets.theme_switcher import ThemeSwitcher


@Gtk.Template(resource_path=shared.PREFIX + '/ui/views/main_view.ui')
class MainView(Adw.Bin):
    """
    This class represents the main view of the app.

    Properties:
        None

    Methods:
        refresh(): Causes the window to update its contents

    Signals:
        None
    """

    __gtype_name__ = 'MainView'

    _tab_stack = Gtk.Template.Child()
    _show_search_btn = Gtk.Template.Child()
    _menu_btn = Gtk.Template.Child()
    _banner = Gtk.Template.Child()
    _background_indicator = Gtk.Template.Child()
    _search_bar = Gtk.Template.Child()
    _search_mode = Gtk.Template.Child()
    _search_entry = Gtk.Template.Child()

    _needs_refresh = ''

    def __init__(self, window):
        super().__init__()
        self.app = window.app

        self._tab_stack.add_titled_with_icon(ContentView(movie_view=True),
                                             'movies',
                                             C_('Category', 'Movies'),
                                             'movies'
                                             )

        self._tab_stack.add_titled_with_icon(ContentView(movie_view=False),
                                             'series',
                                             C_('Category', 'TV Series'),
                                             'series'
                                             )

        shared.schema.bind('win-tab', self._tab_stack,
                           'visible-child-name', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('offline-mode', self._banner,
                           'revealed', Gio.SettingsBindFlags.GET)
        shared.schema.bind('search-enabled', self._search_bar,
                           'search-mode-enabled', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('search-enabled', self._show_search_btn,
                           'active', Gio.SettingsBindFlags.DEFAULT)

        self._search_mode.connect(
            'notify::selected', self._on_search_mode_changed)

        self._tab_stack.connect(
            'notify::visible-child-name', self._check_needs_refresh)

        # Theme switcher (Adapted from https://gitlab.gnome.org/tijder/blueprintgtk/)
        self._menu_btn.get_popover().add_child(ThemeSwitcher(), 'themeswitcher')

    def _check_needs_refresh(self, pspec: GObject.ParamSpec, user_data: object | None) -> None:
        """
        Checks if the tab switched to is pending a refresh and does it if needed.

        Args:
            pspec (GObject.ParamSpec): pspec of the changed property
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """
        if self._tab_stack.get_visible_child_name() == 'movies' and self._needs_refresh == 'movies':
            self._tab_stack.get_child_by_name('movies').refresh_view()
            logging.info('Refreshed movies tab')
            self._needs_refresh = ''
        elif self._tab_stack.get_visible_child_name() == 'series' and self._needs_refresh == 'series':
            self._tab_stack.get_child_by_name('series').refresh_view()
            logging.info('Refreshed TV Series tab')
            self._needs_refresh = ''

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for "map" signal.
        Calls method to check if an automatic content update is due.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self._check_update_content()

    def _check_update_content(self) -> None:
        """
        Checks if a content update is due, triggering it by adding background activities, if necessary.

        Args:
            None

        Returns:
            None
        """

        last_check = datetime.fromisoformat(
            shared.schema.get_string('last-update'))
        frequency = shared.schema.get_string('update-freq')
        last_notification_check = datetime.fromisoformat(
            shared.schema.get_string('last-notification-update'))

        if last_notification_check + timedelta(hours=12) < datetime.now():
            shared.schema.set_string(
                'last-notification-update', datetime.now().strftime('%Y-%m-%d %H:%M'))
            logging.info('Starting automatic notification list update...')
            BackgroundQueue.add(
                activity=BackgroundActivity(
                    activity_type=ActivityType.UPDATE,
                    title=C_('Notification List activity title',
                             'Automatic update of notification list'),
                    task_function=self._update_notification_list),
                on_done=self._on_notification_list_done)

        logging.debug(
            f'Last update done on {last_check}, frequency {frequency}')

        run = True
        match frequency:
            case 'day':
                if last_check + timedelta(days=1) < datetime.now():
                    logging.info('Starting automatic update...')
                    BackgroundQueue.add(
                        activity=BackgroundActivity(
                            activity_type=ActivityType.UPDATE,
                            title=C_('Background activity title',
                                     'Automatic update'),
                            task_function=self._update_content),
                        on_done=self._on_update_done)
            case 'week':
                if last_check + timedelta(days=7) < datetime.now():
                    logging.info('Starting automatic update...')
                    BackgroundQueue.add(
                        activity=BackgroundActivity(
                            activity_type=ActivityType.UPDATE,
                            title=C_('Background activity title',
                                     'Automatic update'),
                            task_function=self._update_content),
                        on_done=self._on_update_done)
            case 'month':
                if last_check + timedelta(days=30) < datetime.now():
                    logging.info('Starting automatic update...')
                    BackgroundQueue.add(
                        activity=BackgroundActivity(
                            activity_type=ActivityType.UPDATE,
                            title=C_('Background activity title',
                                     'Automatic update'),
                            task_function=self._update_content),
                        on_done=self._on_update_done)
            case 'never':
                return

        shared.schema.set_string(
            'last-update', datetime.now().strftime('%Y-%m-%d'))

    def _update_content(self, activity: BackgroundActivity) -> None:
        """
        Performs a content update on manually added content.

        Args:
            activity (BackgroundActivity): the calling activity

        Returns:
            None
        """

        # TMDB updates removed - only manual content supported now
        logging.info('Automatic TMDB updates no longer supported')
        return

    def _on_update_done(self,
                        source: GObject.Object,
                        result: Gio.AsyncResult,
                        cancellable: Gio.Cancellable,
                        activity: BackgroundActivity):
        """Callback to complete async activity"""

        self.refresh()
        logging.info('Automatic update done')
        activity.end()

    def _update_notification_list(self, activity: BackgroundActivity) -> None:
        """
        Performs a content update on the notification list.

        Args:
            activity (BackgroundActivity): the calling activity

        Returns:
            None
        """
        # TMDB updates removed - notification list feature no longer supported
        logging.info('Automatic TMDB notification updates no longer supported')
        return

    def _on_notification_list_done(self,
                                   source: GObject.Object,
                                   result: Gio.AsyncResult,
                                   cancellable: Gio.Cancellable,
                                   activity: BackgroundActivity):
        """Callback to complete async activity"""

        self.refresh()
        logging.info('Automatic notification list update done')
        activity.end()

    def refresh(self) -> None:
        """
        Refreshes the visible window.

        Args:
            None

        Returns:
            None
        """

        if self._tab_stack.get_visible_child_name() == 'movies':
            self._tab_stack.get_child_by_name('movies').refresh_view()
            logging.info('Refreshed movies tab')
            self._needs_refresh = 'series'
        else:
            self._tab_stack.get_child_by_name('series').refresh_view()
            logging.info('Refreshed TV series tab')
            self._needs_refresh = 'movies'

    @Gtk.Template.Callback()
    def _on_searchentry_search_changed(self, user_data: GObject.GPointer | None) -> None:
        shared.schema.set_string('search-query', self._search_entry.get_text())

    @Gtk.Template.Callback()
    def _on_search_btn_toggled(self, user_data: GObject.GPointer | None) -> None:
        shared.schema.set_boolean(
            'search-enabled', self._show_search_btn.get_active())
        shared.schema.set_string('search-query', '')

    def _on_search_mode_changed(self, pspec: GObject.ParamSpec, user_data: object | None) -> None:
        if self._search_mode.get_selected() == 0:
            shared.schema.set_string('search-mode', 'title')
        elif self._search_mode.get_selected() == 1:
            shared.schema.set_string('search-mode', 'genre')
        elif self._search_mode.get_selected() == 2:
            shared.schema.set_string('search-mode', 'overview')
        elif self._search_mode.get_selected() == 3:
            shared.schema.set_string('search-mode', 'notes')
        elif self._search_mode.get_selected() == 4:
            shared.schema.set_string('search-mode', 'tmdb-id')
