"""
Authentication and Security Module for Library Management System (Q04 Compliance).
Handles Role-Based Access Control, Password Security, Input Validation, Reset, and Audit Logging.
"""

import re
from datetime import datetime
from database import get_connection, hash_password, verify_password


class ValidationError(Exception):
    """Exception raised for input validation failures."""
    pass


def validate_username(username: str) -> str:
    """Validate username format (alphanumeric and underscores, 3-20 chars)."""
    username = (username or "").strip()
    if not username:
        raise ValidationError("Username cannot be empty.")
    if len(username) < 3 or len(username) > 20:
        raise ValidationError("Username must be between 3 and 20 characters.")
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        raise ValidationError("Username can only contain letters, numbers, and underscores.")
    return username


def validate_email(email: str) -> str:
    """Validate email address format."""
    email = (email or "").strip().lower()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not email or not re.match(pattern, email):
        raise ValidationError("Please provide a valid email address.")
    return email


def validate_password(password: str) -> str:
    """Validate password strength (minimum 6 characters)."""
    if not password or len(password) < 6:
        raise ValidationError("Password must be at least 6 characters long.")
    return password


def sanitize_text(text: str) -> str:
    """Sanitize generic text input to prevent basic injection."""
    if text is None:
        return ""
    # Strip dangerous characters and whitespace
    clean = text.strip()
    clean = re.sub(r"[<>]", "", clean)  # Strip HTML tags
    return clean


def log_audit_trail(username: str, action: str, details: str = "", user_id: int = None):
    """Record security event or system modification into the audit trail."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO audit_logs (username, action, details, user_id)
               VALUES (?, ?, ?, ?)""",
            (username, action, details, user_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Audit Log Warning] Could not record audit trail: {e}")


def authenticate_user(username: str, password: str, expected_role: str = None) -> dict | None:
    """
    Authenticate a user with username, password, and optional expected role.
    Records successful and failed login attempts in the audit trail.
    """
    username = (username or "").strip()
    if not username or not password:
        log_audit_trail(username or "UNKNOWN", "LOGIN_FAILED", "Empty username or password provided.")
        return None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        log_audit_trail(username, "LOGIN_FAILED", "User does not exist.")
        return None

    if not verify_password(password, user["password_hash"], user["salt"]):
        log_audit_trail(username, "LOGIN_FAILED", "Incorrect password attempt.", user_id=user["id"])
        return None

    if expected_role and user["role"] != expected_role:
        log_audit_trail(
            username,
            "LOGIN_FAILED",
            f"Unauthorized role attempt: required '{expected_role}', but user is '{user['role']}'.",
            user_id=user["id"]
        )
        return None

    # Authentication successful
    log_audit_trail(username, "LOGIN_SUCCESS", f"User logged in successfully with role '{user['role']}'.", user_id=user["id"])
    return dict(user)


def register_user(username: str, password: str, full_name: str, email: str, role: str = "student") -> dict:
    """
    Register a new user with input sanitization and password hashing.
    """
    username = validate_username(username)
    email = validate_email(email)
    password = validate_password(password)
    full_name = sanitize_text(full_name)
    if not full_name:
        raise ValidationError("Full name cannot be empty.")

    if role not in ("admin", "student"):
        role = "student"

    conn = get_connection()
    cursor = conn.cursor()

    # Check if username or email already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        raise ValidationError(f"Username '{username}' is already taken.")

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        raise ValidationError(f"Email '{email}' is already registered.")

    pw_hash, salt = hash_password(password)

    cursor.execute(
        """INSERT INTO users (username, password_hash, salt, role, full_name, email)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (username, pw_hash, salt, role, full_name, email)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_audit_trail(username, "USER_REGISTERED", f"New user '{username}' registered with role '{role}'.", user_id=user_id)
    return {"id": user_id, "username": username, "role": role, "full_name": full_name, "email": email}


def reset_password(username: str, email: str, new_password: str) -> bool:
    """
    Reset user password after verifying username and registered email.
    """
    username = validate_username(username)
    email = validate_email(email)
    new_password = validate_password(new_password)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND email = ?", (username, email))
    user = cursor.fetchone()

    if not user:
        conn.close()
        log_audit_trail(username, "PASSWORD_RESET_FAILED", f"Password reset attempted with invalid email '{email}'.")
        raise ValidationError("No matching user found with the provided username and email.")

    pw_hash, salt = hash_password(new_password)
    cursor.execute(
        "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
        (pw_hash, salt, user["id"])
    )
    conn.commit()
    conn.close()

    log_audit_trail(username, "PASSWORD_RESET_SUCCESS", "Password was successfully reset.", user_id=user["id"])
    return True
