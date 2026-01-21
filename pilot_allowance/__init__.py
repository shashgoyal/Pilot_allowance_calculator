"""
Pilot Allowance Calculator Package

A Python tool to calculate pilot allowances based on:
- ScheduleReport.pdf (flight schedule)
- JarfclrpReport.xls (pilot logbook)

Based on Revised Cockpit Crew Allowances effective 1st January 2026.
"""

from .models import (
    PilotInfo,
    FlightDuty,
    LogbookFlight,
    TrainingDuty,
    Layover,
    AllowanceBreakdown,
)

from .constants import (
    RATES,
    AIRPORT_TIMEZONE_OFFSET_FROM_IST,
    INDIAN_AIRPORTS,
    is_domestic_airport,
)

from .parsers import (
    PDFScheduleParser,
    LogbookParser,
    LogbookPDFParser,
    LogbookParserBase,
    create_logbook_parser,
)

from .calculators import (
    TailSwapDetector,
    NightHoursCalculator,
    TransitCalculator,
    AllowanceCalculator,
)

from .report import (
    generate_report,
    print_report,
    save_report,
)

# API (optional - requires fastapi)
try:
    from .api import app as api_app
except ImportError:
    api_app = None

__version__ = "1.0.0"
__author__ = "Pilot Allowance Calculator"

__all__ = [
    # Models
    "PilotInfo",
    "FlightDuty",
    "LogbookFlight",
    "TrainingDuty",
    "Layover",
    "AllowanceBreakdown",
    # Constants
    "RATES",
    "AIRPORT_TIMEZONE_OFFSET_FROM_IST",
    "INDIAN_AIRPORTS",
    "is_domestic_airport",
    # Parsers
    "PDFScheduleParser",
    "LogbookParser",
    # Calculators
    "TailSwapDetector",
    "NightHoursCalculator",
    "TransitCalculator",
    "AllowanceCalculator",
    # Report
    "generate_report",
    "print_report",
    "save_report",
]

