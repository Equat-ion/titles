# Copyright (C) 2025 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Widget for displaying a horizontal scrolling catalog row (Netflix-style).
"""

import logging
from gi.repository import Gtk, GObject, Adw, GLib
from .. import shared  # type: ignore


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/catalog_row.ui')
class CatalogRow(Gtk.Box):
    """
    Widget for displaying a catalog as a horizontal scrolling row.
    
    Properties:
        catalog_name (str): Name of the catalog
        addon_name (str): Name of the addon providing this catalog
    
    Methods:
        add_item(item_widget): Add an item widget to the catalog row
        clear(): Clear all items from the catalog row
    
    Signals:
        item-clicked(meta_object): Emitted when a catalog item is clicked
    """
    
    __gtype_name__ = 'CatalogRow'
    
    _title_label = Gtk.Template.Child()
    _subtitle_label = Gtk.Template.Child()
    _rows_box = Gtk.Template.Child()
    _row1 = Gtk.Template.Child()
    _row2 = Gtk.Template.Child()
    _show_more_button = Gtk.Template.Child()
    
    # For dynamic layout we keep all added item widgets here and render
    # only the number that fits in the preview area.
    _all_items: list
    _show_more_card = None
    
    catalog_name = GObject.Property(type=str, default='')
    addon_name = GObject.Property(type=str, default='')
    
    __gsignals__ = {
        'item-clicked': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'show-more': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }
    
    def __init__(self, catalog_name: str = '', addon_name: str = ''):
        super().__init__()
        self.catalog_name = catalog_name
        self.addon_name = addon_name
        self._title_label.set_label(catalog_name)
        self._subtitle_label.set_label(addon_name)
        # Track how many items are currently added (max shown = 9)
        self._items_shown = 0
        self._all_items = []
        self._relayout_scheduled = False
        self._show_more_card = None

        # Re-layout after map so allocations are available
        self.connect('map', lambda *a: GLib.idle_add(self._relayout_preview))
    
    
    def _update_button_states(self) -> None:
        """
        Update the enabled/disabled state of navigation buttons.
        
        Returns:
            None
        """
        # Navigation buttons removed; nothing to update
        return
    
    def add_item(self, item_widget: Gtk.Widget) -> None:
        """
        Add an item widget to the catalog row.
        
        Args:
            item_widget (Gtk.Widget): The widget to add
        
        Returns:
            None
        """
        # Buffer the widget; actual layout is handled in _relayout_preview
        self._all_items.append(item_widget)
        # Schedule a relayout once (avoid flooding idles)
        if not self._relayout_scheduled:
            self._relayout_scheduled = True
            GLib.idle_add(self._relayout_preview)
    
    def clear(self) -> None:
        """
        Clear all items from the catalog row.
        
        Args:
            None
        
        Returns:
            None
        """
        # Remove children from both rows and clear buffers
        while child := self._row1.get_first_child():
            self._row1.remove(child)
        while child := self._row2.get_first_child():
            self._row2.remove(child)

        self._all_items.clear()
        self._items_shown = 0
        self._relayout_scheduled = False
        if self._show_more_card:
            self._show_more_card.destroy()
            self._show_more_card = None

    def _relayout_preview(self) -> bool:
        """Layout as many item widgets as fit into the rows. Reserve the
        last visible slot as a show-more card when there are more items than
        fit."""
        self._relayout_scheduled = False

        # Clear current row contents
        while child := self._row1.get_first_child():
            self._row1.remove(child)
        while child := self._row2.get_first_child():
            self._row2.remove(child)

        # If no allocation yet, try again later
        avail_width = self._rows_box.get_allocated_width()
        if avail_width <= 0:
            # schedule retry
            GLib.idle_add(self._relayout_preview)
            return False

        # Card sizing mirrors CatalogItem Adw.Clamp maximum-size
        card_width = 180
        spacing = 12

        # Compute how many columns can fit horizontally
        import math
        columns = max(1, math.floor((avail_width + spacing) / (card_width + spacing)))
        visible_slots = columns * 2

        total_items = len(self._all_items)
        # If everything fits, show all
        if total_items <= visible_slots:
            items_to_show = total_items
            need_show_more = False
        else:
            # Reserve last slot for show-more card
            items_to_show = max(0, visible_slots - 1)
            need_show_more = True

        # Append items_to_show widgets into rows (first row fills first)
        for idx in range(items_to_show):
            widget = self._all_items[idx]
            if idx < columns:
                self._row1.append(widget)
            else:
                self._row2.append(widget)

        self._items_shown = items_to_show

        # Add show-more card if needed
        if need_show_more:
            # create show-more card lazily
            if not self._show_more_card:
                from .show_more_card import ShowMoreCard
                self._show_more_card = ShowMoreCard()
                self._show_more_card.connect('show-more-clicked', lambda *a: self.emit('show-more'))

            # Place show-more card as the last visible slot
            last_index = items_to_show
            if last_index < columns:
                self._row1.append(self._show_more_card)
            else:
                self._row2.append(self._show_more_card)

        else:
            if self._show_more_card:
                self._show_more_card.destroy()
                self._show_more_card = None

        return False

    @Gtk.Template.Callback('_on_show_more_clicked')
    def _on_show_more_clicked(self, button: Gtk.Button) -> None:
        """Emit a 'show-more' signal when the user requests the full catalog."""
        self.emit('show-more')

    def set_show_more_visible(self, visible: bool) -> None:
        """Set the visibility of the show-more button."""
        if self._show_more_button:
            self._show_more_button.set_visible(visible)
