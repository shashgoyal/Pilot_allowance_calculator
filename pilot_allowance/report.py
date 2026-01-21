"""
Report generation for Pilot Allowance Calculator.
"""

from .models import AllowanceBreakdown, AllowanceDetail
from .constants import RATES
from .parsers import PDFScheduleParser


def _format_detail(detail: AllowanceDetail) -> str:
    """Format an AllowanceDetail object as a string for the report."""
    if detail.date:
        return f"{detail.date}: {detail.description}"
    return detail.description


def generate_report(pdf_parser: PDFScheduleParser, 
                    breakdown: AllowanceBreakdown) -> str:
    """
    Generate a formatted allowance report.
    
    Args:
        pdf_parser: Parsed PDF schedule data
        breakdown: Calculated allowance breakdown
        
    Returns:
        Formatted report as a string
    """
    pilot = pdf_parser.pilot_info
    rank_name = "Captain" if pilot.rank == 'CP' else "First Officer"
    
    report = []
    
    # Header
    report.append("=" * 70)
    report.append("         PILOT ALLOWANCE CALCULATION REPORT")
    report.append("         Effective 1st January 2026")
    report.append("=" * 70)
    report.append("")
    
    # Pilot Information
    report.append("PILOT INFORMATION")
    report.append("-" * 40)
    report.append(f"Employee ID    : {pilot.employee_id}")
    report.append(f"Name           : {pilot.name}")
    report.append(f"Rank           : {rank_name} ({pilot.rank})")
    report.append(f"Base           : {pilot.base}")
    report.append(f"Aircraft Type  : {pilot.aircraft_type}")
    report.append("")
    
    # Summary Statistics
    report.append("SCHEDULE SUMMARY")
    report.append("-" * 40)
    if pdf_parser.summary_stats:
        for key, value in pdf_parser.summary_stats.items():
            formatted_key = key.replace('_', ' ').title()
            report.append(f"{formatted_key:20}: {value}")
    
    operating_count = len([f for f in pdf_parser.flight_duties if f.is_operating])
    deadhead_count = len([f for f in pdf_parser.flight_duties if f.is_deadhead])
    report.append(f"{'Operating Flights':20}: {operating_count}")
    report.append(f"{'Deadhead Flights':20}: {deadhead_count}")
    report.append(f"{'Layovers':20}: {len(pdf_parser.layovers)}")
    report.append("")
    
    # Allowance Breakdown Header
    report.append("ALLOWANCE BREAKDOWN")
    report.append("=" * 70)
    report.append("")
    
    # 1. Tail-swap Allowance
    report.append("1. TAIL-SWAP ALLOWANCE")
    report.append("-" * 40)
    report.append(f"   Rate: ₹{RATES['tail_swap'][pilot.rank]:,} per tail-swap")
    report.append(f"   Count: {breakdown.tail_swap_count} tail-swap(s)")
    report.append(f"   Amount: ₹{breakdown.tail_swap_amount:,.2f}")
    if breakdown.tail_swap_details:
        report.append("   Details:")
        for detail in breakdown.tail_swap_details:
            formatted = _format_detail(detail)
            if formatted.startswith("["):
                report.append(f"   {formatted}")
            else:
                report.append(f"      • {formatted}")
    report.append("")
    
    # 2. Transit Allowance
    report.append("2. TRANSIT ALLOWANCE (Domestic)")
    report.append("-" * 40)
    report.append(
        f"   Rate: ₹{RATES['transit_per_hour'][pilot.rank]:,} per hour "
        f"(halts > 90 min, max 4 hrs)"
    )
    report.append(f"   Eligible Hours: {breakdown.transit_hours:.2f} hrs")
    report.append(f"   Amount: ₹{breakdown.transit_amount:,.2f}")
    if breakdown.transit_details:
        report.append("   Details:")
        for detail in breakdown.transit_details:
            formatted = _format_detail(detail)
            if formatted.startswith("["):
                report.append(f"   {formatted}")
            else:
                report.append(f"      • {formatted}")
    report.append("")
    
    # 3. Layover Allowance
    report.append("3. DOMESTIC LAYOVER ALLOWANCE")
    report.append("-" * 40)
    report.append(f"   Base Rate (10:01-24 hrs): ₹{RATES['layover_base'][pilot.rank]:,}")
    report.append(
        f"   Extra Rate (>24 hrs): ₹{RATES['layover_extra_per_hour'][pilot.rank]:,}/hour"
    )
    report.append(f"   Layover Count: {breakdown.layover_count}")
    report.append(f"   Base Amount: ₹{breakdown.layover_base_amount:,.2f}")
    if breakdown.layover_extra_hours > 0:
        report.append(f"   Extra Hours: {breakdown.layover_extra_hours:.2f} hrs")
        report.append(f"   Extra Amount: ₹{breakdown.layover_extra_amount:,.2f}")
    report.append(f"   Total: ₹{breakdown.layover_total:,.2f}")
    if breakdown.layover_details:
        report.append("   Details:")
        for detail in breakdown.layover_details:
            formatted = _format_detail(detail)
            report.append(f"      • {formatted}")
    report.append("")
    
    # 4. Deadhead Allowance
    report.append("4. DEADHEAD ALLOWANCE")
    report.append("-" * 40)
    report.append(f"   Rate: ₹{RATES['deadhead_per_block_hour'][pilot.rank]:,} per block hour")
    report.append(f"   Hours: {breakdown.deadhead_hours:.2f} hrs")
    report.append(f"   Amount: ₹{breakdown.deadhead_amount:,.2f}")
    if breakdown.deadhead_details:
        report.append("   Details:")
        for detail in breakdown.deadhead_details:
            formatted = _format_detail(detail)
            report.append(f"      • {formatted}")
    report.append("")
    
    # 5. Night Allowance
    report.append("5. NIGHT ALLOWANCE")
    report.append("-" * 40)
    report.append(f"   Rate: ₹{RATES['night_per_hour'][pilot.rank]:,} per night hour")
    report.append(f"   Night Hours (0000-0600 IST): {breakdown.night_hours:.2f} hrs")
    report.append(f"   Amount: ₹{breakdown.night_amount:,.2f}")
    if breakdown.night_details:
        report.append("   Details:")
        for detail in breakdown.night_details:
            formatted = _format_detail(detail)
            if formatted.startswith("["):
                report.append(f"   {formatted}")
            else:
                report.append(f"      • {formatted}")
    report.append("")
    
    # Grand Total
    report.append("=" * 70)
    report.append("GRAND TOTAL")
    report.append("=" * 70)
    report.append(f"   Tail-swap Allowance    : ₹{breakdown.tail_swap_amount:>12,.2f}")
    report.append(f"   Transit Allowance      : ₹{breakdown.transit_amount:>12,.2f}")
    report.append(f"   Layover Allowance      : ₹{breakdown.layover_total:>12,.2f}")
    report.append(f"   Deadhead Allowance     : ₹{breakdown.deadhead_amount:>12,.2f}")
    report.append(f"   Night Allowance        : ₹{breakdown.night_amount:>12,.2f}")
    report.append("   " + "-" * 35)
    report.append(f"   TOTAL ALLOWANCE        : ₹{breakdown.total_amount:>12,.2f}")
    report.append("=" * 70)
    report.append("")
    
    return "\n".join(report)


def print_report(pdf_parser: PDFScheduleParser, 
                 breakdown: AllowanceBreakdown) -> None:
    """Print the formatted report to stdout."""
    print(generate_report(pdf_parser, breakdown))


def save_report(pdf_parser: PDFScheduleParser, 
                breakdown: AllowanceBreakdown, 
                output_file: str) -> None:
    """
    Save the formatted report to a file.
    
    Args:
        pdf_parser: Parsed PDF schedule data
        breakdown: Calculated allowance breakdown
        output_file: Path to the output file
    """
    report = generate_report(pdf_parser, breakdown)
    with open(output_file, 'w') as f:
        f.write(report)

