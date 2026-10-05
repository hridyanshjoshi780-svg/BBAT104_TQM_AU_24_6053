# Project Scope Definition Document

## Library Management System
### BBAT104: Fundamentals of Total Quality Management
**Academic Session:** 2026 to 2027  
**Roll Number:** 31  
**Assigned Quality Goal:** Q02 Improve Performance  
**Core TQM Goal:** Optimize issue and return flow and catalog search speed  
**Project Milestone:** Review 1  
**Document Version:** 1.0  

---

## 1. Executive Summary

This document establishes the formal boundaries, deliverable commitments, exclusions, and evaluation criteria for the **Library Management System** developed under **BBAT104 Fundamentals of Total Quality Management** for the **2026 to 2027** academic session. 

The baseline software system addresses core institutional library operations, while serving as the practical testbed for applying Total Quality Management principles. In accordance with the student's assigned topic, this project centers on **Q02 Improve Performance**, with the primary operational objective being to **Optimize issue and return flow and catalog search speed**.

---

## 2. Project Objectives

The project is structured around specific technical and quality objectives aligned with the BBAT104 curriculum:

1. **Circulation Workflow Optimization:** Minimize the time required to complete book checkout and check-in transactions by establishing atomic database routines and automated fine calculation.
2. **Catalog Search Acceleration:** Implement an indexed search engine capable of filtering thousands of catalog items by title, author, category, or ISBN with sub-50 ms latency.
3. **Database Efficiency:** Optimize the SQLite data access layer through strategic B-Tree indexing, parameterized batch operations, and connection settings, eliminating full-table scans.
4. **Data Aggregation & Reporting:** Deploy vectorized Pandas data pipelines to aggregate inventory summaries, overdue books, and borrowing histories in under 200 ms.
5. **Operational Visibility:** Provide an interactive dashboard displaying circulation KPIs, inventory counts, and query performance metrics in real time.
6. **High-Throughput Ingestion:** Build an automated bulk CSV import mechanism capable of onboarding external book catalogs at rates exceeding 1,000 records per second.
7. **TQM & Statistical Quality Control Integration:** Apply quality management tools (SIPOC, CTQ tree, FMEA, Fishbone diagram, Pareto analysis, and Statistical Process Control charts) to monitor and optimize software response times.

---

## 3. Project Boundaries

The boundaries of the project define the execution context:
- **Application Type:** Standalone desktop application.
- **Operating Environment:** Local workstation (cross-platform: Linux, Windows, macOS).
- **Execution Domain:** Single-library circulation counter and administrative desk.
- **Data Persistence:** Local, embedded SQLite relational database (`library.db`).
- **User Interface:** Modern desktop GUI developed using CustomTkinter / Tkinter.

---

## 4. In Scope

The items listed below are strictly within the functional, technical, and analytical scope of this course project:

### 4.1 Core Library Management Operations
- **Book Catalog Management:** Adding new titles, editing bibliographic records (title, author, ISBN, category, total copies), and managing available shelf stock.
- **Member Management:** Registering library members (students and administrators), maintaining profile records, and tracking member borrowing statuses.
- **Book Issue Workflow:** Validating member eligibility, verifying real-time copy availability, recording loan dates and due dates, and updating stock counters.
- **Book Return Workflow:** Processing returned items, restoring inventory counts, determining elapsed loan periods, and computing overdue fines automatically.
- **Catalog Search:** Multi-field searching (title, author, ISBN) with real-time category filtering.

### 4.2 Assigned Q02 Performance Features
1. **Fast Search:**
   - Multi-criteria substring and prefix search matching.
   - B-Tree indexed search queries (`idx_books_isbn_title`, `idx_books_category`).
   - Selective SQL column projection to eliminate redundant memory bandwidth.
   - Target query latency: $\le$ 50 milliseconds.
2. **Optimized Reports:**
   - Vectorized data processing using Pandas.
   - Aggregated reports for overdue items, category distribution, and borrowing frequency.
   - Elimination of nested procedural query loops (solving the N+1 problem).
   - Target generation latency: $\le$ 200 milliseconds.
3. **Dashboard:**
   - Central visual summary interface with real-time operational KPI tiles.
   - Aggregated counts of total titles, active checkouts, overdue books, and registered members.
   - Visual charts rendered via Matplotlib.
   - Target load latency: $\le$ 100 milliseconds.
4. **CSV Import:**
   - Automated ingestion of external book catalogs in standard `.csv` format.
   - In-memory validation of mandatory fields and ISBN format.
   - Bulk insertion using SQLite `executemany` enclosed within a single database transaction.
   - Ingestion throughput target: $\ge$ 1,000 records per second.
5. **Efficient Database Queries:**
   - Implementation of primary and foreign key constraints (`PRAGMA foreign_keys = ON`).
   - Creation and maintenance of dedicated performance B-Tree indices.
   - Utilization of `sqlite3.Row` row factories for zero-copy column access.
   - Parameterized SQL statements to ensure query plan caching and prevent injection vulnerabilities.

### 4.3 Database Architecture & Operations
- Relational SQLite schema comprising `users`, `books`, `borrow_records`, `search_metrics`, and `audit_logs`.
- Database initialization and automated sample seeding on startup.
- Complete ACID-compliant transactional consistency across all insert, update, and delete actions.

### 4.4 Total Quality Management (TQM) Deliverables
- **SIPOC Process Map:** Mapping Suppliers, Inputs, Processes, Outputs, and Customers for catalog search and book circulation.
- **CTQ Tree (Critical to Quality):** Defining customer needs, quality drivers, and measurable performance requirements.
- **FMEA Matrix (Failure Mode and Effects Analysis):** Risk assessment identifying software failure modes, calculating Risk Priority Numbers (RPN), and outlining mitigation controls.
- **Checksheets & Defect Logging:** Structured recording of performance anomalies and software exceptions.
- **Pareto Analysis & Fishbone Diagram:** Statistical root-cause investigation of system latency and circulation bottlenecks.
- **Statistical Quality Control (SQC) Control Charts:** Generation of Individual X-Charts with Upper Control Limits (UCL), Mean ($\bar{X}$), and Lower Control Limits (LCL) to evaluate search latency stability.
- **PDCA Cycle Documentation:** Systematic record of continuous improvement iterations.

---

## 5. Out of Scope

The following capabilities are deliberately excluded from the project scope to preserve focus on the core desktop performance objectives and prevent scope creep:

1. **Online Payment Gateway Integration:** The system will not process electronic debit/credit card or UPI payments for overdue fines. Fines are calculated and tracked internally; monetary settlement is handled externally at the physical library counter.
2. **Multi-Branch Inter-Library Network:** The system does not support distributed multi-campus synchronization or inter-library loan logistics.
3. **Hardware Automation & Robotics:** Automated book return sorting machines, RFID gantry gates, and robotic book retrieval mechanisms are excluded.
4. **Public Cloud Web Hosting & Mobile Apps:** The project does not include iOS/Android mobile applications or public cloud SaaS hosting.
5. **Automated External Communication Gateways:** Integration with commercial SMS gateways or institutional SMTP servers for automated messaging is excluded from this baseline.
6. **Digital Rights Management (DRM) & E-Book Reading:** The system manages physical library inventory and circulation records; digital content delivery and e-reader DRM are out of scope.

---

## 6. Primary Users & Stakeholder Roles

| Stakeholder Role | System Responsibilities | Primary Needs in Scope |
|---|---|---|
| **Library Administrator** | System governance, inventory oversight, quality management | Bulk CSV onboarding, global audit reports, operational dashboard, performance monitoring |
| **Operational Librarian** | Desk circulation, front-counter assistance | Fast catalog lookup, 2-click book issue/return, automated fine calculation |
| **Student / Member** | Library patron, reader | Quick title availability inquiry, loan status inspection |
| **Course Evaluator** | Academic assessment for BBAT104 Review milestones | Verification of Q02 performance targets, TQM artifacts, architecture, and code quality |

---

## 7. Major Deliverables Across Course Milestones

The project deliverables are organized across the academic evaluation milestones:

### Review 1 Deliverables (Current Milestone)
1. **GitHub Repository Initialization:** Fully configured Git repository with remote origin, clean branch management, and foundational source tracking.
2. **System Architecture Flowchart:** Comprehensive architecture diagram (Mermaid `.mmd`, vector `.svg`, and documentation `.md`) mapping all 11 architectural layers and 5 Q02 performance features.
3. **Software Requirements Specification (SRS):** Full 16-section academic specification document covering functional, non-functional, system, database, and Q02 performance requirements.
4. **Scope Definition Document:** Detailed definition of In-Scope, Out-of-Scope, Objectives, Boundaries, Deliverables, and Success Criteria.
5. **Project README Update:** Synchronized documentation hub with clear links to Review 1 deliverables.

### Subsequent Review Milestones (Planned)
- **Review 2 (Core Development & Q02 Implementation):** Full Python/SQLite CRUD modules, Fast Search engine, CSV Import batch pipeline, Performance Dashboard, and Vectorized Reports.
- **Review 3 (TQM & Quality Analysis):** Comprehensive SIPOC, CTQ tree, FMEA risk matrix, Defect checksheets, Pareto charts, Fishbone root-cause diagrams, and SQC Control Charts.
- **Review 4 / Final Submission:** Final software demonstration, user manual, PDCA continuous improvement documentation, and viva defense preparation.

---

## 8. Quality Goal: Q02 Improve Performance

The assigned Quality Goal is strictly **Q02 Improve Performance**. Under TQM philosophy, software performance is a key quality attribute that directly determines user satisfaction, operational throughput, and process capability.

The project addresses this goal through the systematic optimization of five targeted features:

```
[Quality Goal: Q02 Improve Performance]
             │
             ├── 1. Fast Search (Indexed multi-field search, selective projection, <50ms)
             ├── 2. Optimized Reports (Vectorized Pandas aggregation, sub-200ms)
             ├── 3. Dashboard (Consolidated operational KPIs and visual charts, <100ms)
             ├── 4. CSV Import (Batch executemany ingestion, >1,000 records/sec)
             └── 5. Efficient Database Queries (B-Tree indexes, row factory, PRAGMA tuning)
```

---

## 9. Success Criteria

The success of the project will be evaluated against the following quantitative and qualitative criteria:

### Quantitative Performance Metrics
- **Catalog Search Latency:** Average execution latency of under **50 ms** across test queries on a 10,000-book catalog.
- **Circulation Issue / Return Latency:** Single-transaction execution latency of under **50 ms**.
- **Bulk CSV Ingestion Speed:** Ingestion throughput exceeding **1,000 records per second** without database lock failures.
- **Report Generation Speed:** Production of overdue and inventory summary reports in under **200 ms**.
- **SQC Process Capability:** Catalog search latency maintained within statistical control limits ($\pm 3\sigma$) on the Individual X-Chart.

### Qualitative & Academic Criteria
- **Compliance with BBAT104 Guidelines:** Complete fulfillment of all university project guidelines for the 2026–2027 academic session.
- **Traceability:** Full alignment between the SRS, Scope Definition, Architecture Flowchart, and implementation modules.
- **Code Cleanliness:** Modular Python codebase following PEP 8 conventions, with separation of concerns and no redundant code.
- **Documentation Rigor:** Complete, professional, and evaluator-ready documentation with no placeholder or misleading content.

---

## 10. Assumptions & Constraints

### Assumptions
1. The target environment possesses Python 3.10+ and standard library access with write permissions to the local project folder.
2. Ingested CSV files follow standard UTF-8 formatting with column headers matching system specifications.
3. The baseline software system operates on a single workstation counter per physical circulation desk.

### Constraints
1. **Academic Scope:** The project must be developed individually by Roll Number 31, adhering strictly to BBAT104 guidelines.
2. **Local Concurrency:** SQLite does not support simultaneous multi-process write transactions; queries must execute via sequential connection handling.
3. **No External Paid Infrastructure:** The system must run entirely on free, open-source tools (Python, SQLite, Tkinter, Pandas, Matplotlib) without relying on paid cloud services.
