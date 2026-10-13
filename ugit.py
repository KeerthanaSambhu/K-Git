#!/usr/bin/env python3
"""
ugit.py — K-Git Executable Entry Point
========================================
This is the script you run from the terminal.

Usage:
    python ugit.py <command> [arguments]

For example:
    python ugit.py init
    python ugit.py hash-object README.md
    python ugit.py cat-file <sha1>

This file is intentionally minimal. Its only job is to:
  1. Ensure the package directory (ugit/) is importable
  2. Hand control to cli.main() which handles all argument parsing
     and command dispatch

Why keep this file minimal?
  - Separation of concerns: entry point vs. logic
  - Testability: cli.py can be imported and tested independently
  - Installability: in a real project, setup.py would point here as
    the console_scripts entry point
"""

import sys
import os

# Add the directory containing this script to sys.path so that
# 'from ugit import data' works correctly regardless of where
# the user runs this script from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ugit.cli import main

if __name__ == "__main__":
    main()
