# Library Management System

## BBAT104: Fundamentals of Total Quality Management

### Course Project 2026 to 2027 &bull; Review 2 Milestone

---

## Student Information

| Field | Details |
|---|---|
| **Roll Number** | 31 |
| **Baseline Software System** | Library Management System |
| **Assigned Quality Goal** | Q02 Improve Performance |
| **Core TQM Objective** | Optimize issue and return flow and catalog search speed |
| **Academic Session** | 2026 to 2027 |
| **Course** | BBAT104 Fundamentals of Total Quality Management |
| **Milestone** | Review 2: Full Implementation, Testing & Deployment Preparation |

---

## Review 2 Deliverables & Feature Status

| Mandatory Feature / Requirement | Category | Implementation & Evidence | Status |
|---|---|---|---|
| **1. Fast Search** | Q02 Feature 1 | SQLite FTS5 trigram index for case-insensitive substring searches of 3+ characters, with a short-query fallback; category filtering uses a B-Tree index. `EXPLAIN QUERY PLAN` confirms indexed execution. Mean latency: **2.14 ms** (Target: &le; 50 ms). | **PASS** |
| **2. Optimized Reports** | Q02 Feature 2 | 5 management reports (Inventory Distribution, Currently Issued, Overdue Books, Circulation Activity, Member Summary) with SQL aggregation and CSV export. Mean generation time: **9.27 ms** (Target: &le; 200 ms). | **PASS** |
| **3. Centralized Dashboard** | Q02 Feature 3 | Real-time control center with KPI tiles, Chart.js charts, and an activity stream; metrics are read from a consistent database snapshot. Mean aggregation time: **2.08 ms** (Target: &le; 100 ms). | **PASS** |
| **4. Bulk CSV Import** | Q02 Feature 4 | Batch ingestion with strict headers, positive-copy validation, BOM support, duplicate skipping, row/file limits, and atomic `executemany`. Throughput: **16,218.3 records/sec** (Target: &ge; 1,000 rec/sec). | **PASS** |
| **5. Efficient Database Queries** | Q02 Feature 5 | Parameterized queries, selective projections, seven B-Tree indexes, WAL mode, and indexed substring search. Single-record lookup mean: **0.004 ms** (Target: &le; 10 ms). | **PASS** |
| **Book & Catalog CRUD** | Core System | Add book, view details, update metadata/stock, delete/archive with active loan protection safeguards. | **PASS** |
| **Member Management CRUD** | Core System | Register members, edit profiles, role assignment (`admin`/`student`), safe deletion restricted if active loans exist. | **PASS** |
| **Atomic Issue & Return** | Core Workflow | Single-step ACID transaction (`BEGIN IMMEDIATE`), concurrency race protection, bounded 1–90 day loan duration, and consistent overdue fine estimates. Mean latency: **0.91 ms** (Target: &le; 50 ms). | **PASS** |
| **Browser Web Interface** | Usability | Responsive dark UI built with Flask, HTML5, Tailwind CSS, and Chart.js. Fully responsive across desktop, tablet, and mobile. | **PASS** |
| **Automated Testing Suite** | QA Engineering | 33 unit and integration tests run against an isolated temporary database. | **PASS** |
| **Production Deployment Config** | Deployment | `Procfile`, `render.yaml`, `Dockerfile`, production WSGI entry point, generated deployment secrets, and `/health` endpoint. Cloud SQLite persistence still requires a mounted persistent disk. | **CONFIGURED; STORAGE LIMITATION DOCUMENTED** |

---

## Preserved Review 1 Documentation

All official Review 1 deliverables are preserved and synchronized with the Review 2 implementation:

| Deliverable | Document Link | Description |
|---|---|---|
| **Software Requirements Specification** | [docs/SRS.md](docs/SRS.md) | Full 16-section SRS covering functional, non-functional, system, database, and Q02 performance requirements |
| **Project Scope Definition** | [docs/Scope_Definition.md](docs/Scope_Definition.md) | Comprehensive In-Scope, Out-of-Scope, Boundaries, Objectives, Deliverables, and Success Criteria |
| **System Architecture Document** | [docs/System_Architecture.md](docs/System_Architecture.md) | Detailed architecture specification mapping all 5 Q02 performance features, web browser tier, and database layer |
| **Architecture Flowchart (Mermaid)** | [architecture/library_management_architecture.mmd](architecture/library_management_architecture.mmd) | Plain-text editable Mermaid source diagram |
| **Architecture Flowchart (SVG)** | [architecture/library_management_architecture.svg](architecture/library_management_architecture.svg) | Scalable vector graphics rendering for instant browser/evaluator viewing |

---

## Actual Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| **Programming Language** | Python 3.10+ (tested on Python 3.14) | Standard high-level language specified in BBAT104 curriculum; rapid prototyping, robust standard library. |
| **Web Application Server** | Flask 3.1 & Gunicorn 26.2 | Production-ready WSGI application framework providing high responsiveness, clean routing, and low overhead. |
| **Browser User Interface** | HTML5, Tailwind CSS, Chart.js | Modern responsive browser interface accessible on any device with dark mode aesthetics matching Review 1 specifications. |
| **Desktop GUI (Backward-Compatible)** | CustomTkinter / Tkinter | Retained for offline single-machine desktop evaluation if preferred. |
| **Relational Database** | SQLite 3 with FTS5 trigram and WAL mode | ACID-compliant local storage with indexed substring search and strategic B-Tree indexes. SQLite must include FTS5 trigram support. |
| **Data Processing & Analytics** | Pandas 3.0 & NumPy | Data-frame processing for analytical reports and SQC analysis; CSV import uses the Python standard library. |
| **Statistical Quality Control** | Matplotlib 3.11 | Generates individual X-charts with Mean, UCL (+3&sigma;), and LCL (-3&sigma;) process control limits. |
| **Production Deployment** | Docker, Render, Railway, Gunicorn | Declarative cloud hosting configurations supporting public HTTPS and automated health check polling. |

---

## Quantitative Performance Benchmark Results

Evaluated against a synthetic dataset of **3,000 catalog books, 300 registered members, and 1,000 circulation transactions** using `python benchmark.py`:

| Performance Metric | SRS Target Benchmark | Measured Result (Mean) | 95th Percentile | Evaluation Status |
|---|---|---|---|---|
| **1. Fast Catalog Search Latency** | &le; 50.0 ms | **2.14 ms** | 4.08 ms | **PASS** |
| **2. Issue / Return Transaction** | &le; 50.0 ms | **0.91 ms** | 1.02 ms | **PASS** |
| **3. Bulk CSV Ingestion Throughput** | &ge; 1,000 records/sec | **16,218.3 rec/s** | 123.3 ms total | **PASS** |
| **4. Optimized Reports Generation** | &le; 200.0 ms | **9.27 ms** | 11.65 ms | **PASS** |
| **5. Dashboard Metric Aggregation** | &le; 100.0 ms | **2.08 ms** | 3.01 ms | **PASS** |
| **6. B-Tree Indexed Point Lookup** | &le; 10.0 ms | **0.004 ms** | 0.005 ms | **PASS** |

*All six local benchmark measurements meet the stated targets. Results may vary by host and dataset size.*

---

## Installation and Setup

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Clone Repository
```bash
git clone git@github.com:hridyanshjoshi780-svg/BBAT104_TQM_AU_24_6053.git
cd BBAT104_TQM_AU_24_6053
```

### 3. Create & Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Environment Configuration
Copy the local-development environment template. `run.sh` loads `.env` automatically:
```bash
cp .env.example .env
```
The template uses development-only demo credentials. Configure these values in the hosting platform for production instead:
```ini
APP_ENV=development
SECRET_KEY=change-this-local-secret
ADMIN_PASSWORD=admin123
PORT=5000
HOST=0.0.0.0
FLASK_DEBUG=0
DATABASE_PATH=library.db
```

### 6. Initialize Database
The web application initializes the database on startup, or you can initialize it manually:
```bash
python database.py
```

---

## Running the Application

### Option A: Web Browser Application (Recommended for Review 2)
```bash
./run.sh
# OR explicitly:
python web_app.py
```
Open your browser and navigate to: **[http://localhost:5000](http://localhost:5000)**

### Option B: Production WSGI Server (Gunicorn)
```bash
gunicorn wsgi:application --bind 0.0.0.0:5000 --workers 2 --threads 4
```

### Option C: Desktop GUI (Review 1 Backward Compatibility)
```bash
./run.sh --desktop
```
*(Requires `sudo apt install python3-tk` on Linux)*

---

## Default Evaluation Accounts

| Role | Username | Password | Access Privileges |
|---|---|---|---|
| **Administrator** | `admin` | `admin123` | Local development/test only. |
| **Student (Patron)** | `student1` | `student123` | Local development/test only. |

Production requires an operator-provided `ADMIN_PASSWORD` and a 32+ character `SECRET_KEY`; it does not seed the demo student account or display demo login shortcuts.

---

## Testing & Verification

### 1. Run Automated Test Suite
The automated test suite runs against an isolated temporary SQLite database, guaranteeing zero interference with persistent data:
```bash
python -m unittest test_app.py -v
```
**Results:** `Ran 33 tests &bull; OK`

### 2. Run Quantitative Performance Benchmark
```bash
python benchmark.py
```
Measures and prints latency distributions across Search, Circulation, Bulk Ingestion, Reports, and Dashboard.

### 3. Health Check Verification
```bash
curl -s http://localhost:5000/health
```
The verified healthy response reports `"status": "healthy"`, `"database": "connected"`, and catalog metadata.
Production-mode WSGI startup and this endpoint were smoke-tested against a temporary database.

---

## Production Deployment Preparation

The project includes a browser-based deployment configuration. Public hosting has not been verified:

### 1. Render Deployment (1-Click Blueprint)
The repository includes [`render.yaml`](render.yaml):
1. Create a Render account at [render.com](https://render.com).
2. Connect this GitHub repository.
3. Select **"Blueprint"** deployment — Render reads `render.yaml`, configures Gunicorn, and generates the production secret and initial administrator password.

> **SQLite persistence:** The blueprint does not configure a persistent disk. SQLite data on the service filesystem can be lost when the instance is replaced or redeployed. Attach a persistent disk and set `DATABASE_PATH` to a path under its mount before relying on cloud data persistence; disk availability and cost depend on the hosting plan.

### 2. Railway / Fly.io / Heroku Deployment
The repository includes a standard [`Procfile`](Procfile):
```
web: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4
```

### 3. Docker Container Deployment
The repository includes a production [`Dockerfile`](Dockerfile):
```bash
docker build -t bbat104-library .
docker run -p 5000:5000 -e APP_ENV=production -e SECRET_KEY="<32+ random characters>" -e ADMIN_PASSWORD="<12+ character password>" bbat104-library
```

> **Public Deployment Status:** No public deployment or public URL has been verified. The local WSGI/health-check verification is reported separately; cloud deployment requires an account and persistent storage configuration.

---

## Total Quality Management (TQM) Implementation

The project applies foundational TQM principles:
- **PDCA Cycle:** Plan (SRS and architecture targets), Do (atomic circulation, indexed search, vectorized reports), Check (benchmark suite, unit tests, SQC control charts), Act (refining database indexes and error handlers).
- **Process Centric Approach:** Modeled via SIPOC process maps and Critical-to-Quality (CTQ) trees.
- **Risk Mitigation:** Failure Mode and Effects Analysis (FMEA) for race conditions, inventory counter discrepancies, and duplicate records.
- **Statistical Quality Control (SQC):** Individual X-Charts with UCL, Mean, and LCL tracking catalog query response stability over time.