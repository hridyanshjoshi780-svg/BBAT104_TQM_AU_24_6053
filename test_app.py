"""
Automated unit and integration tests for BBAT104 TQM Library Management System.
Tests database operations, Q04 security compliance, book transactions, and SQC calculations.
"""

import unittest
from database import init_db, get_connection
from auth import (
    authenticate_user, register_user, reset_password,
    validate_username, validate_email, validate_password,
    ValidationError
)
from library_service import (
    search_books, add_book, issue_book, return_book,
    get_borrow_records, get_audit_logs
)
from sqc_analysis import generate_sqc_chart


class TestLibraryManagementSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_authentication_admin(self):
        user = authenticate_user("admin", "admin123", expected_role="admin")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "admin")

    def test_02_authentication_student(self):
        user = authenticate_user("student1", "student123", expected_role="student")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "student")

    def test_03_invalid_login(self):
        user = authenticate_user("admin", "wrongpassword")
        self.assertIsNone(user)

    def test_04_role_mismatch_login(self):
        # Student attempting to log in as admin
        user = authenticate_user("student1", "student123", expected_role="admin")
        self.assertIsNone(user)

    def test_05_input_validation(self):
        with self.assertRaises(ValidationError):
            validate_username("a")  # Too short

        with self.assertRaises(ValidationError):
            validate_username("invalid user!")  # Invalid character

        with self.assertRaises(ValidationError):
            validate_email("not-an-email")

        with self.assertRaises(ValidationError):
            validate_password("123")  # Too short

    def test_06_registration_and_reset(self):
        test_user = "test_user_q04"
        test_email = "test_q04@domain.com"
        reg = register_user(test_user, "password123", "Test Student", test_email, role="student")
        self.assertEqual(reg["username"], test_user)

        # Verify password reset
        reset_res = reset_password(test_user, test_email, "new_password123")
        self.assertTrue(reset_res)

        # Authenticate with new password
        user = authenticate_user(test_user, "new_password123")
        self.assertIsNotNone(user)

    def test_07_catalog_search_and_latency(self):
        books, latency = search_books("Quality")
        self.assertGreaterEqual(len(books), 1)
        self.assertGreater(latency, 0.0)

    def test_08_book_issue_and_return_flow(self):
        books, _ = search_books()
        first_book = books[0]
        initial_avail = first_book["available_copies"]

        # Issue book to student1
        user = authenticate_user("student1", "student123")
        issue_res = issue_book(first_book["id"], user["id"], user["username"])
        self.assertIn("due_date", issue_res)

        # Verify available copies decremented
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT available_copies FROM books WHERE id = ?", (first_book["id"],))
        updated_avail = cur.fetchone()["available_copies"]
        self.assertEqual(updated_avail, initial_avail - 1)

        # Return book
        record_id = issue_res["record_id"]
        ret_res = return_book(record_id, user["username"])
        self.assertEqual(ret_res["title"], first_book["title"])

        # Verify available copies restored
        cur.execute("SELECT available_copies FROM books WHERE id = ?", (first_book["id"],))
        restored_avail = cur.fetchone()["available_copies"]
        self.assertEqual(restored_avail, initial_avail)
        conn.close()

    def test_09_audit_trail_logging(self):
        logs = get_audit_logs(limit=10)
        self.assertGreater(len(logs), 0)
        actions = [l["action"] for l in logs]
        self.assertTrue(any("LOGIN" in a or "BOOK" in a or "USER" in a for a in actions))

    def test_10_sqc_chart_generation(self):
        fig, stats = generate_sqc_chart()
        self.assertIsNotNone(fig)
        self.assertGreater(stats["count"], 0)
        self.assertGreaterEqual(stats["ucl"], stats["mean"])
        self.assertLessEqual(stats["lcl"], stats["mean"])


if __name__ == "__main__":
    unittest.main()
