# ✈️ Pilot Allowance Calculator

A comprehensive tool for calculating pilot allowances based on schedule and logbook files. Supports both CLI and API usage with a modern web UI.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Features

- **Multiple Input Formats**: Accepts PDF schedule reports and PDF/XLS logbook files
- **Comprehensive Allowance Calculation**:
  - 🔄 **Tail Swap** - When aircraft changes between consecutive flights
  - ⏱️ **Transit** - Domestic halts > 90 minutes (max 4 hours)
  - 🏨 **Layover** - Domestic layovers > 10 hours
  - 💺 **Deadhead** - Non-operating flight time
  - 🌙 **Night Flying** - Flight time between 00:00-06:00 IST
- **REST API** with FastAPI and automatic documentation
- **Modern Web UI** with drag-and-drop file upload (Vanilla JS & Vue.js versions)
- **Interactive Filtering** - Click on allowance cards to filter the breakdown table
- **CLI Support** for quick calculations

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/pilot-allowance-calculator.git
   cd pilot-allowance-calculator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Usage

### Option 1: Web UI (Recommended)

1. **Start the API server**
   ```bash
   python3 run_api.py
   ```
   Or with a custom port:
   ```bash
   python3 -m uvicorn pilot_allowance.api:app --port 8043 --reload
   ```

2. **Open the UI** (choose one):
   
   **Vanilla JS version:**
   ```bash
   open ui/index.html
   ```
   
   **Vue.js version:**
   ```bash
   open ui-vue/index-cdn.html
   ```

3. **Upload your files**
   - Drag & drop your `ScheduleReport.pdf` (required)
   - Optionally add your `JarfclrpReport.pdf` for accurate calculations
   - Click "Calculate Allowances"

4. **Filter Results**
   - Click on any allowance card to filter the table by that type
   - Click multiple cards to show multiple types
   - Click again to remove the filter
   - Use "Clear All" to reset filters

> **Note**: If using a different port, update the `API_URL` variable in the HTML file

### Option 2: Command Line Interface

```bash
# With both schedule and logbook
python3 -m pilot_allowance ScheduleReport.pdf JarfclrpReport.pdf

# With schedule only
python3 -m pilot_allowance ScheduleReport.pdf

# Alternative scripts
python3 calculate_allowance.py
python3 pilot_allowance_calculator.py
```

### Option 3: REST API

1. **Start the server**
   ```bash
   python3 run_api.py
   ```

2. **API Endpoints**

   | Method | Endpoint | Description |
   |--------|----------|-------------|
   | GET | `/` | API information |
   | GET | `/health` | Health check |
   | GET | `/rates` | Current allowance rates |
   | POST | `/calculate` | Upload files and calculate allowances |

3. **Example API call with curl**
   ```bash
   curl -X POST "http://localhost:8000/calculate" \
     -F "schedule_pdf=@ScheduleReport.pdf" \
     -F "logbook_pdf=@JarfclrpReport.pdf"
   ```

4. **Interactive API Documentation**
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 📁 Project Structure

```
pilot-allowance-calculator/
├── pilot_allowance/          # Main package
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # CLI entry point
│   ├── api.py               # FastAPI application
│   ├── calculators.py       # Allowance calculation logic
│   ├── constants.py         # Rates and configuration
│   ├── models.py            # Data models
│   ├── parsers.py           # PDF/XLS parsing
│   ├── main.py              # Core processing logic
│   └── report.py            # Report generation
├── ui/
│   └── index.html           # Web UI (Vanilla JS)
├── ui-vue/
│   ├── index-cdn.html       # Web UI (Vue.js CDN - no build required)
│   ├── index.html           # Vue.js Vite entry point
│   ├── package.json         # Node.js dependencies
│   ├── vite.config.js       # Vite configuration
│   └── src/                 # Vue.js source files
│       ├── main.js
│       ├── App.vue
│       └── components/      # Vue components
├── calculate_allowance.py   # Quick CLI script
├── pilot_allowance_calculator.py  # Alternative CLI script
├── run_api.py               # API server launcher
├── requirements.txt         # Python dependencies
└── README.md
```

## 📊 Input Files

### ScheduleReport.pdf (Required)
The pilot's monthly schedule report containing:
- Flight duties with dates, routes, and timings
- Layover information
- Pilot information (name, rank, base, aircraft type)

### JarfclrpReport.pdf (Optional but Recommended)
The pilot's logbook report containing:
- Detailed flight records with aircraft registrations
- Required for accurate tail-swap detection
- Required for night flying calculations
- Supports both PDF and legacy XLS formats

## 💰 Allowance Types

| Allowance | Description | Rate Basis |
|-----------|-------------|------------|
| **Tail Swap** | Aircraft change between consecutive flights | Per swap |
| **Transit** | Domestic halts > 90 minutes | Per hour (max 4h) |
| **Layover** | Domestic layovers > 10 hours | Base + hourly after 24h |
| **Deadhead** | Non-operating (passenger) flights | Per block hour |
| **Night** | Flying between 00:00-06:00 IST | Per hour |

## 🔧 Configuration

Allowance rates are configured in `pilot_allowance/constants.py`. Rates differ by rank (Captain vs First Officer).

## 📱 UI Features

- 🎨 Modern dark theme with smooth animations
- 📁 Drag-and-drop file upload
- 👨‍✈️ Pilot info display with total allowance
- 📊 Summary statistics dashboard (block hours, flights, layovers, etc.)
- 💳 **Clickable allowance cards** - Click to filter the table by type
- 🔍 **Multi-select filtering** - Select multiple allowance types at once
- 🏷️ **Active filter badges** - Visual indicators of selected filters
- 📅 Date-wise breakdown table grouped by date
- 🔎 Text search filter for dates and descriptions
- 📱 Fully responsive design

### UI Versions

| Version | File | Requirements |
|---------|------|--------------|
| Vanilla JS | `ui/index.html` | None - just open in browser |
| Vue.js (CDN) | `ui-vue/index-cdn.html` | None - just open in browser |
| Vue.js (Vite) | `ui-vue/` | Node.js + npm install |

## 🛠️ Development

### Running API in development mode
```bash
python3 -m uvicorn pilot_allowance.api:app --reload --port 8000
```

### Running Vue.js UI with Vite (optional)
```bash
cd ui-vue
npm install
npm run dev
```
This starts a development server with hot-reload at `http://localhost:5173`

### Running tests
```bash
python3 -m pytest tests/
```

## 📝 API Response Example

```json
{
  "success": true,
  "message": "Allowances calculated successfully",
  "pilot_info": {
    "employee_id": "12345",
    "name": "John Doe",
    "base": "DEL",
    "rank": "CP",
    "rank_full": "Captain",
    "aircraft_type": "A320"
  },
  "summary": {
    "block_hours": "45:30",
    "duty_hours": "120:00",
    "operating_flights": 25,
    "layover_count": 5
  },
  "allowances": {
    "tail_swap": { "count": 3, "amount": 1500.0 },
    "transit": { "hours": 8.5, "amount": 850.0 },
    "layover": { "count": 5, "total": 12500.0 },
    "deadhead": { "hours": 4.0, "amount": 2000.0 },
    "night": { "hours": 12.0, "amount": 3600.0 },
    "total_amount": 20450.0
  }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- PDF parsing powered by [pdfplumber](https://github.com/jsvine/pdfplumber)
- UI inspired by modern dashboard designs

---

Made with ❤️ for pilots

