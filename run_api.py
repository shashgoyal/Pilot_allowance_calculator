#!/usr/bin/env python3
"""
Run the Pilot Allowance Calculator API server.

Usage:
    python run_api.py [port]
    
Example:
    python run_api.py 8000

API Endpoints:
    GET  /           - API information
    GET  /health     - Health check
    GET  /rates      - Get current allowance rates
    POST /calculate  - Upload files and calculate allowances

API Documentation:
    http://localhost:8000/docs      - Swagger UI
    http://localhost:8000/redoc     - ReDoc
"""

import sys
import os

# Add the script directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)


def main():
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is not installed.")
        print("Please run: pip3 install uvicorn fastapi python-multipart")
        return 1
    
    host = "0.0.0.0"
    port = 8000
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            return 1
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║         PILOT ALLOWANCE CALCULATOR API                       ║
╠══════════════════════════════════════════════════════════════╣
║  Server:  http://{host}:{port:<5}                               ║
║  Docs:    http://localhost:{port}/docs                         ║
║  ReDoc:   http://localhost:{port}/redoc                        ║
╠══════════════════════════════════════════════════════════════╣
║  Endpoints:                                                  ║
║    POST /calculate  - Upload PDF & XLS, get allowances       ║
║    GET  /rates      - View current allowance rates           ║
║    GET  /health     - Health check                           ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    uvicorn.run(
        "pilot_allowance.api:app",
        host=host,
        port=port,
        reload=True
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

