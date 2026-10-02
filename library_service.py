"""
Library Service Module for Library Management System.
Handles book catalog management, search latency metrics recording, issue/return transactions, and audit retrieval.
"""

import time
from datetime import datetime, timedelta
from database import get_connection
from auth import log_audit_trail, sanitize_text, ValidationError


def search_books(query: str = "", category: str = "All") -> tuple[list[dict], float]:
    """
    Search books in the catalog and record latency for TQM SQC analysis.
    Returns (list_of_books, duration_ms).
    """
    start_time = time.perf_counter()
    query = (query or "").strip().lower()

    conn = get_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM books WHERE 1=1"
    params = []

    if category and category != "All":
        sql += " AND category = ?"
        params.append(category)

    if query:
        sql += " AND (LOWER(title) LIKE ? OR LOWER(author) LIKE ? OR LOWER(isbn) LIKE ?)"
        pattern = f"%{query}%"
        params.extend([pattern, pattern, pattern])

    sql += " ORDER BY title ASC"
    cursor.execute(sql, params)
    books = [dict(row) for row in cursor.fetchall()]

    end_time = time.perf_counter()
    duration_ms = round((end_time - start_time) * 1000.0, 2)

    # Record search metric into database for SQC charting
    try:
        cursor.execute(
            """INSERT INTO search_metrics (query, duration_ms, result_count)
               VALUES (?, ?, ?)""",
            (query or "All", duration_ms, len(books))
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

    return books, duration_ms


def get_all_categories() -> list[str]:
    """Get list of distinct book categories."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM books ORDER BY category ASC")
    categories = [row["category"] for row in cursor.fetchall() if row["category"]]
    conn.close()
    return categories


def add_book(title: str, author: str, isbn: str, category: str, copies: int, admin_user: str) -> dict:
    """Add a new book to the library catalog (Admin privilege)."""
    title = sanitize_text(title)
    author = sanitize_text(author)
    isbn = sanitize_text(isbn)
    category = sanitize_text(category)

    if not title or not author or not isbn or not category:
        raise ValidationError("All book fields (Title, Author, ISBN, Category) are required.")

    if copies <= 0:
        raise ValidationError("Total copies must be at least 1.")

    conn = get_connection()
    cursor = conn.cursor()

    # Check for duplicate ISBN
    cursor.execute("SELECT id FROM books WHERE isbn = ?", (isbn,))
    if cursor.fetchone():
        conn.close()
        raise ValidationError(f"A book with ISBN '{isbn}' already exists in the catalog.")

    cursor.execute(
        """INSERT INTO books (title, author, isbn, category, total_copies, available_copies)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (title, author, isbn, category, copies, copies)
    )
    book_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_audit_trail(admin_user, "BOOK_ADDED", f"Added '{title}' (ISBN: {isbn}, Copies: {copies})")
    return {"id": book_id, "title": title, "author": author, "isbn": isbn}


def issue_book(book_id: int, user_id: int, username: str, loan_days: int = 14) -> dict:
    """Issue a book to a user, checking availability and updating inventory."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    if not book:
        conn.close()
        raise ValidationError("Book not found.")

    if book["available_copies"] <= 0:
        conn.close()
        raise ValidationError(f"No copies available for '{book['title']}'.")

    # Check if student already borrowed this specific book without returning
    cursor.execute(
        "SELECT id FROM borrow_records WHERE book_id = ? AND user_id = ? AND status = 'BORROWED'",
        (book_id, user_id)
    )
    if cursor.fetchone():
        conn.close()
        raise ValidationError(f"User already has an active copy of '{book['title']}' checked out.")

    due_date = datetime.now() + timedelta(days=loan_days)
    cursor.execute(
        """INSERT INTO borrow_records (book_id, user_id, due_date, status)
           VALUES (?, ?, ?, 'BORROWED')""",
        (book_id, user_id, due_date.strftime("%Y-%m-%d %H:%M:%S"))
    )
    record_id = cursor.lastrowid

    cursor.execute(
        "UPDATE books SET available_copies = available_copies - 1 WHERE id = ?",
        (book_id,)
    )

    conn.commit()
    conn.close()

    log_audit_trail(username, "BOOK_ISSUED", f"Issued '{book['title']}' to {username}. Due: {due_date.strftime('%Y-%m-%d')}")
    return {"record_id": record_id, "title": book["title"], "due_date": due_date.strftime("%Y-%m-%d")}


def return_book(record_id: int, username: str) -> dict:
    """Process book return, calculate overdue fines if applicable, and update inventory."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """SELECT r.*, b.title, b.id as book_id 
           FROM borrow_records r
           JOIN books b ON r.book_id = b.id
           WHERE r.id = ? AND r.status = 'BORROWED'""",
        (record_id,)
    )
    record = cursor.fetchone()
    if not record:
        conn.close()
        raise ValidationError("Active borrow record not found or book already returned.")

    now = datetime.now()
    due_date = datetime.strptime(record["due_date"], "%Y-%m-%d %H:%M:%S")

    # Fine calculation: $1.00 per overdue day
    fine = 0.0
    if now > due_date:
        overdue_days = (now - due_date).days
        if overdue_days > 0:
            fine = overdue_days * 1.0

    cursor.execute(
        """UPDATE borrow_records 
           SET status = 'RETURNED', return_date = ?, fine_amount = ? 
           WHERE id = ?""",
        (now.strftime("%Y-%m-%d %H:%M:%S"), fine, record_id)
    )

    cursor.execute(
        "UPDATE books SET available_copies = available_copies + 1 WHERE id = ?",
        (record["book_id"],)
    )

    conn.commit()
    conn.close()

    log_audit_trail(
        username,
        "BOOK_RETURNED",
        f"Returned '{record['title']}'. Fine: ${fine:.2f}"
    )
    return {"record_id": record_id, "title": record["title"], "fine": fine}


def get_borrow_records(user_id: int = None) -> list[dict]:
    """Retrieve borrow records. If user_id is provided, filters for that user."""
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT r.id, r.borrow_date, r.due_date, r.return_date, r.status, r.fine_amount,
               b.title, b.author, b.isbn, u.username, u.full_name
        FROM borrow_records r
        JOIN books b ON r.book_id = b.id
        JOIN users u ON r.user_id = u.id
    """
    params = []
    if user_id:
        sql += " WHERE r.user_id = ?"
        params.append(user_id)

    sql += " ORDER BY r.borrow_date DESC"
    cursor.execute(sql, params)
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return records


def get_audit_logs(limit: int = 100) -> list[dict]:
    """Retrieve recent audit logs for the administrative security viewer."""
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
