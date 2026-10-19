"""
Database module for Library Management System (BBAT104 TQM Project)
Provides SQLite schema management, initial seeding, and thread-safe connections.
"""

import os
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")


def get_db_path() -> str:
    """Return active SQLite database file path from environment or default."""
    return os.environ.get("DATABASE_PATH", DB_FILE)


def get_connection(db_path: str = None):
    """Create and return an optimized database connection with row factory enabled."""
    target_db = db_path or get_db_path()
    conn = sqlite3.connect(target_db, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn



def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Securely hash a password with PBKDF2-HMAC-SHA256 and salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return key.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify input password against stored hash using the provided salt."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)


def init_db(db_path: str = None):
    """Initialize SQLite database tables, apply migrations, build indexes, and seed default data if empty."""
    production = os.environ.get("APP_ENV", "development").strip().lower() == "production"
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if production and not admin_password:
        raise RuntimeError("ADMIN_PASSWORD must be configured before initializing a production database.")
    if production and (len(admin_password) < 12 or admin_password == "admin123"):
        raise RuntimeError("Production ADMIN_PASSWORD must be at least 12 characters and not use the demo password.")
    if admin_password is not None and len(admin_password) < 6:
        raise RuntimeError("ADMIN_PASSWORD must be at least 6 characters long.")
    if not production and not admin_password:
        admin_password = "admin123"

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode = WAL")

    # 1. Users table (Admin & Student roles)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'student')) NOT NULL DEFAULT 'student',
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Books catalog
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            total_copies INTEGER NOT NULL DEFAULT 1,
            available_copies INTEGER NOT NULL DEFAULT 1,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Borrow records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS borrow_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            borrow_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TIMESTAMP NOT NULL,
            return_date TIMESTAMP,
            status TEXT CHECK(status IN ('BORROWED', 'RETURNED')) DEFAULT 'BORROWED',
            fine_amount REAL DEFAULT 0.0,
            FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # 4. Audit Trail (Q04 Security Requirement)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            username TEXT,
            action TEXT NOT NULL,
            details TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
    """)

    # 5. Search Latency Metrics for SQC Quality Control Charts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            query TEXT,
            duration_ms REAL NOT NULL,
            result_count INTEGER NOT NULL
        )
    """)

    conn.commit()

    cursor.execute("BEGIN IMMEDIATE")

    # Seed initial users if table is empty
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()['count'] == 0:
        admin_hash, admin_salt = hash_password(admin_password)
        cursor.execute(
            """INSERT INTO users (username, password_hash, salt, role, full_name, email)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("admin", admin_hash, admin_salt, "admin", "System Administrator", "admin@library.edu")
        )

        if not production:
            student_hash, student_salt = hash_password("student123")
            cursor.execute(
                """INSERT INTO users (username, password_hash, salt, role, full_name, email)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("student1", student_hash, student_salt, "student", "Hridyansh (Student)", "student1@library.edu")
            )

        # Log system initialization in Audit Trail
        cursor.execute(
            """INSERT INTO audit_logs (username, action, details)
               VALUES (?, ?, ?)""",
            ("SYSTEM", "INITIALIZE", "Database initialized with configured user accounts.")
        )

    # Seed initial books if table is empty
    cursor.execute("SELECT COUNT(*) as count FROM books")
    if cursor.fetchone()['count'] == 0:
        sample_books = [
            ("Total Quality Management", "Dale H. Besterfield", "978-0130993069", "Management", 5, 5),
            ("Python Crash Course", "Eric Matthes", "978-1593279288", "Computer Science", 4, 4),
            ("Introduction to Algorithms", "Thomas H. Cormen", "978-0262033848", "Computer Science", 3, 3),
            ("Database System Concepts", "Abraham Silberschatz", "978-0078022159", "Computer Science", 4, 4),
            ("Statistical Quality Control", "Douglas C. Montgomery", "978-1118146811", "Quality Engineering", 3, 3),
            ("Clean Code", "Robert C. Martin", "978-0132350884", "Software Engineering", 5, 5),
            ("Operations Management", "William J. Stevenson", "978-1259667473", "Management", 2, 2)
        ]

        cursor.executemany(
            """INSERT INTO books (title, author, isbn, category, total_copies, available_copies)
               VALUES (?, ?, ?, ?, ?, ?)""",
            sample_books
        )

        # Generate some initial search metrics for SQC chart demonstration
        import random
        base_time = datetime.now() - timedelta(days=5)
        metrics = []
        for i in range(25):
            t = base_time + timedelta(hours=i * 4)
            # Simulated search response time with slight variance (e.g. 12-25 ms)
            duration = round(random.gauss(18.5, 3.2), 2)
            duration = max(8.0, duration)
            metrics.append((t.strftime("%Y-%m-%d %H:%M:%S"), "TQM sample search", duration, random.randint(1, 5)))

        cursor.executemany(
            """INSERT INTO search_metrics (timestamp, query, duration_ms, result_count)
               VALUES (?, ?, ?, ?)""",
            metrics
        )

    conn.commit()

    # Apply backward-compatible migrations: ensure is_active column exists
    for table in ("users", "books"):
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

    if production:
        cursor.execute(
            "SELECT id, password_hash, salt FROM users WHERE username = ?",
            ("admin",)
        )
        admin = cursor.fetchone()
        if admin and verify_password("admin123", admin["password_hash"], admin["salt"]):
            password_hash, salt = hash_password(admin_password)
            cursor.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                (password_hash, salt, admin["id"])
            )
            cursor.execute(
                """INSERT INTO audit_logs (username, action, details)
                   VALUES (?, ?, ?)""",
                ("SYSTEM", "ADMIN_PASSWORD_ROTATED", "Replaced the development default administrator credential.")
            )

        cursor.execute("SELECT id, password_hash, salt FROM users WHERE username = ?", ("student1",))
        student = cursor.fetchone()
        if student and verify_password("student123", student["password_hash"], student["salt"]):
            cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?", (student["id"],))
        conn.commit()

    # 6. Strategic B-Tree Indexes for Q02 Performance Requirements
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_title_author ON books(title, author)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_category ON books(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_borrow_lookup ON borrow_records(user_id, book_id, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_borrow_due_status ON borrow_records(status, due_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON search_metrics(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)")
    conn.commit()

    cursor.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)")
    try:
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS books_search
            USING fts5(title, author, isbn, content='books', content_rowid='id', tokenize='trigram')
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS books_search_insert
            AFTER INSERT ON books
            BEGIN
                INSERT INTO books_search(rowid, title, author, isbn)
                VALUES (new.id, new.title, new.author, new.isbn);
            END
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS books_search_update
            AFTER UPDATE OF title, author, isbn ON books
            BEGIN
                INSERT INTO books_search(books_search, rowid, title, author, isbn)
                VALUES ('delete', old.id, old.title, old.author, old.isbn);
                INSERT INTO books_search(rowid, title, author, isbn)
                VALUES (new.id, new.title, new.author, new.isbn);
            END
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS books_search_delete
            AFTER DELETE ON books
            BEGIN
                INSERT INTO books_search(books_search, rowid, title, author, isbn)
                VALUES ('delete', old.id, old.title, old.author, old.isbn);
            END
        """)
        cursor.execute(
            "SELECT 1 FROM schema_migrations WHERE name = ?",
            ("books_search_trigram",)
        )
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO books_search(books_search) VALUES ('rebuild')")
            cursor.execute(
                "INSERT INTO schema_migrations(name) VALUES (?)",
                ("books_search_trigram",)
            )
        conn.commit()
    except sqlite3.OperationalError as exc:
        conn.rollback()
        conn.close()
        raise RuntimeError(
            "SQLite FTS5 trigram support is required for indexed catalog substring search."
        ) from exc

    conn.close()


def explain_query(sql: str, params: tuple = (), db_path: str = None) -> list[dict]:
    """Execute EXPLAIN QUERY PLAN on the given SQL query and return plan steps."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(f"EXPLAIN QUERY PLAN {sql}", params)
    plan = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return plan


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", get_db_path())
