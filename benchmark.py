"""
Performance Benchmark Suite for BBAT104 TQM Library Management System (Quality Goal: Q02).
Quantitatively evaluates and validates the official Review 1 / Review 2 performance targets:
1. Fast Search Latency (Target: <= 50 ms)
2. Issue & Return Transaction Latency (Target: <= 50 ms)
3. Bulk CSV Ingestion Throughput (Target: >= 1,000 records/sec)
4. Vectorized Reports Generation Latency (Target: <= 200 ms)
5. Dashboard Aggregation Load Latency (Target: <= 100 ms)
6. Single-Record B-Tree Indexed Lookup (Target: <= 10 ms)

Executes against an isolated synthetic test dataset and prints an evidence-based quality report.
"""

import os
import sys
import tempfile
import time
import random
import statistics

from database import init_db, get_connection
from auth import register_user
from library_service import (
    search_books, issue_book, return_book,
    get_dashboard_metrics, get_report_inventory_distribution,
    get_report_currently_issued, get_report_overdue_books,
    get_report_circulation_activity, get_report_member_summary,
    import_books_from_csv
)


def run_benchmark():
    print("=" * 80)
    print(" BBAT104 TOTAL QUALITY MANAGEMENT (TQM) — PERFORMANCE BENCHMARK (Q02)")
    print(f" Python: {sys.version.split()[0]} | Platform: {sys.platform}")
    print("=" * 80)

    # 1. Setup isolated benchmarking database
    temp_dir = tempfile.TemporaryDirectory()
    bench_db = os.path.join(temp_dir.name, "bench_library.db")
    os.environ["DATABASE_PATH"] = bench_db
    init_db(bench_db)

    print("\n[*] Populating synthetic benchmark catalog dataset (3,000 books, 300 members)...")
    conn = get_connection(bench_db)
    cur = conn.cursor()

    categories = ["Computer Science", "Management", "Quality Engineering", "Mathematics", "Literature", "Physics"]
    sample_books = []
    for i in range(1, 3001):
        cat = categories[i % len(categories)]
        sample_books.append((
            f"Benchmark Book Title Vol {i}",
            f"Author Name {i % 150}",
            f"978-BENCH-{i:06d}",
            cat,
            5,
            5,
            1
        ))

    cur.executemany(
        """INSERT INTO books (title, author, isbn, category, total_copies, available_copies, is_active)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        sample_books
    )

    # Seed members
    for m in range(1, 301):
        cur.execute(
            """INSERT INTO users (username, password_hash, salt, role, full_name, email, is_active)
               VALUES (?, 'hash', 'salt', 'student', ?, ?, 1)""",
            (f"bench_user_{m}", f"Benchmark Student {m}", f"user_{m}@bench.edu")
        )

    # Seed 1,000 historical borrow records
    borrows = []
    base_time = time.time() - (30 * 86400)
    for b in range(1, 1001):
        book_id = (b % 3000) + 1
        user_id = (b % 300) + 1
        b_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(base_time + b * 1800))
        d_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(base_time + b * 1800 + 14 * 86400))
        status = "RETURNED" if b % 4 != 0 else "BORROWED"
        ret_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(base_time + b * 1800 + 10 * 86400)) if status == "RETURNED" else None
        borrows.append((book_id, user_id, b_time, d_time, ret_time, status, 0.0 if status == "RETURNED" else 0.0))

    cur.executemany(
        """INSERT INTO borrow_records (book_id, user_id, borrow_date, due_date, return_date, status, fine_amount)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        borrows
    )
    conn.commit()
    conn.close()
    print("    Catalog seeded: 3,000 books, 300 members, 1,000 circulation transactions.\n")

    results = []

    # -------------------------------------------------------------------------
    # TEST 1: CATALOG FAST SEARCH
    # -------------------------------------------------------------------------
    search_queries = ["Title Vol 10", "Author Name 25", "BENCH-001", "Management", "Computer", "NonexistentXYZ"]
    search_latencies = []
    for _ in range(50):
        q = random.choice(search_queries)
        t0 = time.perf_counter()
        books, _ = search_books(query=q, limit=20, record_metric=False)
        t1 = time.perf_counter()
        search_latencies.append((t1 - t0) * 1000.0)

    avg_search = statistics.mean(search_latencies)
    p95_search = sorted(search_latencies)[int(len(search_latencies) * 0.95)]
    results.append({
        "feature": "1. Fast Search Latency",
        "target": "<= 50.0 ms",
        "mean": f"{avg_search:.2f} ms",
        "p95": f"{p95_search:.2f} ms",
        "status": "PASS" if avg_search <= 50.0 else "FAIL",
        "note": f"Evaluated across 50 runs on 3,000 titles catalog"
    })

    # -------------------------------------------------------------------------
    # TEST 2: ISSUE & RETURN CIRCULATION TRANSACTIONS
    # -------------------------------------------------------------------------
    issue_latencies = []
    return_latencies = []
    for i in range(1, 31):
        book_id = 500 + i
        user_id = 100 + i
        t0 = time.perf_counter()
        issue_res = issue_book(book_id=book_id, user_id=user_id, username="admin", loan_days=14)
        t1 = time.perf_counter()
        issue_latencies.append((t1 - t0) * 1000.0)

        record_id = issue_res["record_id"]
        t2 = time.perf_counter()
        return_book(record_id=record_id, username="admin")
        t3 = time.perf_counter()
        return_latencies.append((t3 - t2) * 1000.0)

    circ_latencies = issue_latencies + return_latencies
    avg_circ = statistics.mean(circ_latencies)
    p95_circ = sorted(circ_latencies)[int(len(circ_latencies) * 0.95)]
    results.append({
        "feature": "2. Issue/Return Latency",
        "target": "<= 50.0 ms",
        "mean": f"{avg_circ:.2f} ms",
        "p95": f"{p95_circ:.2f} ms",
        "status": "PASS" if avg_circ <= 50.0 else "FAIL",
        "note": "Evaluated across 60 atomic operations"
    })

    # -------------------------------------------------------------------------
    # TEST 3: BULK CSV INGESTION PIPELINE
    # -------------------------------------------------------------------------
    batch_size = 2000
    csv_lines = ["title,author,isbn,category,copies"]
    for i in range(1, batch_size + 1):
        csv_lines.append(f"Ingested Book {i},Batch Author {i},978-BULK-{i:06d},Computer Science,3")
    csv_payload = "\n".join(csv_lines)

    import_summary = import_books_from_csv(csv_payload, admin_user="admin")
    throughput = import_summary["throughput_per_sec"]
    results.append({
        "feature": "3. Bulk CSV Ingestion",
        "target": ">= 1,000 rec/sec",
        "mean": f"{throughput:.1f} rec/s",
        "p95": f"{import_summary['duration_ms']:.1f} ms total",
        "status": "PASS" if throughput >= 1000.0 else "FAIL",
        "note": f"Ingested {import_summary['inserted']} records in {import_summary['duration_ms']} ms"
    })

    # -------------------------------------------------------------------------
    # TEST 4: VECTORIZED REPORTS GENERATION
    # -------------------------------------------------------------------------
    report_latencies = []
    for _ in range(25):
        t0 = time.perf_counter()
        get_report_inventory_distribution()
        get_report_currently_issued()
        get_report_overdue_books()
        get_report_circulation_activity()
        get_report_member_summary()
        t1 = time.perf_counter()
        report_latencies.append((t1 - t0) * 1000.0)

    avg_reports = statistics.mean(report_latencies)
    p95_reports = sorted(report_latencies)[int(len(report_latencies) * 0.95)]
    results.append({
        "feature": "4. Optimized Reports Latency",
        "target": "<= 200.0 ms",
        "mean": f"{avg_reports:.2f} ms",
        "p95": f"{p95_reports:.2f} ms",
        "status": "PASS" if avg_reports <= 200.0 else "FAIL",
        "note": "5 full analytical reports across 5,000+ records"
    })

    # -------------------------------------------------------------------------
    # TEST 5: DASHBOARD AGGREGATION LOAD TIME
    # -------------------------------------------------------------------------
    dash_latencies = []
    for _ in range(50):
        t0 = time.perf_counter()
        get_dashboard_metrics()
        t1 = time.perf_counter()
        dash_latencies.append((t1 - t0) * 1000.0)

    avg_dash = statistics.mean(dash_latencies)
    p95_dash = sorted(dash_latencies)[int(len(dash_latencies) * 0.95)]
    results.append({
        "feature": "5. Dashboard Metric Aggregation",
        "target": "<= 100.0 ms",
        "mean": f"{avg_dash:.2f} ms",
        "p95": f"{p95_dash:.2f} ms",
        "status": "PASS" if avg_dash <= 100.0 else "FAIL",
        "note": "Complete 8-KPI snapshot & distribution aggregations"
    })

    # -------------------------------------------------------------------------
    # TEST 6: SINGLE-RECORD B-TREE INDEXED LOOKUP
    # -------------------------------------------------------------------------
    conn = get_connection(bench_db)
    cur = conn.cursor()
    lookup_latencies = []
    for _ in range(100):
        isbn = f"978-BENCH-{random.randint(1, 3000):06d}"
        t0 = time.perf_counter()
        cur.execute("SELECT id, title, available_copies FROM books WHERE isbn = ?", (isbn,))
        cur.fetchone()
        t1 = time.perf_counter()
        lookup_latencies.append((t1 - t0) * 1000.0)
    conn.close()

    avg_lookup = statistics.mean(lookup_latencies)
    p95_lookup = sorted(lookup_latencies)[int(len(lookup_latencies) * 0.95)]
    results.append({
        "feature": "6. B-Tree Indexed Point Lookup",
        "target": "<= 10.0 ms",
        "mean": f"{avg_lookup:.3f} ms",
        "p95": f"{p95_lookup:.3f} ms",
        "status": "PASS" if avg_lookup <= 10.0 else "FAIL",
        "note": "Direct index seek on idx_books_isbn"
    })

    # -------------------------------------------------------------------------
    # PRINT RESULTS TABLE
    # -------------------------------------------------------------------------
    print("-" * 105)
    print(f"{'Performance Metric':<32} | {'SRS Target':<16} | {'Measured (Mean)':<16} | {'95th %ile':<14} | {'Status':<10}")
    print("-" * 105)
    for r in results:
        print(f"{r['feature']:<32} | {r['target']:<16} | {r['mean']:<16} | {r['p95']:<14} | {r['status']:<10}")
    print("-" * 105)

    print("\n[+] Benchmark Verification Notes:")
    for r in results:
        print(f"  - {r['feature']}: {r['note']} ({r['status']})")
    print("\n" + "=" * 80 + "\n")

    # Cleanup temp resources
    temp_dir.cleanup()
    os.environ.pop("DATABASE_PATH", None)


if __name__ == "__main__":
    run_benchmark()
