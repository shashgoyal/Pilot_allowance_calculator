"""
Calculation logic for pilot allowances.
Contains all classes responsible for calculating different types of allowances.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .models import LogbookFlight, AllowanceBreakdown, AllowanceDetail
from .constants import RATES, is_domestic_airport
from .parsers import PDFScheduleParser, LogbookParser


class TailSwapDetector:
    """
    Detects tail-swaps by analyzing aircraft registration changes
    between consecutive flights on the same duty day.
    
    A tail-swap occurs when a pilot operates consecutive flights on
    different aircraft within the same duty period.
    """
    
    def __init__(self, logbook_parser: LogbookParser):
        self.logbook = logbook_parser
        self.tail_swaps: List[Dict] = []
    
    def detect_tail_swaps(self) -> List[Dict]:
        """
        Detect tail-swaps from logbook by comparing aircraft registrations
        between consecutive flights on the same day.
        
        Returns:
            List of tail-swap events with flight details
        """
        self.tail_swaps = []
        flights_by_date = self.logbook.get_flights_by_date()
        
        for date, flights in flights_by_date.items():
            if len(flights) < 2:
                continue
            
            # Sort flights by departure time
            sorted_flights = sorted(flights, key=lambda f: f.departure_time)
            
            for i in range(1, len(sorted_flights)):
                prev_flight = sorted_flights[i - 1]
                curr_flight = sorted_flights[i]
                
                prev_reg = prev_flight.aircraft_reg.strip().upper()
                curr_reg = curr_flight.aircraft_reg.strip().upper()
                
                # Aircraft registration changed = tail-swap
                if prev_reg and curr_reg and prev_reg != curr_reg:
                    tail_swap = {
                        'date': date,
                        'date_full': self.logbook.normalize_date(date),
                        'prev_flight': {
                            'route': f"{prev_flight.departure_airport}-{prev_flight.arrival_airport}",
                            'time': f"{prev_flight.departure_time}-{prev_flight.arrival_time}",
                            'aircraft_reg': prev_reg,
                        },
                        'curr_flight': {
                            'route': f"{curr_flight.departure_airport}-{curr_flight.arrival_airport}",
                            'time': f"{curr_flight.departure_time}-{curr_flight.arrival_time}",
                            'aircraft_reg': curr_reg,
                        },
                    }
                    self.tail_swaps.append(tail_swap)
        
        return self.tail_swaps
    
    def get_count(self) -> int:
        """Return the number of tail-swaps detected."""
        return len(self.tail_swaps)
    
    def get_formatted_details(self) -> List[AllowanceDetail]:
        """Return AllowanceDetail objects describing each tail-swap."""
        details = []
        for swap in self.tail_swaps:
            description = (
                f"{swap['prev_flight']['aircraft_reg']} → {swap['curr_flight']['aircraft_reg']} "
                f"({swap['prev_flight']['route']} → {swap['curr_flight']['route']})"
            )
            details.append(AllowanceDetail(
                date=swap['date_full'],
                description=description
            ))
        return details


class NightHoursCalculator:
    """
    Calculates night flying hours from logbook data.
    
    Night hours are defined as flight time between 00:00 and 06:00 IST.
    For international flights, times are converted to IST before calculation.
    """
    
    NIGHT_START_HOUR = 0   # 00:00 IST
    NIGHT_END_HOUR = 6     # 06:00 IST
    
    def __init__(self, logbook_parser: LogbookParser):
        self.logbook = logbook_parser
        self.night_flight_details: List[Dict] = []
        self.total_night_hours: float = 0.0
    
    def calculate_night_hours(self) -> float:
        """
        Calculate total night flying hours from all flights.
        
        Returns:
            Total night hours across all flights
        """
        self.night_flight_details = []
        self.total_night_hours = 0.0
        
        for flight in self.logbook.flights:
            result = self._calculate_flight_night_hours(flight)
            if result and result['night_hours'] > 0:
                self.total_night_hours += result['night_hours']
                self.night_flight_details.append({
                    'date': result['date_ist'],
                    'route': f"{flight.departure_airport.strip()}-{flight.arrival_airport.strip()}",
                    'dep_time_ist': result['dep_time_ist'],
                    'arr_time_ist': result['arr_time_ist'],
                    'night_hours': result['night_hours'],
                })
        
        return self.total_night_hours
    
    def _calculate_flight_night_hours(self, flight: LogbookFlight) -> Optional[Dict]:
        """Calculate night hours for a single flight with IST conversion.
        
        Note: Logbook times are in GMT. We convert to IST by adding 5:30 hours.
        
        Returns:
            Dict with night_hours, IST times and date, or None if parsing fails
        """
        try:
            dep_time = self._parse_time(flight.departure_time)
            arr_time = self._parse_time(flight.arrival_time)
            
            if dep_time is None or arr_time is None:
                return None
            
            # Parse date
            date_parts = flight.date.split('/')
            if len(date_parts) == 3:
                day = int(date_parts[0])
                month = int(date_parts[1])
                year = int(date_parts[2])
                if year < 100:
                    year += 2000
                
                # Create datetime objects in GMT
                dep_datetime_gmt = datetime(year, month, day, dep_time[0], dep_time[1])
                arr_datetime_gmt = datetime(year, month, day, arr_time[0], arr_time[1])
                
                # Handle overnight flights (in GMT)
                if arr_datetime_gmt <= dep_datetime_gmt:
                    arr_datetime_gmt += timedelta(days=1)
            else:
                return None
            
            # Convert GMT to IST by adding 5 hours 30 minutes
            dep_ist = self._convert_gmt_to_ist(dep_datetime_gmt)
            arr_ist = self._convert_gmt_to_ist(arr_datetime_gmt)
            
            # Calculate night hours (00:00-06:00 IST)
            night_hours = self._calculate_night_overlap(dep_ist, arr_ist)
            
            return {
                'night_hours': night_hours,
                'date_ist': dep_ist.strftime('%d/%m/%Y'),
                'dep_time_ist': dep_ist.strftime('%H:%M'),
                'arr_time_ist': arr_ist.strftime('%H:%M'),
            }
            
        except Exception:
            return None
    
    def _parse_time(self, time_str: str) -> Optional[Tuple[int, int]]:
        """Parse time string (HH:MM) to (hour, minute) tuple."""
        time_str = time_str.strip()
        if ':' in time_str:
            parts = time_str.split(':')
            try:
                return (int(parts[0]), int(parts[1]))
            except ValueError:
                return None
        return None
    
    def _convert_gmt_to_ist(self, dt: datetime) -> datetime:
        """
        Convert GMT time to IST.
        
        IST is GMT + 5:30 hours.
        
        Args:
            dt: Datetime in GMT
            
        Returns:
            Datetime converted to IST
        """
        # IST = GMT + 5 hours 30 minutes
        return dt + timedelta(hours=5, minutes=30)
    
    def _calculate_night_overlap(self, dep_ist: datetime, arr_ist: datetime) -> float:
        """
        Calculate hours of flight within the night window (00:00-06:00 IST).
        """
        total_night_hours = 0.0
        current = dep_ist
        
        while current < arr_ist:
            current_hour = current.hour
            
            if self.NIGHT_START_HOUR <= current_hour < self.NIGHT_END_HOUR:
                # Within night window
                night_window_end = current.replace(
                    hour=self.NIGHT_END_HOUR, minute=0, second=0
                )
                end_point = min(night_window_end, arr_ist)
                
                duration_seconds = (end_point - current).total_seconds()
                if duration_seconds > 0:
                    total_night_hours += duration_seconds / 3600
                
                current = end_point
            else:
                # Outside night window - advance to next potential night window
                next_hour = current.replace(minute=0, second=0) + timedelta(hours=1)
                
                if current.hour >= self.NIGHT_END_HOUR:
                    # Move to midnight of next day
                    next_midnight = (current + timedelta(days=1)).replace(
                        hour=0, minute=0, second=0
                    )
                    if next_midnight < arr_ist:
                        current = next_midnight
                    else:
                        break
                else:
                    current = next_hour
                    
                if current >= arr_ist:
                    break
        
        return round(total_night_hours, 2)
    
    def get_formatted_details(self) -> List[AllowanceDetail]:
        """Return AllowanceDetail objects describing each night flight."""
        details = []
        for flight in self.night_flight_details:
            description = (
                f"{flight['route']} | "
                f"{flight['dep_time_ist']}-{flight['arr_time_ist']} IST | "
                f"Night: {flight['night_hours']:.2f} hrs"
            )
            details.append(AllowanceDetail(
                date=flight['date'],
                description=description
            ))
        return details


class TransitCalculator:
    """
    Calculates transit allowance from flight data.
    
    Transit is the time between landing of one flight and departure of the next
    at the same station.
    
    Rules:
        - Only domestic halts qualify
        - Minimum 90 minutes to qualify
        - Maximum 4 hours per halt
    """
    
    TRANSIT_MIN_MINUTES = 90
    TRANSIT_MAX_HOURS = 4.0
    
    def __init__(self, logbook_parser: LogbookParser):
        self.logbook = logbook_parser
        self.transit_events: List[Dict] = []
        self.total_transit_hours: float = 0.0
    
    def calculate_transit(self) -> float:
        """
        Calculate total eligible transit hours.
        
        Returns:
            Total transit hours (capped at 4 hours per event)
        """
        self.transit_events = []
        self.total_transit_hours = 0.0
        
        flights_by_date = self.logbook.get_flights_by_date()
        
        for date, flights in flights_by_date.items():
            if len(flights) < 2:
                continue
            
            sorted_flights = sorted(flights, key=lambda f: f.departure_time)
            
            for i in range(1, len(sorted_flights)):
                prev_flight = sorted_flights[i - 1]
                curr_flight = sorted_flights[i]
                
                # Only domestic transits qualify
                prev_arr = prev_flight.arrival_airport.strip()
                curr_dep = curr_flight.departure_airport.strip()
                
                if not is_domestic_airport(prev_arr):
                    continue
                if not is_domestic_airport(curr_dep):
                    continue
                
                # Must be same station
                if prev_arr != curr_dep:
                    continue
                
                # Calculate halt time
                try:
                    prev_arr_time = datetime.strptime(prev_flight.arrival_time, "%H:%M")
                    curr_dep_time = datetime.strptime(curr_flight.departure_time, "%H:%M")
                    
                    if curr_dep_time < prev_arr_time:
                        curr_dep_time += timedelta(days=1)
                    
                    halt = curr_dep_time - prev_arr_time
                    halt_minutes = halt.total_seconds() / 60
                    halt_hours = halt.total_seconds() / 3600
                    
                    # Must be > 90 minutes to qualify
                    if halt_minutes > self.TRANSIT_MIN_MINUTES:
                        eligible_hours = min(halt_hours, self.TRANSIT_MAX_HOURS)
                        self.total_transit_hours += eligible_hours
                        
                        self.transit_events.append({
                            'date': self.logbook.normalize_date(date),
                            'station': prev_arr,
                            'prev_arr': prev_flight.arrival_time,
                            'next_dep': curr_flight.departure_time,
                            'halt_hours': halt_hours,
                            'eligible_hours': eligible_hours
                        })
                except ValueError:
                    continue
        
        return self.total_transit_hours
    
    def get_formatted_details(self) -> List[AllowanceDetail]:
        """Return AllowanceDetail objects with transit details."""
        details = []
        for event in self.transit_events:
            description = (
                f"{event['station']} | "
                f"arr {event['prev_arr']} → dep {event['next_dep']} | "
                f"Halt: {event['halt_hours']:.1f}h → Eligible: {event['eligible_hours']:.1f}h"
            )
            details.append(AllowanceDetail(
                date=event['date'],
                description=description
            ))
        return details


class AllowanceCalculator:
    """
    Main calculator that orchestrates all allowance calculations.
    
    Uses:
        - PDFScheduleParser for schedule data (layovers, deadhead)
        - LogbookParser for accurate calculations (tail-swap, night, transit)
    """
    
    def __init__(self, pdf_parser: PDFScheduleParser, 
                 logbook_parser: Optional[LogbookParser] = None):
        self.pdf_parser = pdf_parser
        self.logbook_parser = logbook_parser
        self.breakdown = AllowanceBreakdown()
        self.rank = pdf_parser.pilot_info.rank if pdf_parser.pilot_info else 'CP'
        
        # Initialize specialized calculators if logbook is available
        self.tail_swap_detector: Optional[TailSwapDetector] = None
        self.night_hours_calculator: Optional[NightHoursCalculator] = None
        self.transit_calculator: Optional[TransitCalculator] = None
        
        if logbook_parser:
            self.tail_swap_detector = TailSwapDetector(logbook_parser)
            self.night_hours_calculator = NightHoursCalculator(logbook_parser)
            self.transit_calculator = TransitCalculator(logbook_parser)
    
    def calculate_all(self) -> AllowanceBreakdown:
        """
        Calculate all allowances and return the breakdown.
        
        Returns:
            AllowanceBreakdown with all calculated values
        """
        self._calculate_tail_swap()
        self._calculate_transit()
        self._calculate_layover()
        self._calculate_deadhead()
        self._calculate_night()
        self.breakdown.calculate_total()
        return self.breakdown
    
    def _calculate_tail_swap(self) -> None:
        """Calculate tail-swap allowance using logbook data."""
        if self.tail_swap_detector:
            tail_swaps = self.tail_swap_detector.detect_tail_swaps()
            self.breakdown.tail_swap_count = len(tail_swaps)
            self.breakdown.tail_swap_amount = (
                len(tail_swaps) * RATES['tail_swap'][self.rank]
            )
            self.breakdown.tail_swap_details = self.tail_swap_detector.get_formatted_details()
        else:
            self.breakdown.tail_swap_details.append(AllowanceDetail(
                date="",
                description="[Provide JarfclrpReport for tail-swap calculation]"
            ))
    
    def _calculate_transit(self) -> None:
        """Calculate transit allowance using logbook data."""
        if self.transit_calculator:
            total_hours = self.transit_calculator.calculate_transit()
            self.breakdown.transit_hours = total_hours
            self.breakdown.transit_amount = (
                total_hours * RATES['transit_per_hour'][self.rank]
            )
            self.breakdown.transit_details = self.transit_calculator.get_formatted_details()
        else:
            self.breakdown.transit_details.append(AllowanceDetail(
                date="",
                description="[Provide JarfclrpReport for transit calculation]"
            ))
    
    def _calculate_layover(self) -> None:
        """Calculate domestic layover allowance from PDF schedule."""
        international_skipped = []
        
        for layover in self.pdf_parser.layovers:
            # Get the layover date (use first date from dates list or check_in date)
            layover_date = ""
            if layover.dates and len(layover.dates) > 0:
                layover_date = layover.dates[0]
            elif layover.check_in:
                layover_date = layover.check_in.strftime("%d/%m/%Y")
            
            # Skip international airports
            if not layover.is_domestic:
                if layover.duration_hours >= 10.017:
                    international_skipped.append({
                        'date': layover_date,
                        'description': f"{layover.station}: {layover.duration_hours:.1f} hrs (INTERNATIONAL)"
                    })
                continue
            
            # Minimum 10:01 hours for layover allowance
            if layover.duration_hours >= 10.017:
                self.breakdown.layover_count += 1
                self.breakdown.layover_base_amount += RATES['layover_base'][self.rank]
                
                # Format times for display
                check_in_str = (
                    layover.check_in.strftime("%d/%m %H:%M") 
                    if layover.check_in else "N/A"
                )
                check_out_str = (
                    layover.check_out.strftime("%d/%m %H:%M") 
                    if layover.check_out else "N/A"
                )
                
                description = (
                    f"{layover.station}: {layover.duration_hours:.1f} hrs "
                    f"({check_in_str} → {check_out_str})"
                )
                
                # Extra allowance for layovers > 24 hours
                if layover.duration_hours > 24:
                    extra_hours = layover.duration_hours - 24
                    self.breakdown.layover_extra_hours += extra_hours
                    extra_amount = extra_hours * RATES['layover_extra_per_hour'][self.rank]
                    self.breakdown.layover_extra_amount += extra_amount
                    description += f" = ₹{RATES['layover_base'][self.rank]:,} + ₹{extra_amount:,.0f}"
                else:
                    description += f" = ₹{RATES['layover_base'][self.rank]:,}"
                
                self.breakdown.layover_details.append(AllowanceDetail(
                    date=layover_date,
                    description=description
                ))
        
        # Note about skipped international layovers
        for skipped in international_skipped:
            self.breakdown.layover_details.append(AllowanceDetail(
                date=skipped['date'],
                description=f"[INTL EXCLUDED] {skipped['description']}"
            ))
        
        self.breakdown.layover_total = (
            self.breakdown.layover_base_amount + 
            self.breakdown.layover_extra_amount
        )
    
    def _calculate_deadhead(self) -> None:
        """Calculate deadhead allowance from PDF schedule and logbook."""
        deadhead_flights = [
            f for f in self.pdf_parser.flight_duties if f.is_deadhead
        ]
        
        # If summary has deadhead hours, use that
        if self.pdf_parser.deadhead_hours_total > 0:
            self.breakdown.deadhead_hours = self.pdf_parser.deadhead_hours_total
            for f in deadhead_flights:
                self.breakdown.deadhead_details.append(AllowanceDetail(
                    date=f.date,
                    description=f"Flight {f.duty_code} (Deadhead)"
                ))
        else:
            # Estimate deadhead hours from logbook
            # When a pilot deadheads to a station, the first operating flight
            # FROM that station in the logbook gives us an approximate block time
            self._estimate_deadhead_from_logbook(deadhead_flights)
        
        self.breakdown.deadhead_amount = (
            self.breakdown.deadhead_hours * 
            RATES['deadhead_per_block_hour'][self.rank]
        )
    
    def _estimate_deadhead_from_logbook(self, deadhead_flights: List) -> None:
        """Estimate deadhead block times from logbook data.
        
        When a pilot deadheads to station X, they will have an operating flight
        FROM station X in the logbook. We detect this by finding gaps where:
        - The departure airport doesn't match the previous flight's arrival
        - Or it's the first flight and not from home base
        
        We use that flight's block time as an estimate for the deadhead sector.
        """
        if not self.logbook_parser:
            for f in deadhead_flights:
                self.breakdown.deadhead_details.append(AllowanceDetail(
                    date=f.date,
                    description=f"Flight {f.duty_code} (Deadhead - no logbook for estimation)"
                ))
            return
        
        # Get pilot's home base
        home_base = self.pdf_parser.pilot_info.base if self.pdf_parser.pilot_info else "DEL"
        
        total_deadhead_hours = 0.0
        flights_by_date = self.logbook_parser.get_flights_by_date()
        deadhead_destinations = []  # Track which destinations we've matched
        
        # First, identify all deadhead destinations from the logbook
        # by finding gaps in the flight sequence
        for date, flights in flights_by_date.items():
            sorted_flights = sorted(flights, key=lambda f: f.departure_time)
            
            for i, flight in enumerate(sorted_flights):
                dep_airport = flight.departure_airport.strip().upper()
                
                if i == 0:
                    # First flight of the day - if not from home base, likely deadheaded there
                    if dep_airport != home_base:
                        deadhead_destinations.append({
                            'date': date,
                            'destination': dep_airport,
                            'block_time': flight.flight_time
                        })
                else:
                    # Check if there's a gap (previous arrival != current departure)
                    prev_arrival = sorted_flights[i-1].arrival_airport.strip().upper()
                    if prev_arrival != dep_airport:
                        # Gap found - pilot must have deadheaded to this airport
                        deadhead_destinations.append({
                            'date': date,
                            'destination': dep_airport,
                            'block_time': flight.flight_time
                        })
        
        # Match deadhead flights with identified gaps
        for dh_flight in deadhead_flights:
            dh_date = dh_flight.date
            # Convert DD/MM/YYYY to DD/MM/YY for matching
            if len(dh_date) == 10:
                parts = dh_date.split('/')
                dh_date_short = f"{parts[0]}/{parts[1]}/{parts[2][2:]}"
            else:
                dh_date_short = dh_date
            
            # Find a matching gap for this deadhead date
            matched = False
            for gap in deadhead_destinations:
                if gap['date'] == dh_date_short:
                    block_time_str = gap['block_time']
                    estimated_hours = self._parse_block_time(block_time_str)
                    
                    if estimated_hours > 0:
                        total_deadhead_hours += estimated_hours
                        self.breakdown.deadhead_details.append(AllowanceDetail(
                            date=dh_flight.date,
                            description=f"Flight {dh_flight.duty_code} to {gap['destination']} (~{block_time_str} estimated)"
                        ))
                        matched = True
                        # Remove this gap so we don't match it again
                        deadhead_destinations.remove(gap)
                        break
            
            if not matched:
                # Fallback: use first flight of the day
                logbook_flights = flights_by_date.get(dh_date_short, [])
                if logbook_flights:
                    first_flight = logbook_flights[0]
                    block_time_str = first_flight.flight_time
                    estimated_hours = self._parse_block_time(block_time_str)
                    if estimated_hours > 0:
                        total_deadhead_hours += estimated_hours
                        dep_airport = first_flight.departure_airport.strip()
                        self.breakdown.deadhead_details.append(AllowanceDetail(
                            date=dh_flight.date,
                            description=f"Flight {dh_flight.duty_code} to {dep_airport} (~{block_time_str} estimated)"
                        ))
                    else:
                        self.breakdown.deadhead_details.append(AllowanceDetail(
                            date=dh_flight.date,
                            description=f"Flight {dh_flight.duty_code} (Deadhead - could not parse block time)"
                        ))
                else:
                    self.breakdown.deadhead_details.append(AllowanceDetail(
                        date=dh_flight.date,
                        description=f"Flight {dh_flight.duty_code} (Deadhead - no logbook data for date)"
                    ))
        
        self.breakdown.deadhead_hours = total_deadhead_hours
        
        self.breakdown.deadhead_hours = total_deadhead_hours
    
    def _parse_block_time(self, time_str: str) -> float:
        """Parse block time string (HH:MM) to decimal hours."""
        if not time_str:
            return 0.0
        try:
            time_str = time_str.strip()
            if ':' in time_str:
                parts = time_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0
                return hours + minutes / 60.0
        except (ValueError, IndexError):
            pass
        return 0.0
    
    def _calculate_night(self) -> None:
        """Calculate night allowance using logbook data."""
        if self.night_hours_calculator:
            total_night_hours = self.night_hours_calculator.calculate_night_hours()
            self.breakdown.night_hours = total_night_hours
            self.breakdown.night_amount = (
                total_night_hours * RATES['night_per_hour'][self.rank]
            )
            self.breakdown.night_details = self.night_hours_calculator.get_formatted_details()
        else:
            self.breakdown.night_details.append(AllowanceDetail(
                date="",
                description="[Provide JarfclrpReport for night hour calculation]"
            ))

