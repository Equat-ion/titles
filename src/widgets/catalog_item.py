# Copyright (C) 2025 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Widget for displaying a single catalog item in a catalog row.
"""

import logging
import hashlib
import requests
import threading
from pathlib import Path
from gi.repository import Gio, GObject, Gtk, Adw, GLib
from .. import shared  # type: ignore


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/catalog_item.ui')
class CatalogItem(Gtk.Box):
    """
    Widget for displaying a single catalog item with poster and title.
    
    Properties:
        title (str): Item's title
        poster_url (str): URL to item's poster
        meta_object (object): The meta preview object from Stremio
    
    Methods:
        None
    
    Signals:
        clicked(meta_object): Emitted when the user clicks on the item
    """
    
    __gtype_name__ = 'CatalogItem'
    
    _picture = Gtk.Template.Child()
    _spinner = Gtk.Template.Child()
    _title_label = Gtk.Template.Child()
    _release_label = Gtk.Template.Child()
    
    title = GObject.Property(type=str, default='')
    poster_url = GObject.Property(type=str, default='')
    release_info = GObject.Property(type=str, default='')
    meta_object = GObject.Property(type=object, default=None)
    
    __gsignals__ = {
        'clicked': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
    }
    
    def __init__(self, meta_object: dict):
        super().__init__()
        self.meta_object = meta_object
        self.title = meta_object.get('name', 'Unknown')
        self.poster_url = meta_object.get('poster', '')
        self.release_info = meta_object.get('releaseInfo', '')
    
    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for the 'map' signal.
        Sets images and labels with caching support.
        
        Args:
            user_data (object or None): data passed to the callback
        
        Returns:
            None
        """
        if self.poster_url:
            # Load poster in background thread to avoid blocking UI
            thread = threading.Thread(target=self._load_poster_async, daemon=True)
            thread.start()
        else:
            self._spinner.set_visible(False)
        
        if not self.release_info:
            self._release_label.set_visible(False)
    
    def _load_poster_async(self) -> None:
        """
        Load poster in background thread and update UI when done.
        
        Returns:
            None
        """
        poster_file = self._get_cached_poster()
        
        # Update UI on main thread
        def update_ui():
            if poster_file:
                self._picture.set_file(poster_file)
            self._spinner.set_visible(False)
            return False
        
        GLib.idle_add(update_ui)
    
    def _get_cached_poster(self) -> Gio.File | None:
        """
        Get poster from cache or download it.
        
        Returns:
            Gio.File or None: File object for the poster
        """
        try:
            # Create a hash of the URL for the filename
            url_hash = hashlib.md5(self.poster_url.encode()).hexdigest()
            cache_path = shared.cache_dir / f'catalog_{url_hash}.jpg'
            
            # Check if cached file exists
            if cache_path.exists():
                logging.debug(f'Cache hit for poster: {self.poster_url}')
                return Gio.File.new_for_path(str(cache_path))
            
            # Download and cache the poster
            logging.debug(f'Downloading poster: {self.poster_url}')
            response = requests.get(self.poster_url, timeout=10)
            
            if response.status_code == 200:
                # Ensure cache directory exists
                shared.cache_dir.mkdir(parents=True, exist_ok=True)
                
                # Save to cache
                with open(cache_path, 'wb') as f:
                    f.write(response.content)
                
                logging.debug(f'Cached poster to: {cache_path}')
                return Gio.File.new_for_path(str(cache_path))
            else:
                logging.warning(f'Failed to download poster: {response.status_code}')
                return None
                
        except Exception as e:
            logging.error(f'Error getting poster: {str(e)}')
            return None
    
    @Gtk.Template.Callback('_on_button_clicked')
    def _on_button_clicked(self, user_data: object | None) -> None:
        """
        Callback for button click.
        Emits the clicked signal with the meta object.
        
        Args:
            user_data (object or None): data passed to the callback
        
        Returns:
            None
        """
        self.emit('clicked', self.meta_object)
