#!/usr/bin/env python3
"""
Pilot Allowance Calculator - Wrapper Script

This is a convenience wrapper to run the pilot_allowance package.

Usage:
    python calculate_allowance.py [ScheduleReport.pdf] [JarfclrpReport.xls]
    
    or simply place both files in the same directory and run:
    python calculate_allowance.py

Required files:
    - ScheduleReport.pdf: Pilot's schedule report (REQUIRED)
    - JarfclrpReport.xls: Pilot's logbook for accurate calculations

The script will auto-detect files in the current directory if not specified.
"""

import sys
import os

# Add the parent directory to path if running directly
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from pilot_allowance.main import main

if __name__ == "__main__":
    sys.exit(main())

