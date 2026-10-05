# Library Management System

## BBAT104: Fundamentals of Total Quality Management

### Course Project 2026 to 2027

## Project Overview

This project is developed as part of the BBAT104 Fundamentals of Total Quality Management course project for the academic session 2026 to 2027.

The project focuses on developing a Library Management System using Python and SQLite. The system is designed to manage essential library operations through a structured software application while applying Total Quality Management principles throughout the development and quality improvement process.

The project combines software development with quality analysis techniques such as FMEA, SIPOC, CTQ analysis, Pareto Analysis, Fishbone Analysis, Checksheets, Defect Logging and the PDCA Continuous Improvement Cycle.

## Student Information

| Field | Details |
|---|---|
| Roll Number | 31 |
| Baseline Software System | Library Management System |
| Assigned Quality Goal | Q02 |
| Quality Goal Description | Improve Performance |
| Core TQM Objective | Optimize issue and return flow and catalog search speed |
| Academic Session | 2026 to 2027 |
| Course | BBAT104 Fundamentals of TQM |

## Review 1 Project Documentation

The project has completed all requirements for **Review 1** (Repository Initialization, System Architecture Flowchart, SRS Document, and Scope Definition):

| Deliverable | Document Link | Description |
|---|---|---|
| **Software Requirements Specification** | [docs/SRS.md](docs/SRS.md) | Full 16-section SRS covering functional, non-functional, system, database, and Q02 performance requirements |
| **Project Scope Definition** | [docs/Scope_Definition.md](docs/Scope_Definition.md) | Comprehensive In-Scope, Out-of-Scope, Boundaries, Objectives, Deliverables, and Success Criteria |
| **System Architecture Document** | [docs/System_Architecture.md](docs/System_Architecture.md) | Detailed 6-layer architecture specification mapping all 5 Q02 performance features |
| **Architecture Flowchart (Mermaid)** | [architecture/library_management_architecture.mmd](architecture/library_management_architecture.mmd) | Plain-text editable Mermaid source diagram |
| **Architecture Flowchart (SVG)** | [architecture/library_management_architecture.svg](architecture/library_management_architecture.svg) | Scalable vector graphics rendering for instant browser/evaluator viewing |

## Problem Statement

A library management system handles high volumes of book inquiries, member lookups, and circulation transactions (issue and return) daily. In traditional or baseline software systems, unindexed linear database scans, multi-step circulation updates, unoptimized report aggregations, and single-record catalog entries create operational latency bottlenecks and user interface freezes.

The objective of this project is to develop a functional **Library Management System** while systematically improving its performance (**Q02 Improve Performance**) by optimizing the issue and return flow and catalog search speed through disciplined software architecture and Total Quality Management practices.

## Project Objectives

The major objectives of the project are:

1. Develop a responsive, functional Library Management System using Python and SQLite.
2. Implement Create, Read, Update, and Delete operations for book, member, and circulation data.
3. Improve system performance according to the assigned Quality Goal **Q02 Improve Performance**.
4. Optimize catalog search to achieve sub-50 ms query execution latencies (**Fast Search**).
5. Streamline issue and return circulation transactions with atomic database operations and automatic fine calculations.
6. Restructure the SQLite persistence layer with strategic B-Tree indexing and parameterized queries (**Efficient Database Queries**).
7. Deploy vectorized data processing using Pandas to generate summaries in under 200 ms (**Optimized Reports**).
8. Provide an interactive visual control center reflecting operational KPIs and latencies in real time (**Dashboard**).
9. Implement a high-throughput batch ingestion pipeline capable of loading over 1,000 records/sec (**CSV Import**).
10. Apply Total Quality Management tools (SIPOC, CTQ, FMEA, Pareto, Fishbone, and SQC Control Charts) to measure and continuously improve software performance.
11. Apply the PDCA cycle for continuous quality improvement.
12. Maintain the project through GitHub version control with professional documentation.

## Assigned Quality Goal

### Q02: Improve Performance

According to the BBAT104 project guidelines, students assigned **Q02** are required to improve the performance of their baseline software system. The core operational objective is: **Optimize issue and return flow and catalog search speed**.

The assigned Q02 features are:

| Feature | Purpose | Expected Improvement |
|---|---|---|
| **Fast Search** | Multi-attribute substring/prefix search with selective projection | Sub-50 ms query latency for up to 10,000 catalog records |
| **Optimized Reports** | Vectorized Pandas aggregation for overdue, inventory, and circulation summaries | Report generation under 200 ms without procedural loop delays |
| **Dashboard** | Centralized operational overview with real-time KPI tiles and visual charts | Instant operational visibility; view switch latency under 100 ms |
| **CSV Import** | Bulk catalog data ingestion using parameterized `executemany` batch transactions | High-speed ingestion exceeding 1,000 records per second |
| **Efficient Database Queries** | Dedicated B-Tree indexing, row factories, and connection reuse | 60% to 80% reduction in query execution times compared to unindexed scans |

All five features are incorporated into this project as the performance improvement scope.

## Key System Features

### Fast Search (Q02 Feature)
Provides rapid, multi-attribute substring and prefix searching across titles, authors, and ISBNs with B-Tree indexing and selective column projection to achieve sub-50 ms query latencies.

### Optimized Reports (Q02 Feature)
Employs vectorized Pandas data processing to generate overdue, category distribution, and circulation summary reports in under 200 ms without procedural loop overhead.

### Performance Dashboard (Q02 Feature)
Provides an interactive real-time visual control center displaying core operational KPIs (active loans, catalog volume, overdue books) and query latency distributions.

### Bulk CSV Import (Q02 Feature)
Enables high-throughput automated onboarding of book catalogs from CSV spreadsheets using single-transaction `executemany` batch parameterization (>1,000 records/sec).

### Efficient Database Queries (Q02 Feature)
Utilizes strategic B-Tree indexing, SQLite row factories, parameterized queries, and connection optimization to minimize database latency and prevent table lock contention.

### Book Issue and Return Management
Provides a streamlined, two-click circulation workflow with atomic database transactions, instant stock counter restitution, and automatic overdue fine computation.

### Book Catalog and Member Management
Supports complete Create, Read, Update, and Delete (CRUD) operations for book bibliographic data and registered library member profiles.

### User Authentication & Role Control
Provides secure entry point verification, distinguishing permissions between system administrators, librarians, and student patrons.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3 |
| User Interface | Tkinter or CustomTkinter |
| Database | SQLite |
| Data Processing | Pandas |
| Quality Charts | Matplotlib and Seaborn |
| Development Environment | Visual Studio Code |
| Version Control | Git |
| Repository | GitHub |

## System Architecture

The system follows a structured application architecture in which the user interacts with the graphical interface, application logic processes the requested operation and the database layer manages persistent information.

The major components are:

1. User Interface Layer

2. Application Logic Layer

3. Authentication and Security Layer

4. Database Layer

5. Quality Analysis and Reporting Layer

## Database

SQLite is used for persistent data storage.

The database is responsible for maintaining the information required by the Library Management System, including relevant user, book, transaction and security related records.

Database design is structured to maintain data consistency and support the required CRUD operations.

## Total Quality Management Implementation

The project applies the following TQM principles.

### Customer Focus

The system is designed around the operational requirements of library users and administrators.

### Continuous Improvement

The PDCA cycle is used to identify problems, implement improvements, evaluate results and determine further corrective actions.

### Process Centric Approach

The major processes of the system are analysed using SIPOC mapping to understand suppliers, inputs, processes, outputs and customers.

### Fact Based Decision Making

Defect records and quality measurements are used to identify areas requiring improvement.

### Error Prevention

Input validation and other preventive controls are incorporated to reduce the occurrence of errors during system operation.

## Quality Management Tools

### FMEA

Failure Mode and Effects Analysis is used to identify possible system failures and evaluate their associated risks.

Risk Priority Number is calculated using:

RPN = Severity × Occurrence × Detection

The resulting risk values are used to identify areas requiring attention and define appropriate mitigation measures.

### SIPOC

A SIPOC process map is prepared to understand the major processes of the Library Management System and their relationship with suppliers, inputs, processes, outputs and customers.

### CTQ Tree

Critical to Quality parameters are identified to define the important quality requirements of the system.

### Checksheets

Checksheets are used to record and organise defect information in a structured manner.

### Defect Log

Software defects are documented along with their relevant information, status and resolution.

### Pareto Analysis

A Pareto Chart is used to analyse defect frequencies and identify the major categories contributing to software errors.

### Fishbone Diagram

An Ishikawa Fishbone Diagram is used to identify possible root causes of observed defects by categorising causes related to people, process, software code and infrastructure.

### PDCA Cycle

The Plan, Do, Check and Act cycle is applied as a continuous improvement mechanism.

## Project Development Process

The project follows the development process specified in the BBAT104 project guidelines.

### Step 1: Environment Setup and Repository Initialization

Python, Visual Studio Code and GitHub are configured and the project repository is created.

### Step 2: Requirement Analysis and SRS

The requirements of the Library Management System are analysed and the Software Requirements Specification document is prepared.

### Step 3: Base System and CRUD Development

The core Library Management System is developed with the required CRUD operations using Python and SQLite.

### Step 4: Performance Feature Integration

The five features associated with Quality Goal Q02 (Fast Search, Optimized Reports, Dashboard, CSV Import, and Efficient Database Queries) are implemented and integrated into the system.

### Step 5: Process Mapping and Risk Analysis

SIPOC analysis, CTQ identification and FMEA are performed to analyse system processes and potential risks.

### Step 6: Statistical Quality Control

Defects are recorded through checksheets and defect logs. Pareto Charts and Fishbone Diagrams are prepared to analyse software quality problems.

### Step 7: Continuous Improvement

The PDCA cycle is used to implement and document quality improvements.

### Step 8: Documentation and Version Control

Project development is maintained through GitHub with regular commits. Documentation includes the README, system architecture, user manual and relevant quality analysis documents.

## Project Deliverables

The project documentation and implementation include:

1. Functional Library Management System

2. System Architecture Flowchart

3. Software Requirements Specification

4. CRUD Modules

5. Five Q02 Performance Features

6. CTQ Tree

7. SIPOC Process Map

8. FMEA Matrix

9. Defect Log

10. Checksheets

11. Pareto Chart

12. Fishbone Diagram

13. PDCA Cycle Documentation

14. User Manual

15. GitHub Repository

16. Project README

17. Final Software Demonstration

18. Viva Preparation

## GitHub Repository

The project source code, documentation and development history are maintained in the GitHub repository created according to the BBAT104 project requirements.

Regular commits are maintained to demonstrate the development progress and version history of the project.

## Conclusion

The Library Management System demonstrates the application of software development principles together with Total Quality Management practices.

The project focuses particularly on improving system performance (Q02) by optimizing the issue and return flow and catalog search speed through fast search, optimized reports, dashboard, CSV import, and efficient database queries. Quality management tools such as FMEA, SIPOC, CTQ, Pareto Analysis, Fishbone Analysis, Checksheets and PDCA are incorporated to systematically identify, analyse and improve software quality.

The overall objective is to develop a functional, high-performance Library Management System while demonstrating the practical application of Total Quality Management principles in software development.