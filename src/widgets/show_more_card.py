# SPDX-License-Identifier: GPL-3.0-or-later

"""Show-more card widget: a large button that reads 'Show more'."""

from gi.repository import Gtk, GObject
from .. import shared  # type: ignore


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/show_more_card.ui')
class ShowMoreCard(Gtk.Box):
    __gtype_name__ = 'ShowMoreCard'

    _button = Gtk.Template.Child()

    __gsignals__ = {
        'show-more-clicked': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__()

    @Gtk.Template.Callback('_on_button_clicked')
    def _on_button_clicked(self, user_data=None):
        self.emit('show-more-clicked')
