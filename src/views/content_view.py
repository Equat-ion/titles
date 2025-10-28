# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from gettext import gettext as _
from typing import Callable

from gi.repository import Adw, GObject, Gtk, GLib

from .. import shared  # type: ignore
from ..widgets.catalog_row import CatalogRow
from ..widgets.catalog_item import CatalogItem
from ..providers.stremio_catalog_service import StremioCatalogService


@Gtk.Template(resource_path=shared.PREFIX + '/ui/views/content_view.ui')
class ContentView(Adw.Bin):
    """
    This class represents the content grid view.

    Properties:
        None

    Methods:
        refresh(): Causes the view to update its contents

    Signals:
        None
    """

    __gtype_name__ = 'ContentView'

    movie_view = GObject.Property(type=bool, default=True)
    icon_name = GObject.Property(type=str, default='movies')

    _stack = Gtk.Template.Child()
    _updating_status_lbl = Gtk.Template.Child()
    _catalog_sections_box = Gtk.Template.Child()

    def __init__(self, movie_view: bool):
        super().__init__()
        self.movie_view = movie_view
        self.icon_name = 'movies' if self.movie_view else 'series'
        self.catalog_service = StremioCatalogService()
        self._catalogs_loaded = False
        self._catalog_sections_cache = None

        # Show filled state immediately so UI is responsive
        self._stack.set_visible_child_name('filled')
        
        # Load catalog sections in background (only once)
        if not self._catalogs_loaded:
            self._load_catalog_sections()

    def _load_catalog_sections(self) -> None:
        """
        Load catalog sections from Stremio addons.
        
        Args:
            None
        
        Returns:
            None
        """
        # Return if already loaded
        if self._catalogs_loaded and self._catalog_sections_cache:
            return
            
        # Clear existing catalog sections
        while child := self._catalog_sections_box.get_first_child():
            self._catalog_sections_box.remove(child)
        
        # Add a loading indicator
        loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        loading_box.set_margin_start(12)
        loading_box.set_margin_top(24)
        loading_box.set_halign(Gtk.Align.CENTER)
        
        loading_label = Gtk.Label(label=_("Loading catalogs from Stremio addons..."))
        loading_label.add_css_class("title-2")
        loading_label.set_halign(Gtk.Align.CENTER)
        
        spinner = Adw.Spinner()
        spinner.set_size_request(32, 32)
        spinner.set_halign(Gtk.Align.CENTER)
        
        loading_box.append(loading_label)
        loading_box.append(spinner)
        self._catalog_sections_box.append(loading_box)
        
        # Determine content type based on current view
        content_type = 'movie' if self.movie_view else 'series'
        
        logging.info(f'Loading catalog sections for type: {content_type}')
        
        # Fetch catalogs in a thread to avoid blocking UI
        def fetch_catalogs_threaded():
            try:
                catalog_sections = self.catalog_service.fetch_all_catalogs_for_type(content_type)
                
                # Schedule UI updates on the main thread
                def update_ui():
                    # Remove loading indicator
                    while child := self._catalog_sections_box.get_first_child():
                        self._catalog_sections_box.remove(child)
                    
                    if not catalog_sections:
                        logging.info('No catalogs found or error occurred')
                        # Show empty message
                        empty_label = Gtk.Label(label=_("No catalogs available. Install Stremio addons to see content."))
                        empty_label.add_css_class("dim-label")
                        empty_label.set_margin_start(12)
                        empty_label.set_margin_top(24)
                        empty_label.set_halign(Gtk.Align.START)
                        self._catalog_sections_box.append(empty_label)
                        return False
                    
                    logging.info(f'Loaded {len(catalog_sections)} catalog sections')
                    
                    # Cache the sections and mark as loaded
                    self._catalog_sections_cache = catalog_sections
                    self._catalogs_loaded = True
                    
                    # Create a CatalogRow for each catalog section
                    for section in catalog_sections:
                        catalog_row = CatalogRow(
                            catalog_name=section['catalog_name'],
                            addon_name=section['addon_name']
                        )
                        # Connect show-more signal so we can navigate to a full catalog page
                        catalog_row.connect('show-more', lambda src, s=section: self._open_catalog_full(s))

                        # Add up to 9 catalog items to the preview row (two rows layout)
                        for i, item in enumerate(section['items']):
                            if i >= 9:
                                break

                            catalog_item = CatalogItem(item)
                            catalog_item.connect('clicked', self._on_catalog_item_clicked)
                            catalog_row.add_item(catalog_item)

                        # Show the 'Show more' button only if there are more than 9 items
                        try:
                            catalog_row.set_show_more_visible(len(section['items']) > 9)
                        except Exception:
                            # If the method isn't available for some reason, ignore
                            pass
                        
                        self._catalog_sections_box.append(catalog_row)
                    
                    return False  # Don't repeat
                
                GLib.idle_add(update_ui)
                
            except Exception as e:
                logging.error(f'Error fetching catalogs: {str(e)}')
                import traceback
                logging.error(traceback.format_exc())
                
                # Show error message on main thread
                def show_error():
                    while child := self._catalog_sections_box.get_first_child():
                        self._catalog_sections_box.remove(child)
                    
                    error_label = Gtk.Label(label=_("Failed to load catalogs. Check your internet connection."))
                    error_label.add_css_class("error")
                    error_label.set_margin_start(12)
                    error_label.set_margin_top(24)
                    error_label.set_halign(Gtk.Align.START)
                    self._catalog_sections_box.append(error_label)
                    return False
                
                GLib.idle_add(show_error)
        
        # Run in a background thread
        import threading
        thread = threading.Thread(target=fetch_catalogs_threaded, daemon=True)
        thread.start()

    def _on_catalog_item_clicked(self, source: Gtk.Widget, meta_object: dict) -> None:
        """
        Callback for catalog item click.
        Opens a details view for the catalog item (currently just logs).
        
        Args:
            source (Gtk.Widget): Widget that emitted the signal
            meta_object (dict): The meta preview object from Stremio
        
        Returns:
            None
        """
        item_id = meta_object.get('id', 'unknown')
        item_name = meta_object.get('name', 'Unknown')
        item_type = meta_object.get('type', 'unknown')
        
        logging.info(f'Clicked on catalog item: {item_name} (ID: {item_id}, Type: {item_type})')
        
        # TODO: Open details page for this catalog item
        # For now, we just log the click as requested

    def refresh_view(self) -> None:
        """
        Causes the view to refresh its contents by reloading catalog sections.

        Args:
            None

        Returns:
            None
        """
        self._load_catalog_sections()

    def _open_catalog_full(self, section: dict) -> None:
        """Open the blank full-catalog page (placeholder).

        Args:
            section: The catalog section dict (unused for now but provided for future use)

        Returns:
            None
        """
        # For now, just switch the view stack page to the placeholder
        try:
            self._stack.set_visible_child_name('catalog-full')
        except Exception:
            logging.debug('Unable to switch to full catalog page')
