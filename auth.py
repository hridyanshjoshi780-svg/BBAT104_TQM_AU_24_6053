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

