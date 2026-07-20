#!/bin/bash
# Simple wrapper script for harness-converter
# This allows running the tool without having to activate the virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the harness-converter tool through the virtual environment
"$SCRIPT_DIR/venv/bin/python" -m harness_converter.cli "$@"
