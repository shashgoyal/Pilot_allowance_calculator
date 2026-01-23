#!/usr/bin/env python3
"""
Pilot Allowance Calculator
Based on Revised Cockpit Crew Allowances effective 1st January 2026

This script has been refactored into a modular package structure.
See the 'pilot_allowance' directory for the organized code:

    pilot_allowance/
    ├── __init__.py      # Package exports
    ├── __main__.py      # Module entry point
    ├── constants.py     # Rates, timezones, airport codes
    ├── models.py        # Data classes
    ├── parsers.py       # PDF and XLS parsers
    ├── calculators.py   # Allowance calculation logic
    ├── report.py        # Report generation
    └── main.py          # Main entry point

Usage:
    python pilot_allowance_calculator.py [ScheduleReport.pdf] [JarfclrpReport.xls]

    or use the module directly:
    python -m pilot_allowance [ScheduleReport.pdf] [JarfclrpReport.xls]

Required files:
    - ScheduleReport.pdf: Pilot's schedule report (REQUIRED)
    - JarfclrpReport.xls: Pilot's logbook for accurate calculations
"""

import sys
import os

# Add the script directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from pilot_allowance.main import main

if __name__ == "__main__":
    sys.exit(main())
