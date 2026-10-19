"""
Comprehensive Automated Test Suite for BBAT104 TQM Library Management System (Review 2).
Covers:
- Authentication, input validation, and password reset
- Book CRUD operations and referential integrity safeguards
- Member CRUD operations and loan protection safeguards
- Q02 Fast Search (multi-attribute, case-insensitive, category, availability, query plan)
- Q02 Circulation atomic transactions (issue, return, duplicate prevention, stock decrement/increment)
- Q02 Operational Dashboard aggregations and response time
- Q02 Optimized Reports (inventory, issued, overdue, circulation, member summary, CSV export)
- Q02 Bulk CSV Ingestion (header validation, duplicate skipping, batch performance)
- SQC Control Chart statistical limits (UCL, Mean, LCL)
- Web Browser Routes and Production /health endpoint
- Persistence across connections

Uses an isolated temporary database to guarantee zero disruption to the user's live database.
"""

import os
import tempfile
import subprocess
import sys
import unittest
import csv
import io
import time
from datetime import datetime, timedelta
from unittest.mock import patch

from database import init_db, get_connection, explain_query
from auth import (
    authenticate_user, register_user, reset_password,
    validate_username, validate_email, validate_password,
    ValidationError
)
from library_service import (
    search_books, search_books_paginated, explain_catalog_search,
    get_all_categories, add_book, get_book, update_book, delete_book,
    get_all_members, get_member, update_member, delete_member,
    issue_book, return_book, get_borrow_records, get_active_loans,
    get_dashboard_metrics, get_report_inventory_distribution,
    get_report_currently_issued, get_report_overdue_books,
    get_report_circulation_activity, get_report_member_summary,
    export_report_to_csv, import_books_from_csv, get_sample_csv_template,
    get_audit_logs
)
from sqc_analysis import generate_sqc_chart
from web_app import app


class TestLibraryManagementSystemReview2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create an isolated temporary SQLite database
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.test_db_path = os.path.join(cls.temp_dir.name, "test_library.db")
        cls.original_database_path = os.environ.get("DATABASE_PATH")
        os.environ["DATABASE_PATH"] = cls.test_db_path
        init_db(cls.test_db_path)

        # Flask test client
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key-123"
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        if cls.original_database_path is None:
            os.environ.pop("DATABASE_PATH", None)
        else:
            os.environ["DATABASE_PATH"] = cls.original_database_path
        cls.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. AUTHENTICATION & INPUT VALIDATION
    # -------------------------------------------------------------------------

    def test_01_authentication_admin(self):
        user = authenticate_user("admin", "admin123", expected_role="admin")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "admin")
        self.assertEqual(user["role"], "admin")

    def test_02_authentication_student(self):
        user = authenticate_user("student1", "student123", expected_role="student")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "student")

    def test_03_invalid_login_rejection(self):
        user = authenticate_user("admin", "wrongpassword")
        self.assertIsNone(user)

        user_nonexistent = authenticate_user("ghost_user", "password123")
        self.assertIsNone(user_nonexistent)

    def test_04_role_mismatch_rejection(self):
        # Student attempting admin login
        user = authenticate_user("student1", "student123", expected_role="admin")
        self.assertIsNone(user)

    def test_05_input_validation(self):
        with self.assertRaises(ValidationError):
            validate_username("ab")  # Too short
        with self.assertRaises(ValidationError):
            validate_username("user!name#")  # Special chars
        with self.assertRaises(ValidationError):
            validate_email("not-an-email")
        with self.assertRaises(ValidationError):
            validate_password("12345")  # Less than 6 chars

    def test_06_registration_and_password_reset(self):
        reg = register_user("new_user_test", "securePass123", "New Tester", "tester@unit.edu", role="student")
        self.assertEqual(reg["username"], "new_user_test")
        self.assertEqual(reg["role"], "student")

        # Duplicate username rejection
        with self.assertRaises(ValidationError):
            register_user("new_user_test", "securePass123", "Duplicate", "other@unit.edu")

        # Reset password
        reset_ok = reset_password("new_user_test", "tester@unit.edu", "newSecurePassword1")
        self.assertTrue(reset_ok)

        # Authenticate with new password
        auth_user = authenticate_user("new_user_test", "newSecurePassword1")
        self.assertIsNotNone(auth_user)

    # -------------------------------------------------------------------------
    # 2. BOOK CRUD OPERATIONS (Phase Three)
    # -------------------------------------------------------------------------

    def test_07_book_create_and_read(self):
        new_book = add_book(
            title="TQM Quality Engineering Manual",
            author="Hridyansh Joshi",
            isbn="978-9999000011",
            category="Quality Engineering",
            copies=5,
            admin_user="admin"
        )
        self.assertIn("id", new_book)
        self.assertEqual(new_book["isbn"], "978-9999000011")

        # Read book back
        fetched = get_book(new_book["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["title"], "TQM Quality Engineering Manual")
        self.assertEqual(fetched["available_copies"], 5)
        self.assertEqual(fetched["total_copies"], 5)

    def test_08_book_duplicate_isbn_rejection(self):
        with self.assertRaises(ValidationError):
            add_book(
                title="Another Book With Same ISBN",
                author="Someone Else",
                isbn="978-9999000011",  # Duplicate
                category="Management",
                copies=2,
                admin_user="admin"
            )

    def test_09_book_update_and_stock_consistency(self):
        books, _ = search_books(query="Quality Engineering Manual")
        book = books[0]

        # Update metadata
        updated = update_book(
            book_id=book["id"],
            title="TQM Quality Engineering Handbook 2nd Ed",
            author="Hridyansh Joshi",
            isbn=book["isbn"],
            category="Quality Engineering",
            copies=8,
            admin_user="admin"
        )
        self.assertEqual(updated["title"], "TQM Quality Engineering Handbook 2nd Ed")

        fetched = get_book(book["id"])
        self.assertEqual(fetched["total_copies"], 8)
        self.assertEqual(fetched["available_copies"], 8)

    def test_10_book_delete_with_safeguards(self):
        # Create a disposable book
        temp_book = add_book("Temporary Test Book", "Test Author", "978-0000000001", "Testing", 1, "admin")
        book_id = temp_book["id"]

        # Delete with no history -> permanent delete
        res = delete_book(book_id, admin_user="admin")
        self.assertEqual(res["status"], "permanently deleted")

        # Verify not in active catalog
        fetched = get_book(book_id)
        self.assertIsNone(fetched)

    # -------------------------------------------------------------------------
    # 3. MEMBER CRUD OPERATIONS (Phase Three)
    # -------------------------------------------------------------------------

    def test_11_member_crud_lifecycle(self):
        # Register new student member
        mem = register_user("student_member_1", "pass1234", "Student Member One", "student1_mem@edu.com", "student")
        user_id = mem["id"]

        # Read member details
        details = get_member(user_id)
        self.assertIsNotNone(details)
        self.assertEqual(details["username"], "student_member_1")
        self.assertEqual(details["active_loans"], 0)

        # Update member profile
        upd = update_member(user_id, "Student Member One Updated", "student1_mem@edu.com", "student", "admin")
        self.assertEqual(upd["full_name"], "Student Member One Updated")

        # Delete member without active loans
        del_res = delete_member(user_id, admin_user="admin")
        self.assertIn("deleted", del_res["status"])

    # -------------------------------------------------------------------------
    # 4. Q02 FAST SEARCH (Phase Four - Feature 1)
    # -------------------------------------------------------------------------

    def test_12_fast_search_exact_and_partial(self):
        # Partial match on Title
        books, latency = search_books(query="clean")
        self.assertGreaterEqual(len(books), 1)
        self.assertTrue(any("Clean Code" in b["title"] for b in books))
        self.assertGreater(latency, 0.0)

        # Partial match on Author
        books, _ = search_books(query="Besterfield")
        self.assertGreaterEqual(len(books), 1)
        self.assertTrue(any("Total Quality Management" in b["title"] for b in books))

        # Exact / substring match on ISBN
        books, _ = search_books(query="978-0130993069")
        self.assertEqual(len(books), 1)

    def test_13_fast_search_case_insensitivity_and_special_chars(self):
        # Lowercase search
        books_lower, _ = search_books(query="python")
        # Uppercase search
        books_upper, _ = search_books(query="PYTHON")
        self.assertEqual(len(books_lower), len(books_upper))

        # Special characters
        books_special, latency = search_books(query="--' OR 1=1;--")
        # Parameterized query safely yields 0 results without SQL injection error
        self.assertEqual(len(books_special), 0)

    def test_14_fast_search_category_and_availability_filters(self):
        # Category filter
        books, _ = search_books(category="Computer Science")
        self.assertTrue(all(b["category"] == "Computer Science" for b in books))

        # Availability filter
        avail_books, _ = search_books(availability="Available")
        self.assertTrue(all(b["available_copies"] > 0 for b in avail_books))

    def test_15_fast_search_query_plan_uses_index(self):
        # Explain query plan for indexed search
        plan = explain_catalog_search("Total Quality", category="Management")
        self.assertIsInstance(plan, list)
        self.assertGreater(len(plan), 0)
        details = [str(step.get("detail", "")) for step in plan]
        self.assertTrue(any("VIRTUAL TABLE INDEX" in d for d in details))
        category_plan = explain_catalog_search(category="Management")
        self.assertTrue(any("idx_books_category" in str(step.get("detail", "")) for step in category_plan))

    # -------------------------------------------------------------------------
    # 5. Q02 ISSUE AND RETURN CIRCULATION (Phase Five & Feature 5)
    # -------------------------------------------------------------------------

    def test_16_circulation_issue_and_return_cycle(self):
        # Find a book with available copies
        books, _ = search_books(availability="Available")
        book = books[0]
        initial_avail = book["available_copies"]

        user = authenticate_user("student1", "student123")
        self.assertIsNotNone(user)

        # 1. Issue book
        issue_res = issue_book(book["id"], user["id"], username="admin", loan_days=14)
        self.assertIn("record_id", issue_res)
        self.assertIn("due_date", issue_res)
        self.assertGreater(issue_res["duration_ms"], 0.0)

        # Verify available copies decremented atomically
        updated_book = get_book(book["id"])
        self.assertEqual(updated_book["available_copies"], initial_avail - 1)

        # 2. Duplicate active loan attempt must be rejected
        with self.assertRaises(ValidationError):
            issue_book(book["id"], user["id"], username="admin", loan_days=14)

        # 3. Cannot delete book while active loan exists
        with self.assertRaises(ValidationError):
            delete_book(book["id"], admin_user="admin")

        # 4. Cannot delete member while active loan exists
        with self.assertRaises(ValidationError):
            delete_member(user["id"], admin_user="admin")

        # 5. Return book
        record_id = issue_res["record_id"]
        return_res = return_book(record_id, username="admin")
        self.assertEqual(return_res["record_id"], record_id)
        self.assertGreaterEqual(return_res["fine"], 0.0)

        # Verify available copies restored
        restored_book = get_book(book["id"])
        self.assertEqual(restored_book["available_copies"], initial_avail)

        # 6. Cannot return the same record twice
        with self.assertRaises(ValidationError):
            return_book(record_id, username="admin")

    def test_17_circulation_fine_calculation_for_overdue_book(self):
        # Insert a simulated overdue borrow record directly to test fine calculation
        conn = get_connection()
        cur = conn.cursor()
        past_due = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 5 * 86400)) # 5 days ago
        cur.execute(
            """INSERT INTO borrow_records (book_id, user_id, due_date, status)
               VALUES (1, 2, ?, 'BORROWED')""",
            (past_due,)
        )
        record_id = cur.lastrowid
        cur.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = 1")
        conn.commit()
        conn.close()

        # Return the overdue book
        ret = return_book(record_id, username="admin")
        # Overdue by approx 5 days -> fine should be >= $4.00
        self.assertGreaterEqual(ret["fine"], 4.0)

    # -------------------------------------------------------------------------
    # 6. Q02 DASHBOARD METRICS (Phase Four - Feature 3)
    # -------------------------------------------------------------------------

    def test_18_dashboard_metrics_aggregation(self):
        metrics = get_dashboard_metrics()
        self.assertIn("total_titles", metrics)
        self.assertIn("available_copies", metrics)
        self.assertIn("active_loans", metrics)
        self.assertIn("total_members", metrics)
        self.assertIn("duration_ms", metrics)
        self.assertGreaterEqual(metrics["total_titles"], 5)
        self.assertGreaterEqual(metrics["total_members"], 2)
        # Dashboard aggregation target is < 100 ms
        self.assertLess(metrics["duration_ms"], 100.0)

    # -------------------------------------------------------------------------
    # 7. Q02 OPTIMIZED REPORTS & CSV EXPORT (Phase Four - Feature 2)
    # -------------------------------------------------------------------------

    def test_19_reports_generation_and_export(self):
        # 1. Inventory distribution report
        inv = get_report_inventory_distribution()
        self.assertIsInstance(inv, list)
        self.assertGreater(len(inv), 0)
        self.assertIn("category", inv[0])
        self.assertIn("total_copies", inv[0])

        # 2. Currently issued report
        issued = get_report_currently_issued()
        self.assertIsInstance(issued, list)

        # 3. Overdue books report
        overdue = get_report_overdue_books()
        self.assertIsInstance(overdue, list)

        # 4. Circulation activity report
        circ = get_report_circulation_activity()
        self.assertIsInstance(circ, list)

        # 5. Member summary report
        mem_sum = get_report_member_summary()
        self.assertIsInstance(mem_sum, list)
        self.assertGreater(len(mem_sum), 0)

        # 6. CSV Export verification
        csv_inventory = export_report_to_csv("inventory")
        self.assertIn("category", csv_inventory)
        self.assertIn("total_copies", csv_inventory)

        csv_members = export_report_to_csv("members")
        self.assertIn("username", csv_members)
        self.assertIn("total_borrowings", csv_members)

    # -------------------------------------------------------------------------
    # 8. Q02 BULK CSV INGESTION PIPELINE (Phase Four - Feature 4)
    # -------------------------------------------------------------------------

    def test_20_bulk_csv_import_valid_batch(self):
        csv_rows = [
            "title,author,isbn,category,copies",
            "Discrete Mathematics and Its Applications,Kenneth Rosen,978-0073383095,Mathematics,4",
            "Principles of Management,Philip Kotler,978-0133080148,Management,3",
            "Compilers: Principles Techniques and Tools,Alfred Aho,978-0321486813,Computer Science,2",
            "Quality Control,Dale H. Besterfield,978-0135000953,Quality Engineering,5"
        ]
        csv_text = "\n".join(csv_rows)

        summary = import_books_from_csv(csv_text, admin_user="admin")
        self.assertEqual(summary["inserted"], 4)
        self.assertEqual(summary["skipped_count"], 0)
        self.assertEqual(summary["failed_count"], 0)
        self.assertGreater(summary["throughput_per_sec"], 0.0)

        # Verify books exist in catalog
        books, _ = search_books(query="Discrete Mathematics")
        self.assertEqual(len(books), 1)

    def test_21_bulk_csv_import_duplicate_handling_and_errors(self):
        # Feed CSV with a duplicate of an existing ISBN and a malformed row
        csv_rows = [
            "title,author,isbn,category,copies",
            "Duplicate Book,Duplicate Author,978-0073383095,Mathematics,2", # Already imported above
            ",Missing Title,978-1111111111,Category,2",                     # Malformed row: missing title
            "Invalid Copies,Invalid Author,978-1111111112,Category,not-a-number",
            "Fresh New Book,Fresh Author,978-2222222222,Engineering,3"       # Valid row
        ]
        csv_text = "\n".join(csv_rows)

        summary = import_books_from_csv(csv_text, admin_user="admin")
        self.assertEqual(summary["inserted"], 1)
        self.assertEqual(summary["skipped_count"], 1)
        self.assertEqual(summary["failed_count"], 2)
        self.assertTrue(any("positive integer" in row["reason"] for row in summary["errors"]))

    def test_22_bulk_csv_import_invalid_headers_rejection(self):
        bad_csv = "random_col_1,random_col_2\nval1,val2"
        with self.assertRaises(ValidationError):
            import_books_from_csv(bad_csv, admin_user="admin")

    # -------------------------------------------------------------------------
    # 9. STATISTICAL QUALITY CONTROL (SQC) CHART GENERATION
    # -------------------------------------------------------------------------

    def test_23_sqc_control_chart(self):
        fig, stats = generate_sqc_chart()
        self.assertIsNotNone(fig)
        self.assertGreater(stats["count"], 0)
        self.assertGreaterEqual(stats["ucl"], stats["mean"])
        self.assertLessEqual(stats["lcl"], stats["mean"])

    # -------------------------------------------------------------------------
    # 10. WEB BROWSER FLASK INTERFACE & HEALTH CHECK (Phase Six & Eight)
    # -------------------------------------------------------------------------

    def test_24_web_health_check_endpoint(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["roll_number"], 31)
        self.assertEqual(data["quality_goal"], "Q02 Improve Performance")
        self.assertEqual(data["database"], "connected")
        self.assertGreaterEqual(data["catalog_count"], 5)

    def test_25_web_login_and_navigation_routes(self):
        # 1. Login view
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Library Management System", resp.data)

        # 2. Authenticate session via test client
        with self.client.session_transaction() as sess:
            sess["user"] = {
                "id": 1,
                "username": "admin",
                "full_name": "System Administrator",
                "email": "admin@library.edu",
                "role": "admin"
            }

        # 3. Access Dashboard
        dash_resp = self.client.get("/dashboard")
        self.assertEqual(dash_resp.status_code, 200)
        self.assertIn(b"Operational Control Center", dash_resp.data)

        # 4. Access Catalog
        cat_resp = self.client.get("/catalog")
        self.assertEqual(cat_resp.status_code, 200)
        self.assertIn(b"Book Catalog", cat_resp.data)

        # 5. Access Circulation
        circ_resp = self.client.get("/circulation")
        self.assertEqual(circ_resp.status_code, 200)
        self.assertIn(b"Circulation Desk", circ_resp.data)

        # 6. Access Members
        mem_resp = self.client.get("/members")
        self.assertEqual(mem_resp.status_code, 200)
        self.assertIn(b"Member Management", mem_resp.data)

        # 7. Access Reports
        rep_resp = self.client.get("/reports")
        self.assertEqual(rep_resp.status_code, 200)
        self.assertIn(b"Optimized Management Reports", rep_resp.data)

        # 8. Access CSV Import
        imp_resp = self.client.get("/import-csv")
        self.assertEqual(imp_resp.status_code, 200)
        self.assertIn(b"Bulk Catalog Ingestion", imp_resp.data)

        # 9. Download CSV Template
        tmpl_resp = self.client.get("/api/csv-template")
        self.assertEqual(tmpl_resp.status_code, 200)
        self.assertIn(b"title,author,isbn,category,copies", tmpl_resp.data)

        # 10. Audit log route
        audit_resp = self.client.get("/audit")
        self.assertEqual(audit_resp.status_code, 200)
        self.assertIn(b"Audit Trail", audit_resp.data)

    def test_26_production_initialization_uses_configured_admin_only(self):
        production_db = os.path.join(self.temp_dir.name, "production_library.db")
        production_password = "production-admin-secret-2026"
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "ADMIN_PASSWORD": production_password,
            "DATABASE_PATH": production_db
        }):
            init_db(production_db)
            admin = authenticate_user("admin", production_password)
            self.assertIsNotNone(admin)
            self.assertIsNone(authenticate_user("admin", "admin123"))
            self.assertIsNone(authenticate_user("student1", "student123"))

    def test_27_web_app_import_does_not_initialize_database(self):
        import_db = os.path.join(self.temp_dir.name, "import_only.db")
        env = os.environ.copy()
        env["DATABASE_PATH"] = import_db
        env["APP_ENV"] = "development"
        env.pop("SECRET_KEY", None)
        subprocess.run(
            [sys.executable, "-c", "import web_app"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env,
            check=True,
            capture_output=True
        )
        self.assertFalse(os.path.exists(import_db))

    def test_production_web_requires_a_configured_secret(self):
        env = os.environ.copy()
        env["APP_ENV"] = "production"
        env.pop("SECRET_KEY", None)
        result = subprocess.run(
            [sys.executable, "-c", "import web_app"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env,
            capture_output=True,
            text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SECRET_KEY", result.stderr)

    def test_28_search_index_tracks_book_changes(self):
        book = add_book("Trigram Search Fixture", "Search Author", "978-3333333333", "Testing", 1, "admin")
        found, _ = search_books(query="gram sea")
        self.assertTrue(any(row["id"] == book["id"] for row in found))

        update_book(
            book["id"], "Updated Trigram Fixture", "Search Author",
            book["isbn"], "Testing", 1, "admin"
        )
        found, _ = search_books(query="gram sea")
        self.assertFalse(any(row["id"] == book["id"] for row in found))
        found, _ = search_books(query="updated trig")
        self.assertTrue(any(row["id"] == book["id"] for row in found))

        delete_book(book["id"], "admin")
        found, _ = search_books(query="updated trig")
        self.assertFalse(any(row["id"] == book["id"] for row in found))

    def test_29_loan_duration_is_bounded(self):
        for loan_days in (0, -1, 91):
            with self.subTest(loan_days=loan_days):
                with self.assertRaises(ValidationError):
                    issue_book(1, 2, "admin", loan_days=loan_days)

    def test_30_overdue_report_fine_matches_return_amount(self):
        conn = get_connection()
        cursor = conn.cursor()
        due_date = (datetime.now() - timedelta(days=1, hours=12)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """INSERT INTO borrow_records (book_id, user_id, due_date, status)
               VALUES (1, 2, ?, 'BORROWED')""",
            (due_date,)
        )
        record_id = cursor.lastrowid
        cursor.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = 1")
        conn.commit()
        conn.close()

        report_row = next(
            row for row in get_report_overdue_books()
            if row["record_id"] == record_id
        )
        returned = return_book(record_id, "admin")
        self.assertEqual(report_row["estimated_fine"], returned["fine"])

    def test_31_csv_import_bom_row_limit_and_formula_export(self):
        summary = import_books_from_csv(
            "\ufefftitle,author,isbn,category,copies\nBOM Fixture,CSV Author,978-4444444444,Testing,2",
            admin_user="admin"
        )
        self.assertEqual(summary["inserted"], 1)

        oversized_batch = (
            "title,author,isbn,category,copies\n"
            "One,Author,978-5555555551,Testing,1\n"
            "Two,Author,978-5555555552,Testing,1"
        )
        with self.assertRaises(ValidationError):
            import_books_from_csv(oversized_batch, admin_user="admin", max_rows=1)
        missing, _ = search_books(query="978-5555555552")
        self.assertEqual(missing, [])

        formula_batch = (
            "title,author,isbn,category,copies\n"
            'Formula Fixture,CSV Author,978-6666666666,"=HYPERLINK(""https://example.invalid"")",1'
        )
        import_books_from_csv(formula_batch, admin_user="admin")
        exported = csv.DictReader(io.StringIO(export_report_to_csv("inventory")))
        categories = [row["category"] for row in exported]
        self.assertTrue(any(value.startswith("'=") for value in categories))

    def test_32_student_access_is_limited_to_own_circulation(self):
        student = authenticate_user("student1", "student123")
        self.assertIsNotNone(student)
        other = register_user(
            "other_member",
            "securePass123",
            "Other Member",
            "other_member@unit.edu"
        )
        student_book = add_book("Student Own Fixture", "Author", "978-7777777771", "Testing", 1, "admin")
        other_book = add_book("Other Member Fixture", "Author", "978-7777777772", "Testing", 1, "admin")

        with self.client.session_transaction() as sess:
            sess["user"] = {
                "id": student["id"],
                "username": student["username"],
                "full_name": student["full_name"],
                "email": student["email"],
                "role": student["role"]
            }

        for path in ("/members", "/reports", "/reports/export?type=members"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 302)

        circulation_page = self.client.get("/circulation")
        self.assertEqual(circulation_page.status_code, 200)
        self.assertNotIn(other["email"].encode(), circulation_page.data)

        self.client.post("/circulation/issue", data={
            "book_id": student_book["id"],
            "user_id": other["id"],
            "loan_days": 14
        })
        student_loan = next(
            row for row in get_active_loans(user_id=student["id"])
            if row["book_id"] == student_book["id"]
        )

        other_loan = issue_book(other_book["id"], other["id"], "admin")
        self.client.post(f"/circulation/{other_loan['record_id']}/return")
        self.assertTrue(any(
            row["id"] == other_loan["record_id"]
            for row in get_active_loans(user_id=other["id"])
        ))
        with self.assertRaises(ValidationError):
            return_book(other_loan["record_id"], "student1", borrower_user_id=student["id"])

        return_book(student_loan["id"], "admin")
        return_book(other_loan["record_id"], "admin")


if __name__ == "__main__":
    unittest.main()
