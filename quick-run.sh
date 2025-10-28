#!/usr/bin/env bash
# Quick launcher for Ticket Booth (after initial build)
# Use this after running run-dev.sh at least once

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if build exists
if [ ! -d "_build" ]; then
    echo "Build directory not found. Please run ./run-dev.sh first"
    exit 1
fi

# Activate virtual environment
if [ -d "_venv" ]; then
    source "_venv/bin/activate"
else
    echo "Virtual environment not found. Please run ./run-dev.sh first"
    exit 1
fi

# Set environment and run
export GSETTINGS_SCHEMA_DIR="$SCRIPT_DIR/_build/schemas"
python3 "$SCRIPT_DIR/_build/launcher.py"
