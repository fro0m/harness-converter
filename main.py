#!/usr/bin/env python3
"""
Harness Converter - Alternative command-line entry point script

A multi-stage command-line tool that converts AI coding rules and instruction files
(harnesses) among different IDEs and AI agentic environments. It processes
template-based rule files through variable substitution, validation, and format
conversion to generate ready-to-use rules for each target tool.

Note: This is an alternative entry point. The recommended way is to use:
    poetry run harness-converter

Usage:
    python main.py

Or if executable:
    ./main.py

Examples:
    # Run the converter (will show help if no arguments provided)
    python main.py /path/to/project /path/to/rules-description.json

    # With custom output directory
    python main.py /path/to/project /path/to/rules-description.json --output /path/to/output
"""

import sys
import os

# Add the src directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
sys.path.insert(0, src_dir)

def main():
    """Main entry point that delegates to the CLI module."""
    try:
        from harness_converter.cli import main as cli_main
        cli_main()
    except ImportError as e:
        print(f"Error: Cannot import harness-converter modules. Make sure the package is properly installed.")
        print(f"Import error: {e}")
        print(f"Try running: pip install -e .")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
