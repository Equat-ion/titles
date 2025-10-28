#!/usr/bin/env fish
# Quick launcher for Ticket Booth (after initial build)
# Use this after running run-dev.fish at least once

set SCRIPT_DIR (dirname (status --current-filename))
cd $SCRIPT_DIR

# Check if build exists
if not test -d "_build"
    echo "Build directory not found. Please run ./run-dev.fish first"
    exit 1
end

# Activate virtual environment
if test -d "_venv"
    source "_venv/bin/activate.fish"
else
    echo "Virtual environment not found. Please run ./run-dev.fish first"
    exit 1
end

# Set environment and run
set -x GSETTINGS_SCHEMA_DIR "$SCRIPT_DIR/_build/schemas"
python3 "$SCRIPT_DIR/_build/launcher.py"
