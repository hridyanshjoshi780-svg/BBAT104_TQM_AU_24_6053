"""
Web Application Module for BBAT104 TQM Library Management System (Review 2).
Provides browser-accessible interface and REST API endpoints for:
- User Authentication (Admin & Student roles)
- Interactive Dashboard with real-time KPI tiles and visual charts
- Fast Catalog Search with multi-attribute filtering and pagination
- Full CRUD operations for Books and Members
- Atomic Circulation Workflows (Book Issue & Return)
- Optimized Management Reports with CSV Export
- High-Throughput Bulk CSV Ingestion pipeline
- Health Check and Production Deployment configuration
"""

import os
import secrets
import time
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, Response
)

from database import init_db, get_connection
from auth import (
    authenticate_user, register_user, ValidationError
)
from library_service import (
    search_books_paginated, get_all_categories,
    add_book, get_book, update_book, delete_book,
    get_all_members, get_member, update_member, delete_member,
    issue_book, return_book, get_borrow_records, get_active_loans,
    get_dashboard_metrics, get_report_inventory_distribution,
    get_report_currently_issued, get_report_overdue_books,
    get_report_circulation_activity, get_report_member_summary,
    export_report_to_csv, get_sample_csv_template,
    import_books_from_csv, get_audit_logs
)

# Initialize Flask application
app = Flask(__name__)
app_environment = os.environ.get("APP_ENV", "development").strip().lower()
secret_key = os.environ.get("SECRET_KEY")
if app_environment == "production" and (not secret_key or len(secret_key) < 32):
    raise RuntimeError("Production SECRET_KEY must be configured with at least 32 characters.")
app.secret_key = secret_key or secrets.token_urlsafe(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# =============================================================================
# AUTHENTICATION HELPERS & DECORATORS
# =============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get("user")
        if not user or user.get("role") != "admin":
            flash("Administrator privilege is required for this action.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_active_page():
    return dict(
        active_page=request.endpoint,
        demo_accounts_enabled=app_environment != "production"
    )


# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@app.route("/")
def index():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = authenticate_user(username, password)
        if user:
            session["user"] = {
                "id": user["id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"]
            }
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password. Please try again.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))


# =============================================================================
# DASHBOARD (Q02 Feature 3)
# =============================================================================

@app.route("/dashboard")
@login_required
def dashboard():
    metrics = get_dashboard_metrics()
    return render_template("dashboard.html", metrics=metrics)


# =============================================================================
# BOOK CATALOG & FAST SEARCH (Q02 Feature 1 & Book CRUD)
# =============================================================================

@app.route("/catalog")
@login_required
def catalog():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "All")
    availability = request.args.get("availability", "All")
    page = request.args.get("page", 1, type=int) or 1

    search_res = search_books_paginated(
        query=query,
        category=category,
        availability=availability,
        page=page,
        per_page=15
    )
    categories = get_all_categories()

    return render_template(
        "catalog.html",
        search_res=search_res,
        categories=categories,
        query=query,
        category=category,
        availability=availability
    )


@app.route("/books/create", methods=["POST"])
@login_required
@admin_required
def create_book():
    title = request.form.get("title", "")
    author = request.form.get("author", "")
    isbn = request.form.get("isbn", "")
    category = request.form.get("category", "")
    copies = request.form.get("copies", "1")

    try:
        add_book(
            title=title,
            author=author,
            isbn=isbn,
            category=category,
            copies=int(copies),
            admin_user=session["user"]["username"]
        )
        flash(f"Book '{title}' successfully added to catalog.", "success")
    except ValidationError as e:
        flash(str(e), "error")
    except Exception:
        app.logger.exception("Book creation failed")
        flash("An unexpected error occurred while adding the book.", "error")

    return redirect(url_for("catalog"))


@app.route("/books/<int:book_id>/edit", methods=["POST"])
@login_required
@admin_required
def edit_book(book_id):
    title = request.form.get("title", "")
    author = request.form.get("author", "")
    isbn = request.form.get("isbn", "")
    category = request.form.get("category", "")
    copies = request.form.get("copies", "1")

    try:
        update_book(
            book_id=book_id,
            title=title,
            author=author,
            isbn=isbn,
            category=category,
            copies=int(copies),
            admin_user=session["user"]["username"]
        )
        flash(f"Book '{title}' updated successfully.", "success")
    except ValidationError as e:
        flash(str(e), "error")
    except Exception:
        app.logger.exception("Book update failed")
        flash("An unexpected error occurred while updating the book.", "error")

    return redirect(url_for("catalog"))


@app.route("/books/<int:book_id>/delete", methods=["POST"])
@login_required
@admin_required
def remove_book(book_id):
    try:
        res = delete_book(book_id=book_id, admin_user=session["user"]["username"])
        flash(f"Book '{res['title']}' was {res['status']}.", "success")
    except ValidationError as e:
        flash(str(e), "error")
    except Exception:
        app.logger.exception("Book deletion failed")
        flash("An unexpected error occurred while deleting the book.", "error")

    return redirect(url_for("catalog"))


# =============================================================================
# CIRCULATION (ISSUE & RETURN)
# =============================================================================

@app.route("/circulation")
@login_required
def circulation():
    current_user = session["user"]
    selected_book_id = request.args.get("book_id", type=int)

    # Fetch books with available copies for checkout
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, isbn, available_copies
        FROM books
        WHERE is_active = 1 AND available_copies > 0
        ORDER BY title ASC
    """)
    available_books = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if current_user["role"] == "admin":
        members, _ = get_all_members(limit=500)
        active_loans = get_active_loans()
        recent_history = get_borrow_records(limit=25)
    else:
        members = []
        active_loans = get_active_loans(user_id=current_user["id"])
        recent_history = get_borrow_records(user_id=current_user["id"], limit=25)

    return render_template(
        "circulation.html",
        available_books=available_books,
        members=members,
        active_loans=active_loans,
        recent_history=recent_history,
        selected_book_id=selected_book_id
    )


@app.route("/circulation/issue", methods=["POST"])
@login_required
def issue_book_route():
    book_id = request.form.get("book_id", type=int)
    user_id = request.form.get("user_id", type=int)
    if session["user"]["role"] != "admin":
        user_id = session["user"]["id"]
    loan_days = request.form.get("loan_days", 14, type=int)

    try:
        res = issue_book(
            book_id=book_id,
            user_id=user_id,
            username=session["user"]["username"],
            loan_days=loan_days
        )
        flash(
            f"Successfully issued '{res['title']}' to {res['username']}. "
            f"Due Date: {res['due_date']} (Processed in {res['duration_ms']} ms).",
            "success"
        )
    except ValidationError as e:
        flash(str(e), "error")
    except Exception:
        app.logger.exception("Book issue failed")
        flash("An unexpected error occurred while issuing the book.", "error")

    return redirect(url_for("circulation"))


@app.route("/circulation/<int:record_id>/return", methods=["POST"])
@login_required
def return_book_route(record_id):
    try:
        borrower_user_id = (
            None if session["user"]["role"] == "admin" else session["user"]["id"]
        )
        res = return_book(
            record_id=record_id,
            username=session["user"]["username"],
            borrower_user_id=borrower_user_id
        )
        fine_text = f" Overdue Fine Levied: ${res['fine']:.2f}" if res["fine"] > 0 else " No fines applicable."
        flash(
            f"Returned '{res['title']}' successfully in {res['duration_ms']} ms.{fine_text}",
            "success"
        )
    except ValidationError as e:
        flash(str(e), "error")
    except Exception:
        app.logger.exception("Book return failed")
        flash("An unexpected error occurred while returning the book.", "error")

    return redirect(url_for("circulation"))


# =============================================================================
# MEMBER MANAGEMENT
# =============================================================================

@app.route("/members")
@login_required
@admin_required
def members():
    query = request.args.get("q", "").strip()
    role = request.args.get("role", "All")

    members_list, total_count = get_all_members(query=query, role=role, limit=200)

    return render_template(
        "members.html",
        members_list=members_list,
        total_count=total_count,
        query=query,
        role=role
    )


@app.route("/members/create", methods=["POST"])
@login_required
@admin_required
def create_member():
    username = request.form.get("username", "")
    full_name = request.form.get("full_name", "")
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    role = request.form.get("role", "student")

    try:
        register_user(
            username=username,
            password=password,
            full_name=full_name,
            email=email,
            role=role
        )
        flash(f"Member '{username}' successfully registered.", "success")
    except ValidationError as e:
        flash(str(e), "error")
    except Exception:
        app.logger.exception("Member registration failed")
        flash("An unexpected error occurred while registering the member.", "error")

    return redirect(url_for("members"))


@app.route("/members/<int:user_id>/edit", methods=["POST"])
@login_required
@admin_required
def edit_member(user_id):
    full_name = request.form.get("full_name", "")
    email = request.form.get("email", "")
    role = request.form.get("role", "student")

    try:
        update_member(
            user_id=user_id,
            full_name=full_name,
            email=email,
            role=role,
            admin_user=session["user"]["username"]
        )
        flash("Member details updated successfully.", "success")
    except ValidationError as e:
        flash(str(e), "error")
    except Exception:
        app.logger.exception("Member update failed")
        flash("An unexpected error occurred while updating the member.", "error")

    return redirect(url_for("members"))


@app.route("/members/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def remove_member(user_id):
    try:
        res = delete_member(user_id=user_id, admin_user=session["user"]["username"])
        flash(f"Member '{res['username']}' was {res['status']}.", "success")
    except ValidationError as e:
        flash(str(e), "error")
    except Exception:
        app.logger.exception("Member deletion failed")
        flash("An unexpected error occurred while deleting the member.", "error")

    return redirect(url_for("members"))


# =============================================================================
# OPTIMIZED REPORTS & CSV EXPORT (Q02 Feature 2)
# =============================================================================

@app.route("/reports")
@login_required
@admin_required
def reports():
    report_type = request.args.get("type", "inventory")
    category = request.args.get("category", "All")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    start_time = time.perf_counter()

    if report_type == "inventory":
        data = get_report_inventory_distribution()
    elif report_type == "issued":
        data = get_report_currently_issued(category=category)
    elif report_type == "overdue":
        data = get_report_overdue_books()
    elif report_type == "circulation":
        data = get_report_circulation_activity(start_date=start_date, end_date=end_date)
    elif report_type == "members":
        data = get_report_member_summary()
    else:
        report_type = "inventory"
        data = get_report_inventory_distribution()

    duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    categories = get_all_categories()

    return render_template(
        "reports.html",
        report_type=report_type,
        data=data,
        duration_ms=duration_ms,
        categories=categories,
        category=category,
        start_date=start_date,
        end_date=end_date
    )


@app.route("/reports/export")
@login_required
@admin_required
def export_report_csv_route():
    report_type = request.args.get("type", "inventory")
    category = request.args.get("category", "All")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    try:
        csv_data = export_report_to_csv(
            report_type,
            category=category,
            start_date=start_date,
            end_date=end_date
        )
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=library_{report_type}_report.csv"}
        )
    except Exception:
        app.logger.exception("CSV export failed")
        flash("An unexpected error occurred while exporting the report.", "error")
        return redirect(url_for("reports"))


# =============================================================================
# BULK CSV IMPORT (Q02 Feature 4)
# =============================================================================

@app.route("/import-csv", methods=["GET"])
@login_required
@admin_required
def import_csv():
    return render_template("import_csv.html", summary=None)


@app.route("/import-csv/upload", methods=["POST"])
@login_required
@admin_required
def upload_csv_route():
    if "csv_file" not in request.files:
        flash("No file was uploaded.", "error")
        return redirect(url_for("import_csv"))

    file = request.files["csv_file"]
    if not file.filename or not file.filename.lower().endswith(".csv"):
        flash("Invalid file format. Please upload a standard comma-separated .csv file.", "error")
        return redirect(url_for("import_csv"))

    try:
        content = file.stream.read().decode("utf-8")
        summary = import_books_from_csv(
            csv_content=content,
            admin_user=session["user"]["username"]
        )
        flash(
            f"Bulk ingestion complete: {summary['inserted']} records inserted in {summary['duration_ms']} ms "
            f"({summary['throughput_per_sec']} records/sec).",
            "success"
        )
        return render_template("import_csv.html", summary=summary)
    except ValidationError as e:
        flash(str(e), "error")
        return redirect(url_for("import_csv"))
    except UnicodeDecodeError:
        flash("File encoding error: Please ensure the CSV is saved with UTF-8 encoding.", "error")
        return redirect(url_for("import_csv"))
    except Exception:
        app.logger.exception("CSV import failed")
        flash("An unexpected error occurred while importing the CSV file.", "error")
        return redirect(url_for("import_csv"))


@app.route("/api/csv-template")
def download_csv_template():
    csv_text = get_sample_csv_template()
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=library_books_import_template.csv"}
    )


# =============================================================================
# SECURITY AUDIT TRAIL
# =============================================================================

@app.route("/audit")
@login_required
@admin_required
def audit_logs_view():
    logs = get_audit_logs(limit=250)
    return render_template("audit.html", logs=logs)


# =============================================================================
# HEALTH CHECK & MONITORING
# =============================================================================

@app.route("/health")
def health_check():
    """Production health check endpoint verifying database connectivity."""
    db_status = "error"
    total_books = 0
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM books")
        total_books = cur.fetchone()["cnt"]
        conn.close()
        db_status = "connected"
    except Exception:
        app.logger.error("Database health check failed")
        db_status = "error"

    return jsonify({
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "project": "BBAT104 TQM Library Management System",
        "roll_number": 31,
        "quality_goal": "Q02 Improve Performance",
        "database": db_status,
        "catalog_count": total_books
    }), (200 if db_status == "connected" else 500)


# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"Starting BBAT104 Library Management System on http://localhost:{port}")
    app.run(host=host, port=port, debug=debug)
