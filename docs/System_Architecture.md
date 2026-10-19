# System Architecture Document

## Library Management System
### BBAT104: Fundamentals of Total Quality Management
**Academic Session:** 2026 to 2027  
**Roll Number:** 31  
**Assigned Quality Goal:** Q02 Improve Performance  
**Core TQM Goal:** Optimize issue and return flow and catalog search speed  
**Project Milestone:** Review 2

---

## 1. Architectural Overview

The **Library Management System** uses a Flask browser application with an SQLite data layer, alongside a backward-compatible CustomTkinter desktop interface. Pandas supports report processing and Matplotlib supports desktop statistical quality-control charts.

In accordance with the **BBAT104 Total Quality Management** guidelines and the assigned Quality Goal **Q02 Improve Performance**, the primary design directive is eliminating operational latency across high-frequency library workflows:
- Catalog searching
- Issue and return circulation transactions
- Analytical reporting
- Inventory onboarding via bulk CSV import
- Operational metric visualization via dashboards

The architecture separates the presentation layer, application logic, performance features (indexed search, batching, and report processing), and SQLite storage.

---

## 2. System Architecture Flowchart

The following flowchart illustrates the complete structural flow of the Library Management System, showing the progression of user commands through authentication, the management interface, application logic controllers, the performance optimization engine, the SQLite database layer, and final system responses.

```mermaid
flowchart TD
    %% User Layer
    subgraph UL["1. User & Access Layer"]
        U["Library User / Administrator / Librarian"]
        AUTH["Authentication & Access Entry Point<br/>(Role Verification & Session)"]
        U -->|Credentials / Launch| AUTH
    end

    %% Presentation Layer
    subgraph PL["2. Library Management Presentation Layer (Web Browser & Desktop GUI)"]
        AUTH -->|Access Granted| UI["Central Library Navigation Interface (HTML5/Tailwind/Flask & Tkinter)"]
        UI --> TAB_SEARCH["Catalog Search View"]
        UI --> TAB_CIRC["Issue & Return Management View"]
        UI --> TAB_DASH["[Q02] Central Performance & Operational Dashboard"]
        UI --> TAB_CSV["[Q02] Bulk CSV Import Interface"]
        UI --> TAB_REPORTS["[Q02] Analytics & Summary Reports View"]
    end

    %% Application Logic Layer
    subgraph ALL["3. Application Logic Layer (Python Engine)"]
        TAB_SEARCH --> SVC_SEARCH["Search & Catalog Processing Service"]
        TAB_CIRC --> SVC_CIRC["Issue & Return Workflow Controller"]
        TAB_DASH --> SVC_DASH["Dashboard Metric Aggregator"]
        TAB_CSV --> SVC_CSV["[Q02] Batch CSV Parser & Validator"]
        TAB_REPORTS --> SVC_REPORTS["[Q02] Report Generation Service"]
    end

    %% Performance Optimization Layer (Q02 Quality Focus)
    subgraph POL["4. Performance Optimization Layer (Core Q02 Engine)"]
        SVC_SEARCH -->         OPT_SEARCH["[Q02] Fast Search Engine<br/>- FTS5 Trigram Substring Matching<br/>- LIKE Fallback for Short Queries<br/>- Selective Column Projection"]
        SVC_CIRC --> OPT_CIRC["[Q02] Streamlined Transaction Handler<br/>- Atomic Single-Step Borrow/Return<br/>- Immediate Inventory Counter Updates"]
        SVC_CSV --> OPT_CSV["[Q02] Fast Bulk Ingestion Pipeline<br/>- Parameterized executemany Batch Inserts<br/>- Transaction Wrap (Single Commit)"]
        SVC_REPORTS -->         OPT_REPORTS["[Q02] Optimized Aggregation Engine<br/>- SQL Aggregation and Pandas Processing<br/>- Pre-filtered Summary Pipelines"]
        SVC_DASH --> OPT_DASH["[Q02] Real-Time Metric Aggregation<br/>- Consistent Snapshot KPI Queries<br/>- Chart.js Browser Rendering"]
    end

    %% Database Optimization & Storage Layer
    subgraph DBL["5. Database Layer (SQLite3 Engine)"]
        OPT_SEARCH -->|Indexed Queries| DB_ENGINE["[Q02] Efficient Database Query Layer<br/>(Short-Lived Connections, WAL, Row Factory, Foreign Keys)"]
        OPT_CIRC -->|Atomic Transactions| DB_ENGINE
        OPT_CSV -->|Bulk Commits| DB_ENGINE
        OPT_REPORTS -->|Aggregated Selects| DB_ENGINE
        OPT_DASH -->|Direct Count / Range Queries| DB_ENGINE

        DB_ENGINE --> T_BOOKS[("books Table<br/>Indexed: isbn, title, category")]
        DB_ENGINE --> T_MEMBERS[("users / members Table<br/>Indexed: username, role")]
        DB_ENGINE --> T_BORROW[("borrow_records Table<br/>Indexed: book_id, user_id, status")]
        DB_ENGINE --> T_METRICS[("search_metrics / audit Table<br/>Indexed: timestamp, query")]
    end

    %% Response Flow
    subgraph SRL["6. System Response & Feedback Layer"]
        DB_ENGINE -.->|Fast Result Sets (<50ms)| ALL
        ALL -.->|Formatted UI State & Charts| PL
        PL -.->|Visual Confirmation & Metrics| RESP["System Response<br/>(Catalog Grid, KPI Cards, Status Prompts, Visual Charts)"]
        RESP -.->|Instant Feedback| U
    end

    %% Class Styles
    classDef q02Style fill:#1e3a8a,stroke:#60a5fa,stroke-width:2px,color:#ffffff;
    classDef defaultStyle fill:#1e293b,stroke:#475569,stroke-width:1px,color:#f8fafc;
    classDef storageStyle fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#ffffff;
    classDef userStyle fill:#134e4a,stroke:#2dd4bf,stroke-width:2px,color:#ffffff;

    class TAB_DASH,TAB_CSV,TAB_REPORTS,SVC_CSV,SVC_REPORTS,OPT_SEARCH,OPT_CIRC,OPT_CSV,OPT_REPORTS,OPT_DASH,DB_ENGINE q02Style;
    class T_BOOKS,T_MEMBERS,T_BORROW,T_METRICS storageStyle;
    class U,AUTH,RESP userStyle;
```

> **Vector Diagram Source:** A standalone editable Mermaid definition is stored at [`architecture/library_management_architecture.mmd`](../architecture/library_management_architecture.mmd), and a scalable vector graphics rendering is provided at [`architecture/library_management_architecture.svg`](../architecture/library_management_architecture.svg).

---

## 3. Detailed Component Decomposition

### 3.1 User & Access Entry Point
- **User Roles Supported:** Administrator and student/member.
- **Authentication Entry Point:** Provides credential verification, session initialization, and role resolution. Administrators can access staff operations; students are restricted to their own circulation activity.

### 3.2 Library Management Presentation Layer
The primary presentation layer is a responsive browser application built with Python **Flask**, **HTML5**, **Tailwind CSS**, and **Chart.js**. A local desktop interface remains available for backward compatibility:
1. **Catalog Search View:** Real-time multi-attribute search bar with interactive category and availability filters, instant tabular results, and latency tracking.
2. **Issue & Return View:** Two-click checkout and check-in panels with instant book availability indicators and automatic overdue fine computation.
3. **Operational Performance Dashboard:** High-level overview cards presenting 8 circulation KPIs, total catalog volumes, and Chart.js distribution charts.
4. **Bulk CSV Import View:** File dropzone, schema instructions, template download, and high-throughput ingestion results.
5. **Analytics & Summary Reports View:** Filterable reporting grids for overdue loans, category distribution, borrower activity, and one-click CSV export.
6. **Audit & Member Management:** Administrative controls for user accounts and tamper-evident event trails.

### 3.3 Application Logic Layer
Written in modular Python 3, this layer coordinates business logic rules without coupling GUI components directly to raw SQL queries:
- **Search & Catalog Processing Service:** Sanitizes text queries, executes filtering logic, and computes latency metrics for quality control monitoring.
- **Issue & Return Processing Controller:** Enforces lending policies (maximum active loans, duplicate checkout prevention, loan period duration calculations, fine schedules).
- **Dashboard Metric Aggregator:** Collects snapshot metrics across books, members, and active loans to supply widget cards.
- **CSV Parser & Validator:** Verifies CSV headers, parses records, checks mandatory field constraints, and prepares clean tuples for ingestion.
- **Report Generation Service:** Assembles tabular summary views and formats CSV export streams.

### 3.4 Performance Optimization Layer (Q02 Engine)
This layer encapsulates the specific software engineering enhancements designed to satisfy **Q02 Improve Performance**:
- **Fast Search Engine:** Uses an FTS5 trigram virtual table for case-insensitive substring searches of at least three characters, with a `LIKE` fallback for shorter queries and selective result projections.
- **Streamlined Transaction Handler:** Consolidates loan status checks, borrow record insertions, and inventory decrementing into a single atomic sequence, preventing multiple table scans and lock stalls.
- **Fast Bulk Ingestion Pipeline:** Replaces individual row insertion statements with SQLite `executemany` operations wrapped in a single database transaction, boosting throughput to over 1,000 records per second.
- **Optimized Aggregation Engine:** Employs SQL aggregation and `pandas` processing for statistical summaries, avoiding repetitive per-row database queries.
- **Real-Time Metric Aggregator:** Uses direct indexed count and aggregation queries to feed the dashboard in under 100 milliseconds.

### 3.5 Database Layer (SQLite3 Engine)
Data persistence is handled by an optimized SQLite 3 database utilizing:
- **Connection Optimization:** Centralized connection factory with `row_factory = sqlite3.Row`; WAL mode is configured during database initialization, with short-lived connections for operations.
- **Foreign Key Integrity:** `PRAGMA foreign_keys = ON` ensuring referential integrity across users, books, and borrow records.
- **Strategic B-Tree Indexing:**
  - `idx_books_isbn` on `books(isbn)` for instant O(log N) lookup.
  - `idx_books_title_author` on `books(title, author)` for multi-attribute matching.
  - `idx_books_category` on `books(category)` for instant category filtering.
  - `idx_borrow_due_status` on `borrow_records(status, due_date)` for zero-delay overdue scanning.
  - `idx_borrow_lookup` on `borrow_records(user_id, book_id, status)` for rapid circulation validation.
  - `idx_metrics_timestamp` on `search_metrics(timestamp)`.
  - `idx_audit_timestamp` on `audit_logs(timestamp)`.
  - `books_search`, an FTS5 trigram virtual table maintained by triggers for indexed title, author, and ISBN substring search.

### 3.6 System Response & Operational Feedback Layer
Ensures prompt, deterministic user feedback:
- Instant UI table refresh (<50 ms target for search queries).
- Immediate visual confirmation alerts upon book issue/return.
- Reactive Chart.js rendering in the browser and Matplotlib for desktop SQC charts.

---

## 4. Mapping of the Five Assigned Q02 Features

| Assigned Q02 Feature | Architectural Placement | Optimization Mechanism | Expected TQM Improvement | Measured Result |
|---|---|---|---|---|
| **1. Fast Search** | Interface, Search Logic & DB Indexes | FTS5 trigram index for substring queries of 3+ characters; short-query fallback | Sub-50ms catalog retrieval | **2.14 ms mean; 4.08 ms p95** (PASS) |
| **2. Optimized Reports** | Report Service & Pandas Processing | SQL aggregation, Pandas summaries, and batched result retrieval | Report generation under 200ms | **9.27 ms mean; 11.65 ms p95** (PASS) |
| **3. Dashboard** | Browser & Metric Aggregator | Consistent-snapshot KPI query aggregation and Chart.js charts | Dashboard aggregation under 100ms | **2.08 ms mean; 3.01 ms p95** (PASS) |
| **4. CSV Import** | CSV Manager & Batch Pipeline | Validated parameterized `executemany()` in an atomic transaction | Ingestion rate at least 1,000 rows/sec | **16,218.3 rows/s; 123.3 ms / 2,000 rows** (PASS) |
| **5. Efficient Database Queries** | Database Engine & Schema Definition | Seven B-Tree indexes, FTS5 trigram index, WAL, selective projections | Single-record lookup under 10ms | **0.004 ms mean; 0.005 ms p95** (PASS) |

---

## 5. Technology Stack Specifications

| Layer / Component | Technology | Rationale & Academic Justification |
|---|---|---|
| **Programming Language** | Python 3.10+ (tested 3.14) | Standard high-level language specified in BBAT104 curriculum; rapid prototyping, robust standard library. |
| **Web Application Server** | Flask 3.1 & Gunicorn 26.2 | Production-ready lightweight WSGI web framework suitable for cloud HTTPS deployment. |
| **Browser User Interface** | HTML5, Tailwind CSS, Chart.js | Modern responsive browser interface accessible on desktop, tablet, and mobile without OS dependencies. |
| **Desktop Graphical Interface** | CustomTkinter / Tkinter | Retained for backward-compatible offline desktop execution. |
| **Relational Database** | SQLite 3 (WAL mode enabled) | Serverless, zero-configuration, ACID-compliant relational storage with full SQL support. |
| **Data Processing & Analytics** | Pandas 3.0 & NumPy | Data-frame processing for report summaries and SQC analysis. |
| **Statistical Quality Control** | Matplotlib 3.11 | Generation of performance control charts (Individual X-charts) and statistical limits. |
| **Production Deployment** | Docker, Render, Railway, Procfile | Declarative cloud hosting configurations supporting public HTTPS and automated health checks. |

---

## 6. Review 2 Architectural Verification

- [x] Functional browser-accessible web application deployed via Flask and Gunicorn.
- [x] Complete CRUD operations implemented for Books and Members.
- [x] All 5 assigned Q02 performance features quantitatively tested and verified.
- [x] Production deployment configuration (Procfile, render.yaml, Dockerfile, health check) ready.
- [x] Full automated test suite (33 tests passing) with temporary database isolation.
- [x] Preserved Review 1 deliverables, diagrams, and historical documents.

**Deployment data note:** The Render blueprint does not provision persistent storage. Cloud deployments using SQLite must attach a persistent mount and point `DATABASE_PATH` to it; no public deployment has been verified.
