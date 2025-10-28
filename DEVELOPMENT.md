# Quick Development Setup for Ticket Booth

This guide explains how to quickly run Ticket Booth for development without installing it system-wide.

## Prerequisites

Before running the development scripts, make sure you have the following installed:

### Required System Packages

#### Fedora/RHEL
```bash
sudo dnf install python3 python3-pip python3-gobject gtk4 libadwaita \
                 blueprint-compiler glib2-devel python3-devel
```

#### Ubuntu/Debian
```bash
sudo apt install python3 python3-pip python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 \
                 blueprint-compiler libglib2.0-dev-bin python3-dev
```

#### Arch Linux
```bash
sudo pacman -S python python-pip python-gobject gtk4 libadwaita blueprint-compiler
```

### Alternative: Flatpak SDK
If you have Flatpak, you can install blueprint-compiler from there:
```bash
flatpak install flathub org.freedesktop.Sdk.Extension.blueprint-compiler
```

## Running the Application

### Option 1: Bash Script (Recommended)
```bash
./run-dev.sh
```

### Option 2: Fish Shell Script
```bash
./run-dev.fish
```

## What the Scripts Do

The development scripts automatically handle:

1. **Python Virtual Environment**: Creates an isolated Python environment in `_venv/`
2. **Dependencies**: Installs all required Python packages (Pillow, tmdbsimple, PyGObject)
3. **Blueprint Compilation**: Compiles all `.blp` UI files to `.ui` XML files
4. **GResource Bundle**: Creates a compiled resource bundle containing all UI files and CSS
5. **Configuration**: Generates the necessary configuration files (`shared.py`, GSchema)
6. **Launch**: Runs the application with all resources properly loaded

## Directory Structure After Running

After running the script, you'll see these new directories:

```
_venv/          # Python virtual environment
_build/         # Build artifacts
  ├── ui/       # Compiled UI files
  ├── css/      # CSS files
  ├── schemas/  # Compiled GSchema
  └── ticketbooth.gresource  # Resource bundle
```

## Development Data Location

The development version stores data separately from the installed version:
- **User Data**: `~/.local/share/ticketbooth-dev/`
  - Database: `data.db`
  - Posters, backgrounds, etc.
  - Logs: `logs/ticketbooth.log`
- **Cache**: `~/.cache/ticketbooth-dev/`

This ensures your development testing doesn't interfere with any installed version.

## Cleaning Up

To clean all build artifacts and start fresh:

```bash
rm -rf _build _venv
rm src/shared.py  # This will be regenerated
```

## Making Changes

### UI Changes (Blueprint files)
After editing any `.blp` file in `src/ui/`, just run the script again. It will recompile the blueprints and restart the app.

### Python Code Changes
For Python code changes in `src/`, simply restart the script. No recompilation needed.

### CSS Changes
After editing CSS files in `src/css/`, run the script again to copy them to the build directory.

## Troubleshooting

### "blueprint-compiler not found"
Install blueprint-compiler using your package manager (see Prerequisites above).

### "glib-compile-resources not found"
Install glib development tools:
- Fedora: `sudo dnf install glib2-devel`
- Ubuntu: `sudo apt install libglib2.0-dev-bin`

### "No module named 'gi'"
Install PyGObject:
```bash
source _venv/bin/activate
pip install PyGObject
```

### Application doesn't start
Check the log file at `~/.local/share/ticketbooth-dev/logs/ticketbooth.log` for error messages.

### GSettings/GSchema errors
Make sure the schema is properly compiled. Delete the `_build/` directory and run the script again.

## Tips

- **Fast Iteration**: Keep the script running and make changes. You can kill the app with Ctrl+C and run the script again.
- **Use Development Data**: The app uses separate data directories, so you can test without affecting your main database.
- **Check Logs**: Always check `~/.local/share/ticketbooth-dev/logs/ticketbooth.log` when debugging.
- **Schema Changes**: If you modify the GSchema in `data/`, delete `_build/schemas/` and run the script again.

## Next Steps

Once you've tested your changes and want to create a proper build:

```bash
meson setup builddir --prefix=/usr/local
meson compile -C builddir
meson install -C builddir
```

Or create a Flatpak package following the instructions in `CONTRIBUTING.md`.
