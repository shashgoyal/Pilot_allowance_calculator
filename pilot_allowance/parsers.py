"""
Parsers for reading pilot schedule and logbook files.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

import xlrd

from .models import (
    PilotInfo, FlightDuty, LogbookFlight, 
    TrainingDuty, Layover
)
from .constants import is_domestic_airport

# Try to import pdfplumber for PDF parsing
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


class PDFScheduleParser:
    """
    Parses the ScheduleReport.pdf file to extract all schedule data.
    This is the primary parser for schedule information.
    
    Extracts:
        - Pilot information (name, rank, base, etc.)
        - Summary statistics (block hours, duty hours, etc.)
        - Flight duties with crew details
        - Training duties
        - Layover information from transfer details
    """
    
    def __init__(self, file_path: str):
        if not PDF_SUPPORT:
            raise ImportError(
                "pdfplumber is required for PDF parsing. "
                "Install with: pip install pdfplumber"
            )
        
        self.file_path = file_path
        self.pilot_info: Optional[PilotInfo] = None
        self.summary_stats: Dict[str, str] = {}
        self.flight_duties: List[FlightDuty] = []
        self.training_duties: List[TrainingDuty] = []
        self.layovers: List[Layover] = []
        self.deadhead_hours_total: float = 0.0
        self.year: int = 2025
        
    def parse(self) -> None:
        """Parse the PDF schedule file and extract all data."""
        with pdfplumber.open(self.file_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            self._parse_pilot_info(full_text)
            self._parse_summary_stats(full_text)
            self._parse_crew_details(full_text)
            self._parse_training_duties(full_text)
            self._parse_layovers(full_text)
    
    def _parse_pilot_info(self, text: str) -> None:
        """Extract pilot info from PDF text."""
        # Pattern: "16612 GOYAL, VINEET DEL,CP,320"
        match = re.search(
            r'(\d{5})\s+([A-Z]+),\s*([A-Z]+)\s+(\w{3}),(\w{2}),(\w{3})', 
            text
        )
        if match:
            self.pilot_info = PilotInfo(
                employee_id=match.group(1),
                name=f"{match.group(2)}, {match.group(3)}",
                base=match.group(4),
                rank=match.group(5),
                aircraft_type=match.group(6)
            )
        
        # Extract date range for year
        date_match = re.search(
            r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})', 
            text
        )
        if date_match:
            start_date = date_match.group(1)
            self.year = int(start_date.split('/')[2])
    
    def _parse_summary_stats(self, text: str) -> None:
        """Extract summary statistics from PDF."""
        # Initialize with defaults
        self.summary_stats = {
            'block_hours': '',
            'duty_hours': '',
            'deadhead_hours': '',
            'off_days': '',
            'standby_days': '',
            'flight_days': '',
            'training_days': '',
            'landings': '',
        }
        
        # Try multiple patterns for different PDF formats
        # Pattern 1: Full stats line with headers
        stats_pattern = (
            r'Block Hours\s+Duty Hours\s+Dead Head Hours.*?'
            r'(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+'
            r'(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
        )
        match = re.search(stats_pattern, text, re.DOTALL)
        
        if match:
            self.summary_stats = {
                'block_hours': match.group(1),
                'duty_hours': match.group(2),
                'deadhead_hours': match.group(3),
                'off_days': match.group(4),
                'standby_days': match.group(5),
                'flight_days': match.group(6),
                'training_days': match.group(7),
                'landings': match.group(8),
            }
            self.deadhead_hours_total = self._parse_time_to_hours(match.group(3))
            return
        
        # Pattern 2: Try to find individual values if table format is different
        # Look for block hours pattern
        block_match = re.search(r'Block\s*Hours?\s*[:\s]+(\d+:\d+)', text, re.IGNORECASE)
        if block_match:
            self.summary_stats['block_hours'] = block_match.group(1)
        
        # Look for duty hours pattern
        duty_match = re.search(r'Duty\s*Hours?\s*[:\s]+(\d+:\d+)', text, re.IGNORECASE)
        if duty_match:
            self.summary_stats['duty_hours'] = duty_match.group(1)
        
        # Look for deadhead hours pattern
        deadhead_match = re.search(r'Dead\s*Head\s*Hours?\s*[:\s]+(\d+:\d+)', text, re.IGNORECASE)
        if deadhead_match:
            self.summary_stats['deadhead_hours'] = deadhead_match.group(1)
            self.deadhead_hours_total = self._parse_time_to_hours(deadhead_match.group(1))
        
        # Look for off days pattern
        off_match = re.search(r'Off\s*Days?\s*[:\s]+(\d+)', text, re.IGNORECASE)
        if off_match:
            self.summary_stats['off_days'] = off_match.group(1)
        
        # Look for standby days pattern
        standby_match = re.search(r'Stand\s*[Bb]y\s*Days?\s*[:\s]+(\d+)', text, re.IGNORECASE)
        if standby_match:
            self.summary_stats['standby_days'] = standby_match.group(1)
        
        # Pattern 3: Short format without Dead Head Hours and Standby Days
        # (e.g., OctSchedule.pdf format)
        # Header: Block Hours | Duty Hours | Off Days | Flight Days | Training Days | Landings
        # Format: HH:MM HH:MM N N N N
        short_stats_pattern = (
            r'Block Hours\s+Duty Hours\s+Off Days\s+Flight Days\s+Training Days\s+Landings.*?'
            r'(\d{1,3}:\d{2})\s+(\d{1,3}:\d{2})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
        )
        short_match = re.search(short_stats_pattern, text, re.DOTALL)
        
        if short_match and not self.summary_stats.get('block_hours'):
            self.summary_stats = {
                'block_hours': short_match.group(1),
                'duty_hours': short_match.group(2),
                'deadhead_hours': '',  # Not present in this format
                'off_days': short_match.group(3),
                'standby_days': '',  # Not present in this format
                'flight_days': short_match.group(4),
                'training_days': short_match.group(5),
                'landings': short_match.group(6),
            }
            return
        
        # Pattern 4: Try to find a row of time values followed by numbers (8 columns)
        # Format: HH:MM HH:MM HH:MM N N N N N
        row_pattern = r'(\d{1,3}:\d{2})\s+(\d{1,3}:\d{2})\s+(\d{1,3}:\d{2})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
        row_match = re.search(row_pattern, text)
        
        if row_match and not self.summary_stats.get('block_hours'):
            self.summary_stats = {
                'block_hours': row_match.group(1),
                'duty_hours': row_match.group(2),
                'deadhead_hours': row_match.group(3),
                'off_days': row_match.group(4),
                'standby_days': row_match.group(5),
                'flight_days': row_match.group(6),
                'training_days': row_match.group(7),
                'landings': row_match.group(8),
            }
            self.deadhead_hours_total = self._parse_time_to_hours(row_match.group(3))
            return
        
        # Pattern 5: Try to find a row with 6 values (short format without headers match)
        # Format: HH:MM HH:MM N N N N
        short_row_pattern = r'(\d{1,3}:\d{2})\s+(\d{1,3}:\d{2})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
        short_row_match = re.search(short_row_pattern, text)
        
        if short_row_match and not self.summary_stats.get('block_hours'):
            self.summary_stats = {
                'block_hours': short_row_match.group(1),
                'duty_hours': short_row_match.group(2),
                'deadhead_hours': '',
                'off_days': short_row_match.group(3),
                'standby_days': '',
                'flight_days': short_row_match.group(4),
                'training_days': short_row_match.group(5),
                'landings': short_row_match.group(6),
            }
    
    def _parse_time_to_hours(self, time_str: str) -> float:
        """Convert HH:MM format to decimal hours."""
        if not time_str:
            return 0.0
        try:
            if ':' in time_str:
                parts = time_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0
                return hours + minutes / 60.0
        except (ValueError, IndexError):
            pass
        return 0.0
    
    def _parse_crew_details(self, text: str) -> None:
        """
        Parse crew details section to identify operating and deadhead flights.
        """
        if not self.pilot_info:
            return
        
        emp_id = self.pilot_info.employee_id
        lines = text.split('\n')
        
        current_date = None
        current_duty = None
        crew_buffer = ""
        
        for line in lines:
            line = line.strip()
            
            # Check for date and duty code at start of line
            match = re.match(
                r'^(\d{2}/\d{2}/\d{4})\s+(\d+|SBY|OFG|SCK)\s*(.*)', 
                line
            )
            if match:
                # Save previous flight if exists
                if current_date and current_duty:
                    self._add_flight_duty(current_date, current_duty, crew_buffer, emp_id)
                
                current_date = match.group(1)
                current_duty = match.group(2)
                crew_buffer = match.group(3)
                continue
            
            # Continue accumulating crew details
            if current_date and current_duty:
                if any(x in line for x in ['CP -', 'FO -', 'LD -', 'CA -']):
                    crew_buffer += " " + line
                elif line.startswith(('Training Details', 'Hotel Information', 
                                      'Transfer Information', 'Pax Transfer')):
                    self._add_flight_duty(current_date, current_duty, crew_buffer, emp_id)
                    current_date = None
                    current_duty = None
                    crew_buffer = ""
                    break
        
        # Save last flight if any
        if current_date and current_duty:
            self._add_flight_duty(current_date, current_duty, crew_buffer, emp_id)
    
    def _add_flight_duty(self, date: str, duty_code: str, 
                         crew_details: str, emp_id: str) -> None:
        """Add a flight duty entry to the list."""
        # Skip non-flight duties
        if duty_code in ['SBY', 'OFG', 'SCK', 'VCBM']:
            return
        
        is_operating = f'PIC - {emp_id}' in crew_details
        is_deadhead = f'DHF - {emp_id}' in crew_details
        
        flight = FlightDuty(
            date=date,
            duty_code=duty_code,
            crew_details=crew_details,
            is_operating=is_operating,
            is_deadhead=is_deadhead
        )
        self.flight_duties.append(flight)
    
    def _parse_training_duties(self, text: str) -> None:
        """Parse training duties from PDF."""
        training_section = re.search(
            r'Training Details.*?(?=Hotel Information|Transfer Information|$)', 
            text, 
            re.DOTALL
        )
        if not training_section:
            return
        
        training_text = training_section.group(0)
        
        # Pattern: DD/MM/YYYY HHMM - HHMM TRAINING_TYPE
        pattern = (
            r'(\d{2}/\d{2}/\d{4})\s+(\d{4})\s*-\s*(\d{4})\s+'
            r'(.*?)(?=\d{2}/\d{2}/\d{4}|Generated|$)'
        )
        matches = re.findall(pattern, training_text)
        
        for match in matches:
            date_str = match[0]
            time_range = f"{match[1]} - {match[2]}"
            duty_type = match[3].strip()
            
            training = TrainingDuty(
                date=date_str,
                time_range=time_range,
                duty_type=duty_type,
                crew=""
            )
            
            # Parse times
            try:
                training.start_time = datetime.strptime(
                    f"{date_str} {match[1]}", "%d/%m/%Y %H%M"
                )
                training.end_time = datetime.strptime(
                    f"{date_str} {match[2]}", "%d/%m/%Y %H%M"
                )
                if training.end_time < training.start_time:
                    training.end_time += timedelta(days=1)
            except ValueError:
                pass
            
            self.training_duties.append(training)
    
    def _parse_layovers(self, text: str) -> None:
        """
        Parse layover information from transfer details.
        
        Transfer Information format:
        Airport to Hotel: DD/MM/YYYY HH:MM TRANSPORT_NAME
        Hotel to Airport: DD/MM/YYYY HH:MM TRANSPORT_NAME
        """
        transfers = []
        
        # Pattern for transfer entries
        arrival_pattern = (
            r'Airport to Hotel:\s*(\d{2}/\d{2}/\d{4})\s+'
            r'(\d{2}:\d{2})\s+(\w+)'
        )
        departure_pattern = (
            r'Hotel to Airport:\s*(\d{2}/\d{2}/\d{4})\s+'
            r'(\d{2}:\d{2})\s+(\w+)'
        )
        
        # Parse arrivals
        for match in re.finditer(arrival_pattern, text):
            date_str, time_str, transport = match.groups()
            location = transport[:3].upper() if len(transport) >= 3 else transport.upper()
            
            try:
                dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
                transfers.append({
                    'location': location,
                    'type': 'arrival',
                    'date': date_str,
                    'datetime': dt
                })
            except ValueError:
                continue
        
        # Parse departures
        for match in re.finditer(departure_pattern, text):
            date_str, time_str, transport = match.groups()
            location = transport[:3].upper() if len(transport) >= 3 else transport.upper()
            
            try:
                dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
                transfers.append({
                    'location': location,
                    'type': 'departure',
                    'date': date_str,
                    'datetime': dt
                })
            except ValueError:
                continue
        
        # Group transfers by location
        location_events = defaultdict(list)
        for event in transfers:
            location_events[event['location']].append(event)
        
        # Create layovers
        for location, events in location_events.items():
            arrivals = [e for e in events if e['type'] == 'arrival']
            departures = [e for e in events if e['type'] == 'departure']
            
            if not arrivals or not departures:
                continue
            
            arrivals.sort(key=lambda x: x['datetime'])
            departures.sort(key=lambda x: x['datetime'])
            
            first_arrival = arrivals[0]['datetime']
            last_departure = departures[-1]['datetime']
            
            if last_departure > first_arrival:
                duration = last_departure - first_arrival
                duration_hours = duration.total_seconds() / 3600
            else:
                duration_hours = 0
            
            all_dates = list(set([e['date'] for e in events]))
            is_domestic = is_domestic_airport(location)
            
            layover = Layover(
                station=location,
                dates=all_dates,
                check_in=first_arrival,
                check_out=last_departure,
                duration_hours=duration_hours,
                is_domestic=is_domestic
            )
            
            self.layovers.append(layover)


class LogbookParserBase:
    """
    Base class for logbook parsers.
    Defines the common interface for both XLS and PDF logbook parsers.
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.flights: List[LogbookFlight] = []
        self.pilot_name: str = ""
    
    def parse(self) -> None:
        """Parse the logbook file and extract flight data."""
        raise NotImplementedError
    
    def get_flights_by_date(self) -> Dict[str, List[LogbookFlight]]:
        """Group flights by date for easier processing."""
        flights_by_date = defaultdict(list)
        for flight in self.flights:
            flights_by_date[flight.date].append(flight)
        return dict(flights_by_date)
    
    def normalize_date(self, date_str: str) -> str:
        """
        Normalize date format DD/MM/YY to DD/MM/YYYY.
        
        Args:
            date_str: Date in DD/MM/YY or DD/MM/YYYY format
            
        Returns:
            Date in DD/MM/YYYY format
        """
        if re.match(r'\d{2}/\d{2}/\d{2}$', date_str):
            parts = date_str.split('/')
            return f"{parts[0]}/{parts[1]}/20{parts[2]}"
        elif re.match(r'\d{2}/\d{2}/\d{4}$', date_str):
            # Already in full format, convert to short for consistency
            parts = date_str.split('/')
            return date_str
        return date_str


class LogbookParser(LogbookParserBase):
    """
    Parses the JarfclrpReport.xls (Pilot Logbook) file.
    Contains detailed flight information for accurate calculations.
    
    Used for:
        - Tail-swap detection (aircraft registrations)
        - Night hours calculation (actual flight times)
        - Transit calculation (actual halt times)
    """
    
    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.workbook = xlrd.open_workbook(file_path)
        self.sheet = self.workbook.sheet_by_index(0)
        
    def parse(self) -> None:
        """Parse the logbook file and extract flight data."""
        self._parse_pilot_info()
        self._parse_flights()
    
    def _parse_pilot_info(self) -> None:
        """Extract pilot info from header."""
        for row_idx in range(min(15, self.sheet.nrows)):
            val = self.sheet.cell_value(row_idx, 0)
            if isinstance(val, str) and re.match(r'\d{5}\s+\w+', val):
                self.pilot_name = val
                break
    
    def _parse_flights(self) -> None:
        """Parse individual flight entries from the logbook."""
        # Column mapping:
        # 0: Date (DD/MM/YY)
        # 1: Departure Airport
        # 2: Departure Time
        # 3: Arrival Airport
        # 4: Arrival Time
        # 6: Aircraft Type
        # 7: Aircraft Registration
        # 8: Flight Time
        # 9: PIC Name
        
        for row_idx in range(self.sheet.nrows):
            date_val = self.sheet.cell_value(row_idx, 0)
            
            # Check for flight row (starts with date in DD/MM/YY format)
            if isinstance(date_val, str) and re.match(r'\d{2}/\d{2}/\d{2}$', date_val.strip()):
                try:
                    flight = LogbookFlight(
                        date=str(date_val).strip(),
                        departure_airport=str(self.sheet.cell_value(row_idx, 1)).strip(),
                        departure_time=str(self.sheet.cell_value(row_idx, 2)).strip(),
                        arrival_airport=str(self.sheet.cell_value(row_idx, 3)).strip(),
                        arrival_time=str(self.sheet.cell_value(row_idx, 4)).strip(),
                        aircraft_type=str(self.sheet.cell_value(row_idx, 6)).strip(),
                        aircraft_reg=str(self.sheet.cell_value(row_idx, 7)).strip(),
                        flight_time=str(self.sheet.cell_value(row_idx, 8)).strip(),
                        pic_name=str(self.sheet.cell_value(row_idx, 9)).strip(),
                    )
                    self.flights.append(flight)
                except (ValueError, IndexError):
                    continue


class LogbookPDFParser(LogbookParserBase):
    """
    Parses the JarfclrpReport.pdf (Pilot Logbook) file.
    PDF version of the logbook parser.
    
    Expected PDF format (InterGlobe Aviation Pilot Logbook):
        Date | Airport | Time | Airport | Time | Type | Reg. | Flt time | Name PIC | ...
        
    Used for:
        - Tail-swap detection (aircraft registrations)
        - Night hours calculation (actual flight times)
        - Transit calculation (actual halt times)
    """
    
    def __init__(self, file_path: str):
        if not PDF_SUPPORT:
            raise ImportError(
                "pdfplumber is required for PDF parsing. "
                "Install with: pip install pdfplumber"
            )
        super().__init__(file_path)
        
    def parse(self) -> None:
        """Parse the PDF logbook file and extract flight data."""
        with pdfplumber.open(self.file_path) as pdf:
            # Extract text and parse using regex (more reliable for this format)
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # Parse using text patterns
            self._parse_text(full_text)
            
            # If no flights found, try table extraction
            if not self.flights:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            self._parse_table(table)
    
    def _parse_text(self, text: str) -> None:
        """
        Parse logbook data from text.
        The InterGlobe Aviation Pilot Logbook format:
        DD/MM/YY AIRPORT HH:MM AIRPORT HH:MM TYPE REGISTRATION HH:MM PIC_NAME ...
        
        Example line:
        01/12/25 NAG 13:18 DEL 15:03 321 VTIWN 01:45 GOYAL, VINEET 1 1 01:45 01:45
        """
        # Extract pilot name from header
        pilot_match = re.search(r'(\d{5})\s+([A-Z]+,\s*[A-Z]+)', text)
        if pilot_match:
            self.pilot_name = f"{pilot_match.group(1)} {pilot_match.group(2)}"
        
        # Pattern for flight entries in this specific format
        # DD/MM/YY AIRPORT HH:MM AIRPORT HH:MM TYPE REG HH:MM NAME ...
        flight_pattern = (
            r'(\d{2}/\d{2}/\d{2})\s+'           # Date (DD/MM/YY)
            r'([A-Z]{3})\s+'                     # Departure Airport
            r'(\d{2}:\d{2})\s+'                  # Departure Time
            r'([A-Z]{3})\s+'                     # Arrival Airport
            r'(\d{2}:\d{2})\s+'                  # Arrival Time
            r'(\d{3})\s+'                        # Aircraft Type (320, 321)
            r'(VT[A-Z]{2,4})\s+'                 # Aircraft Registration (VTIWN)
            r'(\d{2}:\d{2})\s+'                  # Flight Time
            r'([A-Z]+,\s*[A-Z]+)'                # PIC Name
        )
        
        for match in re.finditer(flight_pattern, text):
            try:
                flight = LogbookFlight(
                    date=match.group(1),
                    departure_airport=match.group(2),
                    departure_time=match.group(3),
                    arrival_airport=match.group(4),
                    arrival_time=match.group(5),
                    aircraft_type=match.group(6),
                    aircraft_reg=match.group(7),
                    flight_time=match.group(8),
                    pic_name=match.group(9),
                )
                self.flights.append(flight)
            except (ValueError, IndexError):
                continue
        
        # Fallback: simpler pattern without flight time and PIC name
        if not self.flights:
            simple_pattern = (
                r'(\d{2}/\d{2}/\d{2})\s+'       # Date
                r'([A-Z]{3})\s+'                 # Departure Airport
                r'(\d{2}:\d{2})\s+'              # Departure Time
                r'([A-Z]{3})\s+'                 # Arrival Airport
                r'(\d{2}:\d{2})\s+'              # Arrival Time
                r'(\d{3})\s+'                    # Aircraft Type
                r'(VT[A-Z]{2,4})'                # Aircraft Registration
            )
            for match in re.finditer(simple_pattern, text):
                try:
                    flight = LogbookFlight(
                        date=match.group(1),
                        departure_airport=match.group(2),
                        departure_time=match.group(3),
                        arrival_airport=match.group(4),
                        arrival_time=match.group(5),
                        aircraft_type=match.group(6),
                        aircraft_reg=match.group(7),
                        flight_time="",
                        pic_name="",
                    )
                    self.flights.append(flight)
                except (ValueError, IndexError):
                    continue
    
    def _parse_table(self, table: List[List]) -> None:
        """Parse a table extracted from the PDF."""
        if not table or len(table) < 2:
            return
        
        for row in table:
            if not row or len(row) < 7:
                continue
            
            # Clean cells
            cells = [str(cell).strip() if cell else "" for cell in row]
            
            # Find date column
            date_val = None
            date_col = -1
            
            for i, cell in enumerate(cells):
                if re.match(r'\d{2}/\d{2}/\d{2}$', cell):
                    date_val = cell
                    date_col = i
                    break
            
            if not date_val or date_col < 0:
                continue
            
            try:
                # Fixed column positions relative to date column:
                # +1: Departure Airport
                # +2: Departure Time
                # +3: Arrival Airport
                # +4: Arrival Time
                # +5: Aircraft Type
                # +6: Aircraft Registration
                # +7: Flight Time
                # +8: PIC Name
                
                dep_airport = cells[date_col + 1] if len(cells) > date_col + 1 else ""
                dep_time = cells[date_col + 2] if len(cells) > date_col + 2 else ""
                arr_airport = cells[date_col + 3] if len(cells) > date_col + 3 else ""
                arr_time = cells[date_col + 4] if len(cells) > date_col + 4 else ""
                aircraft_type = cells[date_col + 5] if len(cells) > date_col + 5 else ""
                aircraft_reg = cells[date_col + 6] if len(cells) > date_col + 6 else ""
                flight_time = cells[date_col + 7] if len(cells) > date_col + 7 else ""
                pic_name = cells[date_col + 8] if len(cells) > date_col + 8 else ""
                
                # Validate required fields
                if not dep_time or not arr_time:
                    continue
                if not re.match(r'\d{2}:\d{2}', dep_time):
                    continue
                if not re.match(r'\d{2}:\d{2}', arr_time):
                    continue
                
                flight = LogbookFlight(
                    date=date_val,
                    departure_airport=dep_airport.strip(),
                    departure_time=dep_time.strip(),
                    arrival_airport=arr_airport.strip(),
                    arrival_time=arr_time.strip(),
                    aircraft_type=aircraft_type.strip(),
                    aircraft_reg=aircraft_reg.strip().upper(),
                    flight_time=flight_time.strip(),
                    pic_name=pic_name.strip(),
                )
                self.flights.append(flight)
                
            except (ValueError, IndexError):
                continue


def create_logbook_parser(file_path: str) -> LogbookParserBase:
    """
    Factory function to create the appropriate logbook parser
    based on file extension.
    
    Args:
        file_path: Path to the logbook file (.xls or .pdf)
        
    Returns:
        LogbookParser for XLS files, LogbookPDFParser for PDF files
    """
    file_path_lower = file_path.lower()
    
    if file_path_lower.endswith('.pdf'):
        return LogbookPDFParser(file_path)
    elif file_path_lower.endswith('.xls') or file_path_lower.endswith('.xlsx'):
        return LogbookParser(file_path)
    else:
        # Try to detect by content or default to PDF
        raise ValueError(
            f"Unsupported file format: {file_path}. "
            "Expected .pdf or .xls file."
        )

