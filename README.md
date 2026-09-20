# Sinergia: M&A Deal Screening & Accretion/Dilution Workstation

Sinergia is an M&A deal screening, pro-forma merger modeling and accretion/dilution analysis platform. It automates front-office investment banking workflows: it ingests public-company financials, structures the consideration mix (cash, debt, stock), models purchase price allocation and balance sheet consolidation, and produces audit-ready deliverables (Excel model, PowerPoint pitchbook, AI-written investment memo) alongside ML synergy predictions and Monte Carlo risk analysis.

**Status:** Phases 1 to 10 are implemented and covered by an automated test suite (24 tests). Remaining work is listed under [Roadmap](#roadmap).

---

## Features

| Area | What it does |
|---|---|
| **Data ingestion** | Live quotes and three-statement financials via `yfinance`, validated at the boundary with Pydantic (share price > 0, diluted shares > 0, total debt >= 0, tax rate in [0, 0.5]). |
| **Merger engine** | Offer price, purchase equity/enterprise value, consideration mix, new share issuance, foregone cash yield and debt interest, pro-forma net income, EPS accretion/dilution, and an algebraic solver for breakeven pre-tax synergies. |
| **Advanced accounting** | Purchase price allocation, intangible step-ups, deferred tax liabilities, goodwill, pro-forma EBITDA, leverage and interest coverage with Green / Amber / Red covenant status (below 3.0x, 3.0x to 4.5x, above 4.5x). |
| **Sensitivity analysis** | 2D matrix of offer premium vs. stock consideration mix, rendered as Plotly heatmaps. |
| **Exports** | Multi-tab `.xlsx` with live Excel formulas (blue hardcodes, black formulas), a 3-slide `.pptx` pitchbook, and a 4-paragraph investment committee memo. |
| **Quant models** | Random Forest (synergy and premium estimates), Gradient Boosting (regulatory risk score), 10,000-iteration vectorized Monte Carlo with 90/95/99% VaR, and a 3 to 5 year forecast with synergy ramp-up (33% / 66% / 100%). |
| **Benchmark feeds** | Historical mega-deals from SEC EDGAR S-4 filings, Damodaran sector multiples, and FRED macro yield curves. |
| **Security** | Argon2id password hashing, JWT in HttpOnly cookies, IP rate limiting (`slowapi`), TOTP MFA (RFC 6238) with single-use recovery codes. |
| **Persistence** | SQLModel over PostgreSQL (SQLite fallback for local development) storing deal history, inputs, financial statements and sensitivity matrices. |
| **Web app** | React / Vite single-page app with deal sliders, Plotly heatmaps and audit modals. |

---

## Architecture

```
Browser ──► Cloud Run container ──► PostgreSQL (Supabase / Neon)
            ├─ FastAPI  (/api/*, /docs)
            └─ React build served from frontend/dist (SPA fallback to index.html)
```

The frontend and backend are separate codebases that talk only through the JSON REST API. In production they ship in one container, so the app is same-origin (no CORS setup, and HttpOnly cookies work without cross-domain issues).

---

## Tech Stack

- **Backend:** Python 3.12, FastAPI, Uvicorn, Pydantic
- **Database:** PostgreSQL, SQLModel / SQLAlchemy, psycopg2 (SQLite for local dev)
- **Analytics:** pandas, NumPy, scikit-learn, yfinance
- **Exports:** openpyxl, python-pptx, Plotly
- **Security:** passlib (Argon2id), PyJWT, slowapi, pyotp
- **Frontend:** React, Vite
- **Testing:** pytest, HTTPX
- **Infrastructure:** Docker, Google Cloud Run, Artifact Registry, Secret Manager

---

## Project Structure

```plaintext
Sinergia/
├── backend/
│   ├── main.py                 # FastAPI app, routes, static frontend serving
│   ├── database.py             # Engine and session configuration
│   ├── models.py               # SQLModel / Pydantic schemas
│   ├── ingestion.py            # Market data ingestion and validation
│   ├── merger_engine.py        # Merger math, PPA, credit analysis
│   ├── sensitivity.py          # 2D scenario matrix generator
│   ├── excel_exporter.py       # Excel model builder
│   ├── pitchbook_exporter.py   # PowerPoint pitchbook
│   ├── ai_memo.py              # Investment committee memo
│   ├── ml_engine.py            # scikit-learn models
│   ├── monte_carlo.py          # Stochastic simulation
│   ├── multi_year_engine.py    # Multi-year forecast
│   ├── data_sources.py         # EDGAR, Damodaran, FRED feeds
│   └── security.py             # Auth, hashing, JWT, MFA, rate limiting
├── frontend/                   # React / Vite SPA (builds to frontend/dist)
├── tests/
│   ├── test_api.py
│   ├── test_historical_deals.py
│   ├── test_ingestion.py
│   ├── test_merger_math.py
│   └── test_ml_and_simulations.py
├── scratch/
│   ├── verify_phase1.py
│   └── deploy_gcp_cloud_run.sh
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.11+ and Node.js 20+
- Optional: Docker, and a PostgreSQL database (local, Supabase or Neon)

### Run locally

```bash
# 1. Environment
cp .env.example .env            # edit DATABASE_URL and secrets

# 2. Backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload

# 3. Frontend (separate terminal, for development with hot reload)
cd frontend && npm install && npm run dev
```

API docs are available at `http://localhost:8000/docs`.

### Run with Docker (API + Postgres)

```bash
docker compose up --build
```

Then open `http://localhost:8000`.

### Run the tests

```bash
pytest
```

Some tests call external services (yfinance), so the suite needs network access and takes a couple of minutes.

---

## API

Interactive documentation lives at `/docs` (Swagger UI). Core endpoints include:

- `POST /api/auth/login`
- `POST /api/deals/run-and-save`
- `GET  /api/deals/history`
- `GET  /api/deals/export-excel`

---

## Deployment (Google Cloud Run)

The app deploys as a single container: the Dockerfile builds the frontend, installs the Python dependencies and runs FastAPI.

1. Create the database (Supabase or Neon) and store `DATABASE_URL` and the JWT secret in Secret Manager.
2. Run:

   ```bash
   PROJECT_ID=your-project ./scratch/deploy_gcp_cloud_run.sh
   ```

   The script builds the image with Cloud Build, pushes it to Artifact Registry and deploys to Cloud Run with the secrets attached.

Notes:
- Give the service at least 2 GiB of memory (pandas, scikit-learn and the Monte Carlo engine exceed the 512 MiB default).
- Cloud Run's filesystem is ephemeral, so use a managed PostgreSQL database rather than the SQLite fallback.
- The container starts Uvicorn with `--proxy-headers` so rate limiting sees the real client IP.

---

## Roadmap

- [x] Phase 1: Data ingestion and validation
- [x] Phase 2: Merger mechanics and breakeven synergies
- [x] Phase 3: 2D sensitivity engine and Excel exporter
- [x] Phase 4: PostgreSQL persistence and REST API
- [x] Phase 5: React web app
- [x] Phase 6: Security, auth and TOTP MFA
- [x] Phase 7: Advanced accounting and credit analysis
- [x] Phase 8: Pitchbook PPTX and AI deal memo
- [x] Phase 9: Calibration and benchmark feeds
- [x] Phase 10: Quantitative ML and stochastic simulation
- [ ] Vite production build wired into the Docker image
- [ ] Live Cloud Run deployment
- [ ] Secondary market-data provider as automatic failover for yfinance
- [ ] CI pipeline (pytest with mocked network calls)

---

## License

Released under the MIT License. See [LICENSE](LICENSE).
