#!/usr/bin/env fish
# Quick development run script for Ticket Booth (Fish shell version)
# This script sets up everything needed to run the app without installing it system-wide

set SCRIPT_DIR (dirname (status --current-filename))
cd $SCRIPT_DIR

# Colors for output
set GREEN \e\[0\;32m
set BLUE \e\[0\;34m
set YELLOW \e\[1\;33m
set RED \e\[0\;31m
set NC \e\[0m

echo -e "$BLUE=== Ticket Booth Development Runner ===$NC"

# Create build directory if it doesn't exist
set BUILD_DIR "$SCRIPT_DIR/_build"
set VENV_DIR "$SCRIPT_DIR/_venv"

# Check if Python 3 is available
if not command -v python3 &> /dev/null
    echo -e "$RED""Error: python3 is not installed""$NC"
    exit 1
end

# Check if blueprint-compiler is available
if not command -v blueprint-compiler &> /dev/null
    echo -e "$RED""Error: blueprint-compiler is not installed""$NC"
    echo -e "$YELLOW""Install it with: flatpak install flathub org.freedesktop.Sdk.Extension.blueprint-compiler""$NC"
    echo -e "$YELLOW""Or on Fedora: sudo dnf install blueprint-compiler""$NC"
    echo -e "$YELLOW""Or on Ubuntu: sudo apt install blueprint-compiler""$NC"
    exit 1
end

# Check if glib-compile-resources is available
if not command -v glib-compile-resources &> /dev/null
    echo -e "$RED""Error: glib-compile-resources is not installed""$NC"
    echo -e "$YELLOW""Install it with: sudo dnf install glib2-devel (Fedora)""$NC"
    echo -e "$YELLOW""Or: sudo apt install libglib2.0-dev-bin (Ubuntu)""$NC"
    exit 1
end

# Set up Python virtual environment
if not test -d "$VENV_DIR"
    echo -e "$GREEN""Creating Python virtual environment...""$NC"
    python3 -m venv "$VENV_DIR"
end

# Activate virtual environment
source "$VENV_DIR/bin/activate.fish"

# Install Python dependencies
echo -e "$GREEN""Installing Python dependencies...""$NC"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet PyGObject

# Create build directory
mkdir -p "$BUILD_DIR"

# Compile Blueprint files to UI files
echo -e "$GREEN""Compiling Blueprint files...""$NC"
mkdir -p "$BUILD_DIR/ui/widgets"
mkdir -p "$BUILD_DIR/ui/dialogs"
mkdir -p "$BUILD_DIR/ui/views"
mkdir -p "$BUILD_DIR/ui/pages"
mkdir -p "$BUILD_DIR/ui/gtk"

blueprint-compiler batch-compile "$BUILD_DIR/ui" "$SCRIPT_DIR/src/ui" \
    "$SCRIPT_DIR/src/ui/window.blp" \
    "$SCRIPT_DIR/src/ui/about_dialog.blp" \
    "$SCRIPT_DIR/src/ui/preferences.blp"

blueprint-compiler batch-compile "$BUILD_DIR/ui/gtk" "$SCRIPT_DIR/src/ui/gtk" \
    "$SCRIPT_DIR/src/ui/gtk/help-overlay.blp"

blueprint-compiler batch-compile "$BUILD_DIR/ui/views" "$SCRIPT_DIR/src/ui/views" \
    "$SCRIPT_DIR/src/ui/views/main_view.blp" \
    "$SCRIPT_DIR/src/ui/views/db_update_view.blp" \
    "$SCRIPT_DIR/src/ui/views/content_view.blp"

blueprint-compiler batch-compile "$BUILD_DIR/ui/dialogs" "$SCRIPT_DIR/src/ui/dialogs" \
    "$SCRIPT_DIR/src/ui/dialogs/add_manual.blp" \
    "$SCRIPT_DIR/src/ui/dialogs/edit_season.blp" \
    "$SCRIPT_DIR/src/ui/dialogs/message_dialogs.blp" \
    "$SCRIPT_DIR/src/ui/dialogs/stremio_login.blp"

blueprint-compiler batch-compile "$BUILD_DIR/ui/pages" "$SCRIPT_DIR/src/ui/pages" \
    "$SCRIPT_DIR/src/ui/pages/edit_episode_page.blp" \
    "$SCRIPT_DIR/src/ui/pages/details_page.blp"

blueprint-compiler batch-compile "$BUILD_DIR/ui/widgets" "$SCRIPT_DIR/src/ui/widgets" \
    "$SCRIPT_DIR/src/ui/widgets/theme_switcher.blp" \
    "$SCRIPT_DIR/src/ui/widgets/poster_button.blp" \
    "$SCRIPT_DIR/src/ui/widgets/search_result_row.blp" \
    "$SCRIPT_DIR/src/ui/widgets/episode_row.blp" \
    "$SCRIPT_DIR/src/ui/widgets/image_selector.blp" \
    "$SCRIPT_DIR/src/ui/widgets/season_expander.blp" \
    "$SCRIPT_DIR/src/ui/widgets/background_indicator.blp" \
    "$SCRIPT_DIR/src/ui/widgets/background_activity_row.blp" \
    "$SCRIPT_DIR/src/ui/widgets/account_button.blp" \
    "$SCRIPT_DIR/src/ui/widgets/catalog_row.blp" \
    "$SCRIPT_DIR/src/ui/widgets/catalog_item.blp"

# Copy CSS files
echo -e "$GREEN""Copying CSS files...""$NC"
mkdir -p "$BUILD_DIR/css"
cp $SCRIPT_DIR/src/css/*.css "$BUILD_DIR/css/"

# Generate gresource XML file
echo -e "$GREEN""Generating gresource file...""$NC"
printf '<?xml version="1.0" encoding="UTF-8"?>
<gresources>
  <gresource prefix="/me/iepure/Ticketbooth/Devel">
    <file compressed="true" preprocess="xml-stripblanks">ui/window.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/about_dialog.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/preferences.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/gtk/help-overlay.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/views/main_view.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/views/db_update_view.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/views/content_view.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/dialogs/add_manual.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/dialogs/edit_season.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/dialogs/message_dialogs.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/dialogs/stremio_login.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/pages/edit_episode_page.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/pages/details_page.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/widgets/theme_switcher.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/widgets/poster_button.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/widgets/search_result_row.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/widgets/episode_row.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/widgets/image_selector.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/widgets/season_expander.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/widgets/background_indicator.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/widgets/background_activity_row.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/widgets/account_button.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/widgets/catalog_row.ui</file>
    <file compressed="true" preprocess="xml-stripblanks">ui/widgets/catalog_item.ui</file>
    <file>css/style.css</file>
    <file>css/style-dark.css</file>
  </gresource>
</gresources>' > "$BUILD_DIR/ticketbooth.gresource.xml"

# Compile gresource bundle
echo -e "$GREEN""Compiling gresource bundle...""$NC"
glib-compile-resources --sourcedir="$BUILD_DIR" \
    --target="$BUILD_DIR/ticketbooth.gresource" \
    "$BUILD_DIR/ticketbooth.gresource.xml"

# Generate shared.py configuration file
echo -e "$GREEN""Generating shared.py configuration...""$NC"
printf '# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import gi
gi.require_version(\'Gdk\', \'4.0\')
gi.require_version(\'Gio\', \'2.0\')
gi.require_version(\'GLib\', \'2.0\')

from gi.repository import Gdk, Gio, GLib
from pathlib import Path
import logging
from .logging.session_file_handler import SessionFileHandler
import faulthandler
import os

APP_ID = \'me.iepure.Ticketbooth.Devel\'
VERSION = \'Development\'
PREFIX = \'/me/iepure/Ticketbooth/Devel\'
APP_NAME = \'Ticket Booth (Development)\'

# Try to load schema from build directory first, then data directory
schema = None
try:
    schema_source = Gio.SettingsSchemaSource.new_from_directory(
        str(Path(__file__).parent.parent / \'_build\' / \'schemas\'),
        Gio.SettingsSchemaSource.get_default(),
        False
    )
    schema_obj = schema_source.lookup(\'me.iepure.Ticketbooth.Devel\', False)
    if schema_obj:
        schema = Gio.Settings.new_full(schema_obj, None, None)
except Exception as e:
    logging.warning(f"Could not load GSettings schema: {e}")
    schema = None

data_dir = Path(GLib.get_user_data_dir()) / \'ticketbooth-dev\'
cache_dir = Path(GLib.get_user_cache_dir()) / \'ticketbooth-dev\'

poster_dir = data_dir / \'poster\'
background_dir = data_dir / \'background\'
series_dir = data_dir / \'series\'

db = data_dir / \'data.db\'

if not os.path.exists(data_dir/\'logs\'):
    os.makedirs(data_dir/\'logs\')
faulthandler.enable(file=open(data_dir/\'logs\'/\'crash.log\',"w"))

DEBUG = True
logging.basicConfig(level=logging.DEBUG,
                    format=\'%%(asctime)s - %%(levelname)s - %%(message)s\',
                    filename=data_dir / \'logs\' / \'ticketbooth.log\')

handler = SessionFileHandler(filename=data_dir / \'logs\' / \'ticketbooth.log\')
handler.setFormatter(logging.Formatter(\'%%(asctime)s - %%(levelname)s - %%(message)s\'))
logging.getLogger().addHandler(handler)

log_files = None
' > "$SCRIPT_DIR/src/shared.py"

# Generate GSchema file
echo -e "$GREEN""Compiling GSchema...""$NC"
mkdir -p "$BUILD_DIR/schemas"

# Copy and modify the original schema file
sed 's/@app_id@/me.iepure.Ticketbooth.Devel/g; s|@prefix@|/me/iepure/Ticketbooth/Devel|g' \
    "$SCRIPT_DIR/data/me.iepure.Ticketbooth.gschema.xml.in" \
    > "$BUILD_DIR/schemas/me.iepure.Ticketbooth.Devel.gschema.xml"

glib-compile-schemas "$BUILD_DIR/schemas"

# Create launcher script
echo -e "$GREEN""Creating launcher script...""$NC"
printf '#!/usr/bin/env python3
import os
import sys
import signal
from pathlib import Path

# Get the script directory
script_dir = Path(__file__).parent.parent

# Set up paths
os.environ[\'GSETTINGS_SCHEMA_DIR\'] = str(script_dir / \'_build\' / \'schemas\')
sys.path.insert(0, str(script_dir))

# Signal handling
signal.signal(signal.SIGINT, signal.SIG_DFL)

if __name__ == \'__main__\':
    import gi
    gi.require_version(\'Gtk\', \'4.0\')
    gi.require_version(\'Adw\', \'1\')
    
    from gi.repository import Gio
    
    # Load gresource
    resource_path = script_dir / \'_build\' / \'ticketbooth.gresource\'
    if resource_path.exists():
        resource = Gio.Resource.load(str(resource_path))
        resource._register()
    else:
        print(f"Error: Resource file not found at {resource_path}")
        sys.exit(1)
    
    # Import and run the app
    from src import main
    sys.exit(main.main())
' > "$BUILD_DIR/launcher.py"

chmod +x "$BUILD_DIR/launcher.py"

# Run the application
echo -e "$GREEN""Starting Ticket Booth...""$NC"
echo ""
set -x GSETTINGS_SCHEMA_DIR "$BUILD_DIR/schemas"
python3 "$BUILD_DIR/launcher.py"
