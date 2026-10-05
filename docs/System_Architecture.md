# System Architecture Document

## Library Management System
### BBAT104: Fundamentals of Total Quality Management
**Academic Session:** 2026 to 2027  
**Roll Number:** 31  
**Assigned Quality Goal:** Q02 Improve Performance  
**Core TQM Goal:** Optimize issue and return flow and catalog search speed  
**Project Milestone:** Review 1  

---

## 1. Architectural Overview

The **Library Management System** is designed with a high-performance, modular multi-tier desktop architecture built around Python 3, SQLite, CustomTkinter, Pandas, and Matplotlib. 

In accordance with the **BBAT104 Total Quality Management** guidelines and the assigned Quality Goal **Q02 Improve Performance**, the primary design directive is eliminating operational latency across high-frequency library workflows:
- Catalog searching
- Issue and return circulation transactions
- Analytical reporting
- Inventory onboarding via bulk CSV import
- Operational metric visualization via dashboards

The architecture cleanly decouples the Presentation Layer (GUI), Application Logic Layer (workflow management), Performance Optimization Layer (caching, batching, vectorization), and Database Layer (SQLite with targeted indexing and optimized row factories).

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
    subgraph PL["2. Library Management Interface (CustomTkinter / GUI)"]
        AUTH -->|Access Granted| UI["Central Library Navigation Interface"]
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
        SVC_SEARCH --> OPT_SEARCH["[Q02] Fast Search Engine<br/>- Normalized Substring & Prefix Matching<br/>- In-Memory Caching of Active Queries<br/>- Selective Column Projection"]
        SVC_CIRC --> OPT_CIRC["[Q02] Streamlined Transaction Handler<br/>- Atomic Single-Step Borrow/Return<br/>- Immediate Inventory Counter Updates"]
        SVC_CSV --> OPT_CSV["[Q02] Fast Bulk Ingestion Pipeline<br/>- Parameterized executemany Batch Inserts<br/>- Transaction Wrap (Single Commit)"]
        SVC_REPORTS --> OPT_REPORTS["[Q02] Optimized Aggregation Engine<br/>- Pandas Vectorized Processing<br/>- Pre-filtered Summary Pipelines"]
        SVC_DASH --> OPT_DASH["[Q02] Real-Time Metric Aggregation<br/>- Lightweight KPI Querying<br/>- Matplotlib Visual Rendering"]
    end

    %% Database Optimization & Storage Layer
    subgraph DBL["5. Database Layer (SQLite3 Engine)"]
        OPT_SEARCH -->|Indexed Queries| DB_ENGINE["[Q02] Efficient Database Query Layer<br/>(Connection Pooling, Row Factory, Foreign Keys)"]
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
- **User Roles Supported:** Library Administrator, Operational Librarian, and Registered Student/Member.
- **Authentication Entry Point:** Provides credential verification, session initialization, and role resolution. The authentication layer ensures that only authorized personnel can access catalog modifications and bulk data import pipelines.

### 3.2 Library Management Interface
The presentation layer is developed using `CustomTkinter` and standard `tkinter` components to deliver a modern, low-overhead graphical desktop interface. It provides five distinct operational views:
1. **Catalog Search View:** Real-time search bar with interactive category filter dropdowns and instant tabular results.
2. **Issue & Return View:** Two-click checkout and check-in panels with instant book availability indicators and automatic overdue fine computation.
3. **Operational Performance Dashboard:** High-level overview cards presenting circulation KPIs, total catalog volumes, and search latency response distributions.
4. **Bulk CSV Import View:** File picker, schema preview, and progress visualizer for rapid ingestion of large book datasets.
5. **Analytics & Summary Reports View:** Filterable reporting grids for overdue loans, category distribution, and borrower activity.

### 3.3 Application Logic Layer
Written in modular Python 3, this layer coordinates business logic rules without coupling GUI components directly to raw SQL queries:
- **Search & Catalog Processing Service:** Sanitizes text queries, executes filtering logic, and computes latency metrics for quality control monitoring.
- **Issue & Return Processing Controller:** Enforces lending policies (maximum active loans, duplicate checkout prevention, loan period duration calculations, fine schedules).
- **Dashboard Metric Aggregator:** Collects snapshot metrics across books, members, and active loans to supply widget cards.
- **CSV Parser & Validator:** Verifies CSV headers, parses records, checks mandatory field constraints, and prepares clean tuples for ingestion.
- **Report Generation Service:** Assembles tabular summary views and formats CSV/PDF export streams.

### 3.4 Performance Optimization Layer (Q02 Engine)
This layer encapsulates the specific software engineering enhancements designed to satisfy **Q02 Improve Performance**:
- **Fast Search Engine:** Implements normalized prefix/substring search, selectively projects required columns to reduce memory overhead, and maintains transient result caches for high-frequency queries.
- **Streamlined Transaction Handler:** Consolidates loan status checks, borrow record insertions, and inventory decrementing into a single atomic sequence, preventing multiple table scans and lock stalls.
- **Fast Bulk Ingestion Pipeline:** Replaces individual row insertion statements with SQLite `executemany` operations wrapped in a single database transaction, boosting throughput to over 1,000 records per second.
- **Optimized Aggregation Engine:** Employs `pandas` vectorized grouping and aggregation for statistical summaries, avoiding repetitive Python iteration loops.
- **Real-Time Metric Aggregator:** Uses direct indexed count and aggregation queries to feed the dashboard in under 100 milliseconds.

### 3.5 Database Layer (SQLite3 Engine)
Data persistence is handled by an optimized SQLite 3 database utilizing:
- **Connection Optimization:** Centralized connection factory with `row_factory = sqlite3.Row` for efficient attribute mapping without dictionary reconstruction.
- **Foreign Key Integrity:** `PRAGMA foreign_keys = ON` ensuring referential integrity across users, books, and borrow records.
- **Strategic B-Tree Indexing:**
  - `idx_books_isbn_title` on `books(isbn, title)` for instant O(log N) lookup.
  - `idx_books_category` on `books(category)` for instant category filtering.
  - `idx_borrow_status_dates` on `borrow_records(status, due_date)` for zero-delay overdue scanning.
  - `idx_borrow_user_book` on `borrow_records(user_id, book_id, status)` for rapid circulation validation.

### 3.6 System Response & Operational Feedback Layer
Ensures prompt, deterministic user feedback:
- Instant UI table refresh (<50 ms target for search queries).
- Immediate visual confirmation alerts upon book issue/return.
- Reactive chart and KPI card re-rendering upon data updates.

---

## 4. Mapping of the Five Assigned Q02 Features

| Assigned Q02 Feature | Architectural Placement | Optimization Mechanism | Expected TQM Improvement |
|---|---|---|---|
| **1. Fast Search** | Interface & Search Logic & DB Indexes | Selective column projection, normalized LIKE queries with B-Tree indices, active query cache | Sub-50ms catalog retrieval; eliminates librarian wait time during desk queries |
| **2. Optimized Reports** | Report Service & Pandas Vectorizer | SQL group-by pushdown, vectorized pandas summaries, elimination of N+1 select loops | Report generation under 200ms across 10,000+ transaction records |
| **3. Dashboard** | Central GUI & Metric Aggregator | Lightweight COUNT/SUM query aggregation, cached visual rendering via Matplotlib canvas | Instant operational visibility; zero lag on dashboard tab switch (<100ms) |
| **4. CSV Import** | CSV Manager & Batch Pipeline | Parameterized `executemany()` batch processing inside a single atomic SQLite transaction commit | Ingestion rate > 1,000 rows/sec; reduces bulk catalog onboarding from minutes to seconds |
| **5. Efficient Database Queries** | Database Engine & Schema Definition | Explicit indexes on high-frequency columns, selective joins, elimination of `SELECT *` in loops | Reduction of query execution latency by 60% to 80% compared to unindexed scans |

---

## 5. Technology Stack Specifications

| Layer / Component | Technology | Rationale & Academic Justification |
|---|---|---|
| **Programming Language** | Python 3.10+ | Standard high-level language specified in BBAT104 curriculum; rapid prototyping, robust standard library. |
| **Graphical User Interface** | CustomTkinter / Tkinter | Modernized UI widgets, lightweight desktop execution without bulky web-browser runtimes. |
| **Relational Database** | SQLite 3 | Serverless, zero-configuration, ACID-compliant relational storage with full SQL support. |
| **Data Vectorization & Processing** | Pandas 2.2+ | High-efficiency vectorized data frames for reporting, aggregation, and CSV parsing. |
| **Visualization & SQC Analytics** | Matplotlib 3.8+ | Generation of performance control charts (Individual X-charts) and dashboard visualization. |
| **Development & Version Control** | VS Code & Git / GitHub | Standard IDE and distributed version control adhering to Review 1 university guidelines. |

---

## 6. Review 1 Architectural Verification

- [x] Represents the actual planned Python + SQLite system without phantom enterprise dependencies.
- [x] All 11 architectural components clearly specified and connected.
- [x] All five assigned Q02 performance features clearly identified and mapped.
- [x] Includes maintainable Mermaid source and vector graphic output.
- [x] Aligned with BBAT104 TQM quality objectives.
