"""
FastAPI application for Pilot Allowance Calculator.

Provides an API endpoint to upload schedule PDF and logbook PDF files
and receive the calculated allowances as JSON response.

Usage:
    uvicorn pilot_allowance.api:app --reload
    
    or run directly:
    python -m pilot_allowance.api
"""

import os
import tempfile
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .parsers import PDFScheduleParser, create_logbook_parser
from .calculators import AllowanceCalculator
from .constants import RATES


# ============================================================================
# Response Models
# ============================================================================

class PilotInfoResponse(BaseModel):
    """Pilot information in API response."""
    employee_id: str
    name: str
    base: str
    rank: str
    rank_full: str
    aircraft_type: str


class SummaryStatsResponse(BaseModel):
    """Schedule summary statistics."""
    block_hours: str = ""
    duty_hours: str = ""
    deadhead_hours: str = ""
    off_days: str = ""
    standby_days: str = ""
    flight_days: str = ""
    training_days: str = ""
    landings: str = ""
    operating_flights: int = 0
    deadhead_flights: int = 0
    layover_count: int = 0


class AllowanceDetailItem(BaseModel):
    """Single detail item with date for filtering."""
    date: str = ""
    description: str = ""


class AllowanceDetailResponse(BaseModel):
    """Individual allowance details."""
    count: int = 0
    hours: float = 0.0
    rate: float = 0.0
    amount: float = 0.0
    details: List[AllowanceDetailItem] = []


class LayoverAllowanceResponse(BaseModel):
    """Layover allowance details."""
    count: int = 0
    base_amount: float = 0.0
    extra_hours: float = 0.0
    extra_amount: float = 0.0
    total: float = 0.0
    base_rate: float = 0.0
    extra_rate: float = 0.0
    details: List[AllowanceDetailItem] = []


class AllowanceBreakdownResponse(BaseModel):
    """Complete allowance breakdown."""
    tail_swap: AllowanceDetailResponse
    transit: AllowanceDetailResponse
    layover: LayoverAllowanceResponse
    deadhead: AllowanceDetailResponse
    night: AllowanceDetailResponse
    total_amount: float


class CalculationResponse(BaseModel):
    """Complete API response."""
    success: bool
    message: str
    pilot_info: Optional[PilotInfoResponse] = None
    summary: Optional[SummaryStatsResponse] = None
    allowances: Optional[AllowanceBreakdownResponse] = None


# ============================================================================
# FastAPI Application
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("🚀 Pilot Allowance Calculator API starting...")
    yield
    print("👋 Pilot Allowance Calculator API shutting down...")


app = FastAPI(
    title="Pilot Allowance Calculator API",
    description="""
    Calculate pilot allowances based on schedule and logbook files.
    
    ## Features
    - Upload ScheduleReport.pdf and JarfclrpReport.xls
    - Get calculated allowances as JSON
    
    ## Allowance Types
    - **Tail-swap**: When aircraft changes between consecutive flights
    - **Transit**: Domestic halts > 90 minutes (max 4 hours)
    - **Layover**: Domestic layovers > 10 hours
    - **Deadhead**: Non-operating flight time
    - **Night**: Flight time between 00:00-06:00 IST
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Pilot Allowance Calculator API",
        "version": "1.0.0",
        "endpoints": {
            "POST /calculate": "Upload files and calculate allowances",
            "GET /rates": "Get current allowance rates",
            "GET /health": "Health check",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/rates")
async def get_rates():
    """Get current allowance rates."""
    return {
        "effective_date": "2026-01-01",
        "rates": {
            "tail_swap": {
                "captain": RATES['tail_swap']['CP'],
                "first_officer": RATES['tail_swap']['FO'],
                "unit": "per tail-swap"
            },
            "transit": {
                "captain": RATES['transit_per_hour']['CP'],
                "first_officer": RATES['transit_per_hour']['FO'],
                "unit": "per hour",
                "conditions": "halts > 90 min, max 4 hours per halt"
            },
            "layover": {
                "base": {
                    "captain": RATES['layover_base']['CP'],
                    "first_officer": RATES['layover_base']['FO'],
                    "duration": "10:01 to 24 hours"
                },
                "extra": {
                    "captain": RATES['layover_extra_per_hour']['CP'],
                    "first_officer": RATES['layover_extra_per_hour']['FO'],
                    "unit": "per hour beyond 24 hours"
                }
            },
            "deadhead": {
                "captain": RATES['deadhead_per_block_hour']['CP'],
                "first_officer": RATES['deadhead_per_block_hour']['FO'],
                "unit": "per block hour"
            },
            "night": {
                "captain": RATES['night_per_hour']['CP'],
                "first_officer": RATES['night_per_hour']['FO'],
                "unit": "per night hour (00:00-06:00 IST)"
            }
        }
    }


@app.post("/calculate", response_model=CalculationResponse)
async def calculate_allowances(
    schedule_pdf: UploadFile = File(..., description="ScheduleReport.pdf file"),
    logbook_pdf: UploadFile = File(None, description="JarfclrpReport.pdf file (optional but recommended)")
):
    """
    Calculate pilot allowances from uploaded files.
    
    - **schedule_pdf**: Required. The pilot's schedule report in PDF format.
    - **logbook_pdf**: Optional but recommended. The pilot's logbook in PDF format.
      Required for accurate tail-swap, transit, and night calculations.
    
    Returns calculated allowances as JSON.
    """
    
    # Validate schedule file
    if not schedule_pdf.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail="Schedule file must be a PDF"
        )
    
    # Validate logbook file if provided (accept both PDF and XLS for backwards compatibility)
    logbook_suffix = None
    if logbook_pdf:
        filename_lower = logbook_pdf.filename.lower()
        if filename_lower.endswith('.pdf'):
            logbook_suffix = '.pdf'
        elif filename_lower.endswith('.xls'):
            logbook_suffix = '.xls'
        else:
            raise HTTPException(
                status_code=400, 
                detail="Logbook file must be a PDF or XLS file"
            )
    
    # Create temporary files for processing
    temp_files = []
    
    try:
        # Save schedule PDF to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
            content = await schedule_pdf.read()
            tmp_pdf.write(content)
            tmp_pdf_path = tmp_pdf.name
            temp_files.append(tmp_pdf_path)
        
        # Save logbook to temp file if provided
        tmp_logbook_path = None
        if logbook_pdf:
            with tempfile.NamedTemporaryFile(delete=False, suffix=logbook_suffix) as tmp_logbook:
                content = await logbook_pdf.read()
                tmp_logbook.write(content)
                tmp_logbook_path = tmp_logbook.name
                temp_files.append(tmp_logbook_path)
        
        # Parse PDF schedule
        pdf_parser = PDFScheduleParser(tmp_pdf_path)
        pdf_parser.parse()
        
        if not pdf_parser.pilot_info:
            raise HTTPException(
                status_code=400,
                detail="Could not extract pilot information from the PDF. Please check the file format."
            )
        
        # Parse logbook if provided
        logbook_parser = None
        if tmp_logbook_path:
            try:
                logbook_parser = create_logbook_parser(tmp_logbook_path)
                logbook_parser.parse()
            except Exception as e:
                # Continue without logbook if parsing fails
                logbook_parser = None
        
        # Calculate allowances
        calculator = AllowanceCalculator(pdf_parser, logbook_parser)
        breakdown = calculator.calculate_all()
        
        # Build response
        pilot = pdf_parser.pilot_info
        rank = pilot.rank
        
        response = CalculationResponse(
            success=True,
            message="Allowances calculated successfully",
            pilot_info=PilotInfoResponse(
                employee_id=pilot.employee_id,
                name=pilot.name,
                base=pilot.base,
                rank=pilot.rank,
                rank_full="Captain" if pilot.rank == 'CP' else "First Officer",
                aircraft_type=pilot.aircraft_type
            ),
            summary=SummaryStatsResponse(
                block_hours=pdf_parser.summary_stats.get('block_hours', ''),
                duty_hours=pdf_parser.summary_stats.get('duty_hours', ''),
                deadhead_hours=pdf_parser.summary_stats.get('deadhead_hours', ''),
                off_days=pdf_parser.summary_stats.get('off_days', ''),
                standby_days=pdf_parser.summary_stats.get('standby_days', ''),
                flight_days=pdf_parser.summary_stats.get('flight_days', ''),
                training_days=pdf_parser.summary_stats.get('training_days', ''),
                landings=pdf_parser.summary_stats.get('landings', ''),
                operating_flights=len([f for f in pdf_parser.flight_duties if f.is_operating]),
                deadhead_flights=len([f for f in pdf_parser.flight_duties if f.is_deadhead]),
                layover_count=len(pdf_parser.layovers)
            ),
            allowances=AllowanceBreakdownResponse(
                tail_swap=AllowanceDetailResponse(
                    count=breakdown.tail_swap_count,
                    rate=RATES['tail_swap'][rank],
                    amount=breakdown.tail_swap_amount,
                    details=[AllowanceDetailItem(date=d.date, description=d.description) for d in breakdown.tail_swap_details]
                ),
                transit=AllowanceDetailResponse(
                    hours=breakdown.transit_hours,
                    rate=RATES['transit_per_hour'][rank],
                    amount=breakdown.transit_amount,
                    details=[AllowanceDetailItem(date=d.date, description=d.description) for d in breakdown.transit_details]
                ),
                layover=LayoverAllowanceResponse(
                    count=breakdown.layover_count,
                    base_amount=breakdown.layover_base_amount,
                    extra_hours=breakdown.layover_extra_hours,
                    extra_amount=breakdown.layover_extra_amount,
                    total=breakdown.layover_total,
                    base_rate=RATES['layover_base'][rank],
                    extra_rate=RATES['layover_extra_per_hour'][rank],
                    details=[AllowanceDetailItem(date=d.date, description=d.description) for d in breakdown.layover_details]
                ),
                deadhead=AllowanceDetailResponse(
                    hours=breakdown.deadhead_hours,
                    rate=RATES['deadhead_per_block_hour'][rank],
                    amount=breakdown.deadhead_amount,
                    details=[AllowanceDetailItem(date=d.date, description=d.description) for d in breakdown.deadhead_details]
                ),
                night=AllowanceDetailResponse(
                    hours=breakdown.night_hours,
                    rate=RATES['night_per_hour'][rank],
                    amount=breakdown.night_amount,
                    details=[AllowanceDetailItem(date=d.date, description=d.description) for d in breakdown.night_details]
                ),
                total_amount=breakdown.total_amount
            )
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing files: {str(e)}"
        )
    finally:
        # Clean up temporary files
        for tmp_file in temp_files:
            try:
                os.unlink(tmp_file)
            except:
                pass


# ============================================================================
# Run server directly
# ============================================================================

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the API server."""
    import uvicorn
    uvicorn.run(
        "pilot_allowance.api:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    import sys
    
    host = "0.0.0.0"
    port = 8000
    
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    print(f"\n🚀 Starting Pilot Allowance Calculator API on http://{host}:{port}")
    print(f"📚 API Documentation: http://localhost:{port}/docs")
    print(f"📖 Alternative docs: http://localhost:{port}/redoc\n")
    
    run_server(host=host, port=port, reload=True)

