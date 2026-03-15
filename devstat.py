#!/usr/bin/env python3
"""
devstat — entry point.
Launches the GUI by default; use sub-commands for CLI mode.
"""
import sys
from devstat.cli import main

if __name__ == "__main__":
    main()
