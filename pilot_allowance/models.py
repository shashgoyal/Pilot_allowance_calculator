"""
Data models for Pilot Allowance Calculator.
Contains all dataclasses used throughout the application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class PilotInfo:
    """Contains pilot information extracted from schedule."""
    employee_id: str
    name: str
    base: str
    rank: str  # 'CP' for Captain, 'FO' for First Officer
    aircraft_type: str
    
    def __str__(self) -> str:
        rank_name = "Captain" if self.rank == 'CP' else "First Officer"
        return f"{self.name} ({rank_name}, {self.base})"


@dataclass
class FlightDuty:
    """Represents a single flight duty entry from the schedule."""
    date: str
    duty_code: str
    crew_details: str
    is_operating: bool = False   # True if pilot is PIC/operating
    is_deadhead: bool = False    # True if pilot is deadheading (DHF)
    departure_airport: str = ""
    arrival_airport: str = ""
    block_time: str = ""         # Block time in HH:MM format


@dataclass
class LogbookFlight:
    """
    Represents a flight from the pilot logbook (JarfclrpReport.xls).
    Contains detailed flight information including aircraft registration.
    """
    date: str                    # DD/MM/YY format
    departure_airport: str
    departure_time: str          # HH:MM format
    arrival_airport: str
    arrival_time: str            # HH:MM format
    aircraft_type: str
    aircraft_reg: str            # Aircraft registration (e.g., VT-IWN)
    flight_time: str             # Flight duration
    pic_name: str
    takeoff_day: int = 0
    takeoff_night: int = 0
    landing_day: int = 0
    landing_night: int = 0
    hours_as_pic: str = ""
    hours_as_copilot: str = ""


@dataclass
class TrainingDuty:
    """Represents a training duty entry from the schedule."""
    date: str
    time_range: str              # e.g., "1848 - 2033"
    duty_type: str               # Type of training
    crew: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class Layover:
    """Represents a layover at a station with check-in/out times."""
    station: str                 # Airport code (e.g., CCU)
    dates: List[str]             # List of dates for the layover
    check_in: Optional[datetime] = None    # First arrival at hotel
    check_out: Optional[datetime] = None   # Last departure from hotel
    duration_hours: float = 0.0
    is_domestic: bool = True     # True for domestic, False for international


@dataclass
class AllowanceDetail:
    """Individual allowance detail with date for filtering."""
    date: str  # Date in DD/MM/YYYY format
    description: str  # Human-readable description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'date': self.date,
            'description': self.description
        }


@dataclass
class AllowanceBreakdown:
    """Detailed breakdown of all allowances calculated."""
    
    # Tail-swap
    tail_swap_count: int = 0
    tail_swap_amount: float = 0.0
    tail_swap_details: List[AllowanceDetail] = field(default_factory=list)
    
    # Transit
    transit_hours: float = 0.0
    transit_amount: float = 0.0
    transit_details: List[AllowanceDetail] = field(default_factory=list)
    
    # Layover
    layover_count: int = 0
    layover_base_amount: float = 0.0
    layover_extra_hours: float = 0.0
    layover_extra_amount: float = 0.0
    layover_total: float = 0.0
    layover_details: List[AllowanceDetail] = field(default_factory=list)
    
    # Deadhead
    deadhead_hours: float = 0.0
    deadhead_amount: float = 0.0
    deadhead_details: List[AllowanceDetail] = field(default_factory=list)
    
    # Night
    night_hours: float = 0.0
    night_amount: float = 0.0
    night_details: List[AllowanceDetail] = field(default_factory=list)
    
    # Total
    total_amount: float = 0.0
    
    def calculate_total(self) -> float:
        """Calculate and return the total allowance amount."""
        self.total_amount = (
            self.tail_swap_amount +
            self.transit_amount +
            self.layover_total +
            self.deadhead_amount +
            self.night_amount
        )
        return self.total_amount

