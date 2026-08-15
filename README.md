# Sinergia — Automated M&A Accretion/Dilution Engine

Sinergia is an institutional-grade M&A deal screening and pro-forma merger modeling engine built with Python and FastAPI. It automates front-office investment banking workflows by ingesting public equity financial statements, structuring customizable consideration mixes (Cash, Debt, Equity), and modeling balance sheet consolidations, Purchase Price Allocation (PPA), and EPS accretion/dilution mechanics.

---

## Architecture and Technical Overview

- **Data Ingestion and Schema Validation**: Ingests live equity prices and three-statement financial data using `yfinance`, strictly validating inputs via Pydantic.
- **Deterministic Financial Engine**: Computes pro-forma Net Income, share dilution, interest tax shields, goodwill creation, and solves for breakeven pre-tax synergies.
- **Sensitivity Analysis**: Generates two-dimensional scenario matrices (Offer Premium vs. Stock Consideration Mix) visualized through Plotly heatmaps.
- **Audit-Ready Financial Models**: Exports dynamically linked `.xlsx` financial workbooks using `openpyxl` with native Excel formulas.
- **Persistence and Cloud Infrastructure**: Uses PostgreSQL via SQLModel for deal record persistence and is containerized with Docker for deployment on Google Cloud Run.

---

## Tech Stack

- **Backend**: Python 3.11 / 3.12, FastAPI, Uvicorn, Pydantic
- **Database & ORM**: PostgreSQL, SQLModel, SQLAlchemy, Psycopg2
- **Financial Analytics & Export**: Pandas, NumPy, OpenPyXL, Plotly, YFinance
- **Testing & Quality Assurance**: Pytest, HTTPX
- **Infrastructure & Cloud**: Docker, Google Cloud Run

---

## Project Roadmap and Status

### Phase 1: Environment, Database & Data Ingestion Setup (Completed)
- Virtual environment configuration and locked dependencies initialized in `requirements.txt`.
- PostgreSQL connection engine established with SQLModel in `backend/database.py`, supporting local and cloud connection strings (Supabase / Neon / SQLite fallback).
- Market data ingestion pipeline implemented in `backend/ingestion.py` using `yfinance`.
- Pydantic schema validation created in `backend/models.py` to enforce strict numerical and boundary constraints on financial metrics ($\text{Share Price} > 0$, $\text{Diluted Shares} > 0$, $\text{Total Debt} \ge 0$, $\text{Tax Rate} \in [0.0, 0.5]$).

### Phase 2: Merger Mechanics & Breakeven Synergies Engine (Planned)
- Implementation of transaction sizing: Offer Price, Purchase Equity Value, and Purchase Enterprise Value.
- Purchase Price Allocation (PPA) and Goodwill creation logic.
- Consideration mix processing (% Cash, % Debt, % Stock) and new share count derivation.
- Pro-forma net income consolidation, incremental debt interest, and foregone cash interest calculations.
- Algebraic solver for Breakeven Pre-Tax Synergies.

### Phase 3: 2D Sensitivity Engine & Dynamic Excel Pipeline (Planned)
- Generation of 2D sensitivity matrices varying Offer Premiums (10% to 50%) against Stock Consideration Mix (0% to 100%).
- Plotly heatmap rendering for accretion and dilution visualization.
- Dynamic `.xlsx` workbook generation via `openpyxl` using active Excel formulas for full auditability.

### Phase 4: PostgreSQL Persistence & REST API Layer (Planned)
- Definition of `DealRecord` SQLModel tables with JSONB support for multi-variable scenario storage.
- FastAPI endpoints: `POST /api/deals/run-and-save`, `GET /api/deals/history`, and `GET /api/deals/export-excel`.
- Automated unit test suite with `pytest` covering all-cash, all-stock, and breakeven synergy conditions.

### Phase 5: Frontend UI, GCP Cloud Run Deployment & Documentation (Planned)
- Interactive dashboard with deal structuring sliders, scenario tables, and visualization charts.
- Containerization using `Dockerfile` and deployment to Google Cloud Run.
- Public live URL hosting and final technical documentation.

---

## Directory Structure

```plaintext
Sinergia/
├── backend/
│   ├── __init__.py
│   ├── database.py          # PostgreSQL connection & session configuration
│   ├── models.py            # SQLModel schema definitions
│   ├── ingestion.py         # Market data ingestion & Pydantic validation
│   ├── merger_engine.py     # Core pro-forma & accretion/dilution math
│   ├── sensitivity.py       # 2D scenario matrix generator
│   ├── excel_exporter.py    # Dynamic openpyxl model builder
│   └── main.py              # FastAPI REST application routes
├── tests/
│   ├── __init__.py
│   ├── test_ingestion.py    # Phase 1 unit test cases
│   └── test_merger_math.py  # Comprehensive test cases
├── scratch/
│   └── verify_phase1.py     # Phase 1 standalone accuracy verification
├── .env
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Getting Started (Phase 1)

### Prerequisites
- Python 3.10+ installed
- PostgreSQL database (Local or Cloud via Supabase/Neon)

### Quickstart

1. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/sinergia_db
   PORT=8000
   ```

2. **Test Data Ingestion**:
   ```python
   from backend.ingestion import fetch_company_financials

   acquirer = fetch_company_financials("MSFT")
   print(acquirer)
   ```

3. **Run Phase 1 Accuracy Verification**:
   ```bash
   python scratch/verify_phase1.py
   ```

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
