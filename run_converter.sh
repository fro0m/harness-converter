#!/bin/bash
# Simple wrapper script for harness-converter
# This allows running the tool without having to activate the virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ ! -x "$SCRIPT_DIR/venv/bin/harness-converter" ] && [ ! -x "$SCRIPT_DIR/venv/bin/python" ]; then
  echo "venv missing — run install_harness.sh first" >&2
  exit 1
fi

# Run the harness-converter tool through the virtual environment
"$SCRIPT_DIR/venv/bin/python" -m harness_converter.cli "$@"
