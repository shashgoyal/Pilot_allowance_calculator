"""
Main entry point for Pilot Allowance Calculator.

Usage:
    python -m pilot_allowance [schedule.pdf] [logbook.pdf]
    
    or from the parent directory:
    python pilot_allowance/main.py [schedule.pdf] [logbook.pdf]
    
    or simply place both files in the current directory and run:
    python -m pilot_allowance
"""

import os
import sys

# Check for pdfplumber
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

from .parsers import PDFScheduleParser, create_logbook_parser
from .calculators import AllowanceCalculator
from .report import generate_report


def find_files(directory: str = ".") -> tuple:
    """
    Auto-detect schedule PDF and logbook files in directory.
    
    Args:
        directory: Directory to search in
        
    Returns:
        Tuple of (pdf_file, logbook_file) paths or None if not found
    """
    pdf_file = None
    logbook_file = None
    
    # Schedule PDF file patterns
    schedule_patterns = ["ScheduleReport.pdf", "schedule.pdf", "Schedule.pdf"]
    for name in schedule_patterns:
        path = os.path.join(directory, name)
        if os.path.exists(path):
            pdf_file = path
            break
    
    # Logbook file patterns (prefer PDF over XLS)
    logbook_patterns = [
        # PDF patterns first
        "JarfclrpReport.pdf",
        "jarfclrpReport.pdf", 
        "logbook.pdf",
        "Logbook.pdf",
        # XLS patterns as fallback
        "JarfclrpReport.xls", 
        "jarfclrpReport.xls", 
        "logbook.xls", 
        "Logbook.xls"
    ]
    for name in logbook_patterns:
        path = os.path.join(directory, name)
        if os.path.exists(path):
            logbook_file = path
            break
    
    return pdf_file, logbook_file


def main():
    """Main function to run the allowance calculator."""
    
    # Parse command line arguments
    pdf_schedule_file = None
    logbook_file = None
    
    if len(sys.argv) > 1:
        pdf_schedule_file = sys.argv[1]
    
    if len(sys.argv) > 2:
        logbook_file = sys.argv[2]
    
    # Auto-detect files if not provided
    if not pdf_schedule_file or not logbook_file:
        auto_pdf, auto_logbook = find_files(".")
        if not pdf_schedule_file:
            pdf_schedule_file = auto_pdf
        if not logbook_file:
            logbook_file = auto_logbook
    
    # Print header
    print(f"\n{'='*60}")
    print("PILOT ALLOWANCE CALCULATOR")
    print(f"{'='*60}")
    
    # Check for pdfplumber
    if not PDF_SUPPORT:
        print("\nERROR: pdfplumber is required but not installed.")
        print("Please run: pip install pdfplumber")
        return 1
    
    # Validate PDF file
    if not pdf_schedule_file or not os.path.exists(pdf_schedule_file):
        print("\nERROR: ScheduleReport.pdf not found!")
        print("\nUsage:")
        print("  python -m pilot_allowance ScheduleReport.pdf JarfclrpReport.pdf")
        print("\nOr place both files in the current directory and run:")
        print("  python -m pilot_allowance")
        return 1
    
    # Determine logbook file type for display
    logbook_type = "PDF" if logbook_file and logbook_file.lower().endswith('.pdf') else "XLS"
    
    # Print file information
    print(f"\nInput files:")
    print(f"  Schedule (PDF): {pdf_schedule_file}")
    if logbook_file and os.path.exists(logbook_file):
        print(f"  Logbook ({logbook_type}):  {logbook_file}")
    else:
        print("  Logbook:        Not found")
        print("                  → Tail-swap, transit, and night calculations unavailable")
    print("\nProcessing...")
    
    try:
        # Parse PDF schedule
        pdf_parser = PDFScheduleParser(pdf_schedule_file)
        pdf_parser.parse()
        
        if not pdf_parser.pilot_info:
            print("Error: Could not extract pilot information from the PDF.")
            return 1
        
        print(f"  ✓ Loaded schedule for {pdf_parser.pilot_info.name}")
        
        # Parse logbook if available (supports both PDF and XLS)
        logbook_parser = None
        if logbook_file and os.path.exists(logbook_file):
            try:
                logbook_parser = create_logbook_parser(logbook_file)
                logbook_parser.parse()
                print(f"  ✓ Loaded logbook with {len(logbook_parser.flights)} flights")
                print(f"    → Tail-swap, transit, and night calculations enabled")
            except Exception as e:
                print(f"  ⚠ Could not load logbook: {e}")
        
        # Calculate allowances
        calculator = AllowanceCalculator(pdf_parser, logbook_parser)
        breakdown = calculator.calculate_all()
        
        print()
        
        # Generate and print report
        report = generate_report(pdf_parser, breakdown)
        print(report)
        
        # Save to file
        base_name = os.path.basename(pdf_schedule_file)
        output_file = base_name.replace('.pdf', '_allowance_report.txt')
        output_file = output_file.replace('.PDF', '_allowance_report.txt')
        
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"Report saved to: {output_file}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: File not found: {e}")
        return 1
    except Exception as e:
        print(f"Error processing schedule: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
