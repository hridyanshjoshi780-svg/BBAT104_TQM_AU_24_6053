"""
Library Service Module for Library Management System (BBAT104 TQM Project - Q02 Improve Performance).
Handles:
- Core CRUD operations for Books and Members
- Fast Search with multi-attribute filtering, selective projection, and latency tracking
- ACID Transactional Issue and Return circulation workflows
- Centralized real-time Dashboard aggregations (sub-100 ms)
- Optimized Analytical Reports with Pandas/SQL aggregation and CSV export (sub-200 ms)
- High-Throughput Bulk CSV Ingestion pipeline (>1,000 records/sec)
"""

import csv
import io
import time
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from database import get_connection, explain_query
from auth import (
    log_audit_trail, sanitize_text, validate_username,
    validate_email, ValidationError
)


# =============================================================================
# 1. FAST SEARCH (Q02 Feature 1)
# =============================================================================

def _book_search_filter(
    query: str,
    category: str,
    availability: str
) -> tuple[str, list[str]]:
    """Build consistent catalog filters, using FTS5 for substring queries of 3+ characters."""
    clauses = ["is_active = 1"]
    params = []

    if category and category != "All":
        clauses.append("category = ?")
        params.append(category)

    if availability == "Available":
        clauses.append("available_copies > 0")
    elif availability == "Issued":
        clauses.append("available_copies < total_copies")

    if query:
        pattern = f"%{query}%"
        if len(query) >= 3:
            clauses.append(
                """id IN (
                    SELECT rowid FROM books_search WHERE title LIKE ?
                    UNION SELECT rowid FROM books_search WHERE author LIKE ?
                    UNION SELECT rowid FROM books_search WHERE isbn LIKE ?
                )"""
            )
            params.extend([pattern, pattern, pattern])
        else:
            clauses.append(
                "(LOWER(title) LIKE ? OR LOWER(author) LIKE ? OR LOWER(isbn) LIKE ?)"
            )
            params.extend([pattern, pattern, pattern])

    return " AND ".join(clauses), params


def search_books(
    query: str = "",
    category: str = "All",
    availability: str = "All",
    limit: int = 200,
    offset: int = 0,
    record_metric: bool = True
) -> tuple[list[dict], float]:
    """
    Search books in the catalog using B-Tree indexed multi-attribute matching.
    Supports partial and case-insensitive matching across Title, Author, and ISBN,
    along with Category and Availability filters.
    Returns (list_of_books, duration_ms).
    """
    start_time = time.perf_counter()
    query = (query or "").strip().lower()
    where_sql, params = _book_search_filter(query, category, availability)
    sql = f"""
        SELECT id, title, author, isbn, category, total_copies, available_copies, added_at, is_active
        FROM books
        WHERE {where_sql}
        ORDER BY title ASC LIMIT ? OFFSET ?
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, [*params, limit, offset])
        books = [dict(row) for row in cursor.fetchall()]
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        if record_metric:
            cursor.execute(
                """INSERT INTO search_metrics (query, duration_ms, result_count)
                   VALUES (?, ?, ?)""",
                (query or "All", duration_ms, len(books))
            )
            conn.commit()
    finally:
        conn.close()

    return books, duration_ms


def search_books_paginated(
    query: str = "",
    category: str = "All",
    availability: str = "All",
    page: int = 1,
    per_page: int = 15
) -> dict:
    """
    Paginated search endpoint for the web interface.
    Computes total count and returns slice for current page.
    """
    page = max(1, int(page))
    per_page = max(1, min(100, int(per_page)))
    offset = (page - 1) * per_page
    clean_query = (query or "").strip().lower()
    where_sql, params = _book_search_filter(clean_query, category, availability)
    start_time = time.perf_counter()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN")
        cursor.execute(f"SELECT COUNT(*) AS cnt FROM books WHERE {where_sql}", params)
        total_count = cursor.fetchone()["cnt"]

        cursor.execute(
            f"""SELECT id, title, author, isbn, category, total_copies, available_copies,
                       added_at, is_active
                FROM books
                WHERE {where_sql}
                ORDER BY title ASC LIMIT ? OFFSET ?""",
            [*params, per_page, offset]
        )
        books = [dict(row) for row in cursor.fetchall()]
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        cursor.execute(
            """INSERT INTO search_metrics (query, duration_ms, result_count)
               VALUES (?, ?, ?)""",
            (clean_query or "All", duration_ms, len(books))
        )
        conn.commit()
    finally:
        conn.close()

    total_pages = max(1, (total_count + per_page - 1) // per_page)
    return {
        "books": books,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "duration_ms": duration_ms
    }


def explain_catalog_search(query: str = "", category: str = "All") -> list[dict]:
    """Inspect query execution plan using EXPLAIN QUERY PLAN."""
    clean_query = (query or "").strip().lower()
    where_sql, params = _book_search_filter(clean_query, category, "All")
    sql = f"SELECT id, title, author, isbn, category FROM books WHERE {where_sql}"
    return explain_query(sql, tuple(params))


def get_all_categories() -> list[str]:
    """Retrieve distinct book categories from the catalog."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM books WHERE is_active = 1 ORDER BY category ASC")
    categories = [row["category"] for row in cursor.fetchall() if row["category"]]
    conn.close()
    return categories


# =============================================================================
# 2. BOOK CRUD OPERATIONS (Phase Three)
# =============================================================================

def add_book(title: str, author: str, isbn: str, category: str, copies: int, admin_user: str) -> dict:
    """Add a new book to the library catalog with input validation and audit logging."""
    title = sanitize_text(title)
    author = sanitize_text(author)
    isbn = sanitize_text(isbn).upper()
    category = sanitize_text(category)

    if not title or not author or not isbn or not category:
        raise ValidationError("All book fields (Title, Author, ISBN, Category) are required.")

    try:
        copies = int(copies)
    except (ValueError, TypeError):
        raise ValidationError("Total copies must be a valid positive integer.")

    if copies <= 0:
        raise ValidationError("Total copies must be at least 1.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM books WHERE isbn = ?", (isbn,))
    if cursor.fetchone():
        conn.close()
        raise ValidationError(f"A book with ISBN '{isbn}' already exists in the catalog.")

    cursor.execute(
        """INSERT INTO books (title, author, isbn, category, total_copies, available_copies, is_active)
           VALUES (?, ?, ?, ?, ?, ?, 1)""",
        (title, author, isbn, category, copies, copies)
    )
    book_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_audit_trail(admin_user, "BOOK_ADDED", f"Added '{title}' (ISBN: {isbn}, Copies: {copies})")
    return {"id": book_id, "title": title, "author": author, "isbn": isbn, "copies": copies}


def get_book(book_id: int) -> dict | None:
    """Retrieve a single book by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, title, author, isbn, category, total_copies, available_copies, added_at, is_active
           FROM books WHERE id = ?""",
        (book_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_book(
    book_id: int,
    title: str,
    author: str,
    isbn: str,
    category: str,
    copies: int,
    admin_user: str
) -> dict:
    """
    Update book bibliographic details and copy count.
    Ensures total copies does not fall below currently issued copies.
    """
    title = sanitize_text(title)
    author = sanitize_text(author)
    isbn = sanitize_text(isbn).upper()
    category = sanitize_text(category)

    if not title or not author or not isbn or not category:
        raise ValidationError("All book fields (Title, Author, ISBN, Category) are required.")

    try:
        copies = int(copies)
    except (ValueError, TypeError):
        raise ValidationError("Total copies must be a valid positive integer.")

    if copies <= 0:
        raise ValidationError("Total copies must be at least 1.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    if not book:
        conn.close()
        raise ValidationError("Book not found.")

    # Check ISBN uniqueness if changed
    cursor.execute("SELECT id FROM books WHERE isbn = ? AND id != ?", (isbn, book_id))
    if cursor.fetchone():
        conn.close()
        raise ValidationError(f"Another book with ISBN '{isbn}' already exists.")

    # Compute currently issued copies
    issued_copies = book["total_copies"] - book["available_copies"]
    if copies < issued_copies:
        conn.close()
        raise ValidationError(
            f"Cannot reduce total copies to {copies}: {issued_copies} copies are currently borrowed."
        )

    new_available = copies - issued_copies

    cursor.execute(
        """UPDATE books
           SET title = ?, author = ?, isbn = ?, category = ?, total_copies = ?, available_copies = ?
           WHERE id = ?""",
        (title, author, isbn, category, copies, new_available, book_id)
    )
    conn.commit()
    conn.close()

    log_audit_trail(
        admin_user,
        "BOOK_UPDATED",
        f"Updated '{title}' (ID: {book_id}, ISBN: {isbn}, Copies: {copies}, Avail: {new_available})"
    )
    return {"id": book_id, "title": title, "author": author, "isbn": isbn, "copies": copies}


def delete_book(book_id: int, admin_user: str) -> dict:
    """
    Safely delete or archive a book.
    Rejects deletion if active unreturned loans exist.
    If historical loans exist, archives book (soft-delete) to preserve referential integrity.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    if not book:
        conn.close()
        raise ValidationError("Book not found.")

    # Check if there are active loans
    cursor.execute(
        "SELECT COUNT(*) as count FROM borrow_records WHERE book_id = ? AND status = 'BORROWED'",
        (book_id,)
    )
    active_loans = cursor.fetchone()["count"]
    if active_loans > 0:
        conn.close()
        raise ValidationError(
            f"Cannot delete '{book['title']}': {active_loans} copy is currently checked out. "
            "All copies must be returned before deleting or archiving."
        )

    # Check if historical borrow records exist
    cursor.execute(
        "SELECT COUNT(*) as count FROM borrow_records WHERE book_id = ?",
        (book_id,)
    )
    historical_count = cursor.fetchone()["count"]

    if historical_count > 0:
        # Soft delete / archive to preserve history
        cursor.execute("UPDATE books SET is_active = 0 WHERE id = ?", (book_id,))
        action_type = "BOOK_ARCHIVED"
        status_msg = "archived (preserved in audit/circulation history)"
    else:
        # Safe hard delete since no transactions ever referenced it
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        action_type = "BOOK_DELETED"
        status_msg = "permanently deleted"

    conn.commit()
    conn.close()

    log_audit_trail(admin_user, action_type, f"Book '{book['title']}' (ID: {book_id}) was {status_msg}.")
    return {"id": book_id, "title": book["title"], "status": status_msg}


# =============================================================================
# 3. MEMBER CRUD OPERATIONS (Phase Three)
# =============================================================================

def get_all_members(query: str = "", role: str = "All", limit: int = 100, offset: int = 0) -> tuple[list[dict], int]:
    """Retrieve registered members with active loan counts and total counts."""
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT u.id, u.username, u.full_name, u.email, u.role, u.created_at, u.is_active,
               (SELECT COUNT(*) FROM borrow_records b WHERE b.user_id = u.id AND b.status = 'BORROWED') as active_loans
        FROM users u
        WHERE u.is_active = 1
    """
    params = []

    if role and role != "All":
        sql += " AND u.role = ?"
        params.append(role)

    query = (query or "").strip().lower()
    if query:
        sql += " AND (LOWER(u.username) LIKE ? OR LOWER(u.full_name) LIKE ? OR LOWER(u.email) LIKE ?)"
        pattern = f"%{query}%"
        params.extend([pattern, pattern, pattern])

    sql += " ORDER BY u.full_name ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(sql, params)
    members = [dict(row) for row in cursor.fetchall()]

    # Total count
    count_sql = "SELECT COUNT(*) as cnt FROM users WHERE is_active = 1"
    count_params = []
    if role and role != "All":
        count_sql += " AND role = ?"
        count_params.append(role)
    if query:
        count_sql += " AND (LOWER(username) LIKE ? OR LOWER(full_name) LIKE ? OR LOWER(email) LIKE ?)"
        pattern = f"%{query}%"
        count_params.extend([pattern, pattern, pattern])

    cursor.execute(count_sql, count_params)
    total_count = cursor.fetchone()["cnt"]

    conn.close()
    return members, total_count


def get_member(user_id: int) -> dict | None:
    """Retrieve member profile and loan statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT u.id, u.username, u.full_name, u.email, u.role, u.created_at, u.is_active,
                  (SELECT COUNT(*) FROM borrow_records b WHERE b.user_id = u.id AND b.status = 'BORROWED') as active_loans,
                  (SELECT COUNT(*) FROM borrow_records b WHERE b.user_id = u.id) as total_loans
           FROM users u
           WHERE u.id = ?""",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_member(user_id: int, full_name: str, email: str, role: str, admin_user: str) -> dict:
    """Update member profile details with validation and unique email check."""
    full_name = sanitize_text(full_name)
    email = validate_email(email)

    if not full_name:
        raise ValidationError("Full name cannot be empty.")

    if role not in ("student", "admin"):
        role = "student"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    member = cursor.fetchone()
    if not member:
        conn.close()
        raise ValidationError("Member not found.")

    # Unique email check
    cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
    if cursor.fetchone():
        conn.close()
        raise ValidationError(f"Email '{email}' is already registered to another user.")

    cursor.execute(
        "UPDATE users SET full_name = ?, email = ?, role = ? WHERE id = ?",
        (full_name, email, role, user_id)
    )
    conn.commit()
    conn.close()

    log_audit_trail(admin_user, "MEMBER_UPDATED", f"Updated member '{member['username']}' (ID: {user_id})")
    return {"id": user_id, "username": member["username"], "full_name": full_name, "email": email, "role": role}


def delete_member(user_id: int, admin_user: str) -> dict:
    """
    Safely delete or archive a library member.
    Rejects deletion if active unreturned loans exist.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    member = cursor.fetchone()
    if not member:
        conn.close()
        raise ValidationError("Member not found.")

    cursor.execute(
        "SELECT COUNT(*) as count FROM borrow_records WHERE user_id = ? AND status = 'BORROWED'",
        (user_id,)
    )
    active_loans = cursor.fetchone()["count"]
    if active_loans > 0:
        conn.close()
        raise ValidationError(
            f"Cannot delete member '{member['username']}': User has {active_loans} unreturned book(s). "
            "All books must be returned first."
        )

    # Check historical transactions
    cursor.execute(
        "SELECT COUNT(*) as count FROM borrow_records WHERE user_id = ?",
        (user_id,)
    )
    has_history = cursor.fetchone()["count"] > 0

    if has_history:
        cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        status_msg = "archived (preserved in circulation history)"
    else:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        status_msg = "permanently deleted"

    conn.commit()
    conn.close()

    log_audit_trail(admin_user, "MEMBER_DELETED", f"Member '{member['username']}' was {status_msg}.")
    return {"id": user_id, "username": member["username"], "status": status_msg}


# =============================================================================
# 4. OPTIMIZED BOOK ISSUE AND RETURN (Phase Five & Core Q02 Objective)
# =============================================================================

def issue_book(book_id: int, user_id: int, username: str, loan_days: int = 14) -> dict:
    """
    Issue a book to a user within an atomic transaction.
    Verifies:
      1. Book exists, is active, and available_copies > 0.
      2. Member exists, is active.
      3. No duplicate active borrowing of the same book.
      4. Atomically decrements available_copies and inserts borrow_record.
    Returns transaction summary and measured latency.
    """
    start_time = time.perf_counter()

    try:
        book_id = int(book_id)
        user_id = int(user_id)
        loan_days = 14 if loan_days is None or loan_days == "" else int(loan_days)
    except (ValueError, TypeError):
        raise ValidationError("Invalid book ID, user ID, or loan duration.")

    if not 1 <= loan_days <= 90:
        raise ValidationError("Loan duration must be between 1 and 90 days.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        # 1. Verify book
        cursor.execute(
            "SELECT id, title, total_copies, available_copies, is_active FROM books WHERE id = ?",
            (book_id,)
        )
        book = cursor.fetchone()
        if not book or not book["is_active"]:
            raise ValidationError("Book not found or is currently archived.")

        if book["available_copies"] <= 0:
            raise ValidationError(f"No copies currently available for '{book['title']}'.")

        # 2. Verify user
        cursor.execute(
            "SELECT id, username, full_name, is_active FROM users WHERE id = ?",
            (user_id,)
        )
        user = cursor.fetchone()
        if not user or not user["is_active"]:
            raise ValidationError("Member not found or account is deactivated.")

        # 3. Check duplicate active checkout
        cursor.execute(
            """SELECT id FROM borrow_records
               WHERE book_id = ? AND user_id = ? AND status = 'BORROWED'""",
            (book_id, user_id)
        )
        if cursor.fetchone():
            raise ValidationError(f"Member '{user['username']}' already has an active borrowed copy of '{book['title']}'.")

        # 4. Compute due date
        due_date = datetime.now() + timedelta(days=loan_days)

        # 5. Insert record
        cursor.execute(
            """INSERT INTO borrow_records (book_id, user_id, due_date, status)
               VALUES (?, ?, ?, 'BORROWED')""",
            (book_id, user_id, due_date.strftime("%Y-%m-%d %H:%M:%S"))
        )
        record_id = cursor.lastrowid

        # 6. Decrement copy atomically with availability safeguard
        cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE id = ? AND available_copies > 0",
            (book_id,)
        )
        if cursor.rowcount == 0:
            raise ValidationError("Concurrency conflict: book copy was checked out simultaneously.")

        conn.commit()

    except Exception:
        conn.rollback()
        conn.close()
        raise

    conn.close()

    end_time = time.perf_counter()
    duration_ms = round((end_time - start_time) * 1000.0, 2)

    log_audit_trail(
        username,
        "BOOK_ISSUED",
        f"Issued '{book['title']}' to {user['username']} (Record: {record_id}, Due: {due_date.strftime('%Y-%m-%d')})"
    )

    return {
        "record_id": record_id,
        "book_id": book_id,
        "user_id": user_id,
        "title": book["title"],
        "username": user["username"],
        "due_date": due_date.strftime("%Y-%m-%d"),
        "duration_ms": duration_ms
    }


def return_book(record_id: int, username: str, borrower_user_id: int = None) -> dict:
    """
    Process book return in an atomic transaction.
    Verifies:
      1. Borrow record exists and is in BORROWED status.
      2. Computes overdue fines if return is past due date ($1.00/day).
      3. Atomically marks record RETURNED and increments available_copies.
    Returns transaction summary and measured latency.
    """
    start_time = time.perf_counter()

    try:
        record_id = int(record_id)
        if borrower_user_id is not None:
            borrower_user_id = int(borrower_user_id)
    except (ValueError, TypeError):
        raise ValidationError("Invalid borrow record ID.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute(
            """SELECT r.id, r.book_id, r.user_id, r.due_date, r.status, b.title, u.username as borrower
               FROM borrow_records r
               JOIN books b ON r.book_id = b.id
               JOIN users u ON r.user_id = u.id
               WHERE r.id = ? AND r.status = 'BORROWED'
                 AND (? IS NULL OR r.user_id = ?)""",
            (record_id, borrower_user_id, borrower_user_id)
        )
        record = cursor.fetchone()
        if not record:
            raise ValidationError("Active borrow record not found or book has already been returned.")

        now = datetime.now()
        due_date_str = record["due_date"]
        # Handle string parsing
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")

        # Overdue fine calculation: $1.00 per day
        fine = 0.0
        if now > due_date:
            overdue_days = (now - due_date).days
            if overdue_days > 0:
                fine = round(overdue_days * 1.0, 2)

        # Update record
        cursor.execute(
            """UPDATE borrow_records
               SET status = 'RETURNED', return_date = ?, fine_amount = ?
               WHERE id = ?""",
            (now.strftime("%Y-%m-%d %H:%M:%S"), fine, record_id)
        )

        # Restore available copies
        cursor.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE id = ?",
            (record["book_id"],)
        )

        conn.commit()

    except Exception:
        conn.rollback()
        conn.close()
        raise

    conn.close()

    end_time = time.perf_counter()
    duration_ms = round((end_time - start_time) * 1000.0, 2)

    log_audit_trail(
        username,
        "BOOK_RETURNED",
        f"Returned '{record['title']}' for borrower '{record['borrower']}'. Fine: ${fine:.2f}"
    )

    return {
        "record_id": record_id,
        "title": record["title"],
        "borrower": record["borrower"],
        "fine": fine,
        "duration_ms": duration_ms
    }


def get_borrow_records(user_id: int = None, status: str = "All", limit: int = 200) -> list[dict]:
    """Retrieve borrow records with optional user and status filters."""
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT r.id, r.book_id, r.user_id, r.borrow_date, r.due_date, r.return_date,
               r.status, r.fine_amount, b.title, b.author, b.isbn, b.category,
               u.username, u.full_name
        FROM borrow_records r
        JOIN books b ON r.book_id = b.id
        JOIN users u ON r.user_id = u.id
        WHERE 1=1
    """
    params = []

    if user_id:
        sql += " AND r.user_id = ?"
        params.append(user_id)

    if status and status != "All":
        sql += " AND r.status = ?"
        params.append(status)

    sql += " ORDER BY r.borrow_date DESC LIMIT ?"
    params.append(limit)

    cursor.execute(sql, params)
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return records


def get_active_loans(user_id: int = None) -> list[dict]:
    """Retrieve only active unreturned loans."""
    return get_borrow_records(user_id=user_id, status="BORROWED", limit=500)


def get_audit_logs(limit: int = 100) -> list[dict]:
    """Retrieve recent audit logs for the security and quality viewer."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, timestamp, username, action, details
           FROM audit_logs
           ORDER BY timestamp DESC LIMIT ?""",
        (limit,)
    )
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return logs


# =============================================================================
# 5. DASHBOARD METRICS (Q02 Feature 3)
# =============================================================================

def get_dashboard_metrics() -> dict:
    """
    Consolidates core operational KPIs and chart data into a single fast aggregation (target < 100 ms).
    Derives all values dynamically from current database tables.
    """
    start_time = time.perf_counter()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("BEGIN")

    # 1. Books summary
    cursor.execute("""
        SELECT
            COUNT(*) as total_titles,
            COALESCE(SUM(total_copies), 0) as total_copies,
            COALESCE(SUM(available_copies), 0) as available_copies
        FROM books
        WHERE is_active = 1
    """)
    book_stats = cursor.fetchone()
    total_titles = book_stats["total_titles"]
    total_copies = book_stats["total_copies"]
    available_copies = book_stats["available_copies"]
    issued_copies = max(0, total_copies - available_copies)

    # 2. Members count
    cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE is_active = 1")
    total_members = cursor.fetchone()["cnt"]

    # 3. Active loans & Overdue loans
    cursor.execute("""
        SELECT
            COUNT(*) as active_loans,
            COALESCE(SUM(CASE WHEN due_date < CURRENT_TIMESTAMP THEN 1 ELSE 0 END), 0) as overdue_loans,
            COALESCE(SUM(fine_amount), 0.0) as total_fines
        FROM borrow_records
        WHERE status = 'BORROWED'
    """)
    loan_stats = cursor.fetchone()
    active_loans = loan_stats["active_loans"]
    overdue_loans = loan_stats["overdue_loans"]

    # Total fines collected/accrued across all records
    cursor.execute("SELECT COALESCE(SUM(fine_amount), 0.0) as all_fines FROM borrow_records")
    total_fines_accrued = round(cursor.fetchone()["all_fines"], 2)

    # 4. Average Search Latency from search_metrics table
    cursor.execute("""
        SELECT COALESCE(AVG(duration_ms), 0.0) as avg_latency
        FROM (SELECT duration_ms FROM search_metrics ORDER BY id DESC LIMIT 50)
    """)
    avg_search_latency = round(cursor.fetchone()["avg_latency"], 2)

    # 5. Category distribution for chart
    cursor.execute("""
        SELECT category, COUNT(*) as titles, COALESCE(SUM(total_copies), 0) as copies
        FROM books
        WHERE is_active = 1
        GROUP BY category
        ORDER BY titles DESC
    """)
    category_distribution = [dict(r) for r in cursor.fetchall()]

    # 6. Recent activity (combining recent borrows, returns, additions)
    cursor.execute("""
        SELECT timestamp, username, action, details
        FROM audit_logs
        ORDER BY id DESC
        LIMIT 8
    """)
    recent_activity = [dict(r) for r in cursor.fetchall()]

    conn.close()

    duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

    return {
        "total_titles": total_titles,
        "total_copies": total_copies,
        "available_copies": available_copies,
        "issued_copies": issued_copies,
        "total_members": total_members,
        "active_loans": active_loans,
        "overdue_loans": overdue_loans,
        "total_fines_accrued": total_fines_accrued,
        "avg_search_latency_ms": avg_search_latency,
        "category_distribution": category_distribution,
        "recent_activity": recent_activity,
        "duration_ms": duration_ms
    }


# =============================================================================
# 6. OPTIMIZED REPORTS & CSV EXPORT (Q02 Feature 2)
# =============================================================================

def get_report_inventory_distribution() -> list[dict]:
    """Generates inventory distribution summary per category using SQL aggregation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            category,
            COUNT(*) as unique_titles,
            SUM(total_copies) as total_copies,
            SUM(available_copies) as available_copies,
            (SUM(total_copies) - SUM(available_copies)) as borrowed_copies,
            ROUND(100.0 * (SUM(total_copies) - SUM(available_copies)) / MAX(1, SUM(total_copies)), 1) as utilization_pct
        FROM books
        WHERE is_active = 1
        GROUP BY category
        ORDER BY total_copies DESC
    """)
    report = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return report


def get_report_currently_issued(category: str = "All") -> list[dict]:
    """Generates report of currently issued books."""
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT
            r.id as record_id,
            b.title,
            b.author,
            b.isbn,
            b.category,
            u.username as borrower_username,
            u.full_name as borrower_name,
            r.borrow_date,
            r.due_date,
            CASE
                WHEN r.due_date < CURRENT_TIMESTAMP THEN 'OVERDUE'
                ELSE 'ON_LOAN'
            END as status
        FROM borrow_records r
        JOIN books b ON r.book_id = b.id
        JOIN users u ON r.user_id = u.id
        WHERE r.status = 'BORROWED'
    """
    params = []
    if category and category != "All":
        sql += " AND b.category = ?"
        params.append(category)

    sql += " ORDER BY r.due_date ASC"
    cursor.execute(sql, params)
    report = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return report


def get_report_overdue_books() -> list[dict]:
    """Generates overdue books report with days overdue and estimated fines."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            r.id as record_id,
            b.title,
            b.author,
            b.isbn,
            b.category,
            u.username as borrower_username,
            u.full_name as borrower_name,
            u.email,
            r.borrow_date,
            r.due_date,
            ROUND((JULIANDAY(CURRENT_TIMESTAMP) - JULIANDAY(r.due_date)), 1) as days_overdue,
            MAX(0, CAST(JULIANDAY(CURRENT_TIMESTAMP) - JULIANDAY(r.due_date) AS INTEGER)) as estimated_fine
        FROM borrow_records r
        JOIN books b ON r.book_id = b.id
        JOIN users u ON r.user_id = u.id
        WHERE r.status = 'BORROWED' AND r.due_date < CURRENT_TIMESTAMP
        ORDER BY days_overdue DESC
    """)
    report = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return report


def get_report_circulation_activity(start_date: str = None, end_date: str = None) -> list[dict]:
    """Generates historical circulation activity report within an optional date range."""
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT
            r.id as record_id,
            b.title,
            b.isbn,
            u.username,
            u.full_name,
            r.borrow_date,
            r.due_date,
            r.return_date,
            r.status,
            r.fine_amount
        FROM borrow_records r
        JOIN books b ON r.book_id = b.id
        JOIN users u ON r.user_id = u.id
        WHERE 1=1
    """
    params = []
    if start_date:
        sql += " AND r.borrow_date >= ?"
        params.append(f"{start_date} 00:00:00")
    if end_date:
        sql += " AND r.borrow_date <= ?"
        params.append(f"{end_date} 23:59:59")

    sql += " ORDER BY r.borrow_date DESC LIMIT 500"
    cursor.execute(sql, params)
    report = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return report


def get_report_member_summary() -> list[dict]:
    """Generates member borrowing summary report using SQL aggregation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            u.id,
            u.username,
            u.full_name,
            u.email,
            u.role,
            COUNT(r.id) as total_borrowings,
            COALESCE(SUM(CASE WHEN r.status = 'BORROWED' THEN 1 ELSE 0 END), 0) as current_loans,
            COALESCE(SUM(r.fine_amount), 0.0) as total_fines_assessed
        FROM users u
        LEFT JOIN borrow_records r ON u.id = r.user_id
        WHERE u.is_active = 1
        GROUP BY u.id
        ORDER BY current_loans DESC, total_borrowings DESC
    """)
    report = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return report


def export_report_to_csv(report_type: str, **kwargs) -> str:
    """Export any report into standard RFC-4180 CSV format."""
    if report_type == "inventory":
        data = get_report_inventory_distribution()
    elif report_type == "issued":
        data = get_report_currently_issued(category=kwargs.get("category", "All"))
    elif report_type == "overdue":
        data = get_report_overdue_books()
    elif report_type == "circulation":
        data = get_report_circulation_activity(
            start_date=kwargs.get("start_date"),
            end_date=kwargs.get("end_date")
        )
    elif report_type == "members":
        data = get_report_member_summary()
    else:
        raise ValidationError(f"Unknown report type: '{report_type}'")

    if not data:
        return "No records found matching criteria.\n"

    df = pd.DataFrame(data)
    df = df.map(_escape_spreadsheet_formula)
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()


def _escape_spreadsheet_formula(value):
    if isinstance(value, str) and value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


# =============================================================================
# 7. BULK CSV IMPORT (Q02 Feature 4)
# =============================================================================

def get_sample_csv_template() -> str:
    """Return standard CSV format instructions and template sample."""
    sample_rows = [
        ["title", "author", "isbn", "category", "copies"],
        ["Design Patterns: Elements of Reusable Object-Oriented Software", "Erich Gamma", "978-0201633610", "Computer Science", "4"],
        ["Modern Management", "Samuel C. Certo", "978-0134729138", "Management", "3"],
        ["Quality Management for Organizational Excellence", "David L. Goetsch", "978-0133791853", "Quality Engineering", "5"],
        ["Artificial Intelligence: A Modern Approach", "Stuart Russell", "978-0136042594", "Computer Science", "2"],
    ]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(sample_rows)
    return output.getvalue()


def import_books_from_csv(csv_content: str, admin_user: str, max_rows: int = 10000) -> dict:
    """
    High-throughput bulk catalog import using single-transaction batch execution (target > 1,000 records/sec).
    Performs:
      1. Header validation (case-insensitive checking for title, author, isbn, category, copies).
      2. Record validation and type conversion.
      3. Skips duplicate ISBNs within batch and existing catalog.
      4. Single atomic commit using parameterized executemany.
    Returns comprehensive import summary.
    """
    start_time = time.perf_counter()

    if not csv_content or not csv_content.strip():
        raise ValidationError("Uploaded CSV file is empty.")

    # Prevent potential huge memory exhaustion
    if len(csv_content) > 10 * 1024 * 1024:  # 10 MB limit
        raise ValidationError("CSV file size exceeds maximum allowable limit of 10 MB.")

    try:
        max_rows = int(max_rows)
    except (ValueError, TypeError):
        raise ValidationError("Maximum CSV row count must be a positive integer.")
    if max_rows < 1:
        raise ValidationError("Maximum CSV row count must be a positive integer.")

    f = io.StringIO(csv_content.lstrip("\ufeff").strip())
    reader = csv.reader(f)

    try:
        raw_headers = next(reader)
    except StopIteration:
        raise ValidationError("CSV file has no content.")

    headers = [h.strip().lower() for h in raw_headers]

    # Map column headers
    col_map = {}
    for idx, h in enumerate(headers):
        if h in ("title", "book_title", "name"):
            col_map["title"] = idx
        elif h in ("author", "authors", "writer"):
            col_map["author"] = idx
        elif h in ("isbn", "isbn13", "isbn10", "code"):
            col_map["isbn"] = idx
        elif h in ("category", "genre", "subject"):
            col_map["category"] = idx
        elif h in ("copies", "total_copies", "count", "quantity"):
            col_map["copies"] = idx

    required_fields = ["title", "author", "isbn", "category", "copies"]
    missing = [f for f in required_fields if f not in col_map]
    if missing:
        raise ValidationError(
            f"CSV file is missing required headers: {', '.join(missing)}. "
            f"Expected: title, author, isbn, category, copies."
        )

    copies_col = col_map["copies"]

    # Pre-fetch existing ISBNs from database for O(1) duplicate checks
    conn = get_connection()
    batch_to_insert = []
    seen_in_batch = set()
    skipped_records = []
    failed_records = []
    inserted_count = 0
    processed_rows = 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT isbn FROM books")
        existing_isbns = set(row["isbn"].strip().upper() for row in cursor.fetchall())

        for row_number, row in enumerate(reader, start=2):
            if row_number > max_rows + 1:
                raise ValidationError(
                    f"CSV exceeds the maximum of {max_rows} data rows; no rows were imported."
                )
            processed_rows += 1

            if not row or not any(field.strip() for field in row):
                continue

            try:
                title = row[col_map["title"]].strip()
                author = row[col_map["author"]].strip()
                isbn = row[col_map["isbn"]].strip().upper()
                category = row[col_map["category"]].strip()

                if not title or not author or not isbn or not category:
                    failed_records.append({
                        "row": row_number,
                        "isbn": isbn or "N/A",
                        "reason": "Missing required field (Title, Author, ISBN, or Category)."
                    })
                    continue

                copies = int(row[copies_col].strip())
                if copies <= 0:
                    raise ValueError
            except IndexError:
                failed_records.append({
                    "row": row_number,
                    "isbn": "N/A",
                    "reason": "Malformed row: insufficient columns."
                })
                continue
            except ValueError:
                failed_records.append({
                    "row": row_number,
                    "isbn": isbn,
                    "reason": "Copies must be a positive integer."
                })
                continue

            if isbn in existing_isbns or isbn in seen_in_batch:
                skipped_records.append({
                    "row": row_number,
                    "isbn": isbn,
                    "title": title,
                    "reason": "Duplicate ISBN already exists in catalog or batch."
                })
                continue

            seen_in_batch.add(isbn)
            batch_to_insert.append((title, author, isbn, category, copies, copies, 1))

        if batch_to_insert:
            try:
                cursor.execute("BEGIN IMMEDIATE")
                cursor.executemany(
                    """INSERT INTO books (title, author, isbn, category, total_copies, available_copies, is_active)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    batch_to_insert
                )
                conn.commit()
                inserted_count = len(batch_to_insert)
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise ValidationError(
                    "CSV batch conflicts with existing catalog data; no rows were imported."
                ) from exc
            except sqlite3.Error:
                conn.rollback()
                raise
    except csv.Error as exc:
        raise ValidationError("CSV file is malformed.") from exc
    finally:
        conn.close()

    end_time = time.perf_counter()
    duration_s = max(0.0001, end_time - start_time)
    duration_ms = round(duration_s * 1000.0, 2)
    throughput = round(inserted_count / duration_s, 1)

    log_audit_trail(
        admin_user,
        "CSV_IMPORT",
        f"Bulk imported {inserted_count} books, skipped {len(skipped_records)}, failed {len(failed_records)} in {duration_ms} ms."
    )

    return {
        "total_processed": processed_rows,
        "inserted": inserted_count,
        "skipped_count": len(skipped_records),
        "failed_count": len(failed_records),
        "duration_ms": duration_ms,
        "throughput_per_sec": throughput,
        "skipped": skipped_records[:50],  # bounded sample
        "errors": failed_records[:50]
    }
