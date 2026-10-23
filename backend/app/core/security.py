"""
Security utilities for password hashing, token generation, email normalization, and JWT.
"""

import hashlib
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash
from email_validator import validate_email, EmailNotValidError
from jose import jwt, JWTError

# Password Hasher with Argon2id parameters
ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
)

# JWT Secret and Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "returnpilot-ai-super-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

COMMON_PASSWORDS = {
    "password",
    "password123",
    "12345678",
    "123456789",
    "qwerty123",
    "admin123",
    "welcome123",
    "letmein123",
    "iloveyou",
    "secret123",
}


def hash_password(password: str) -> str:
    """Hashes a password using Argon2id."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against an Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False


def normalize_and_validate_email(email: str) -> str:
    """
    Validates email format and normalizes it (lowercase, trimmed).
    Rejects malformed emails like 'rajni', 'rajni@', etc.
    Raises ValueError with a user-friendly message if invalid.
    """
    if not email or not isinstance(email, str):
        raise ValueError("Email address is required.")

    cleaned = email.strip()
    if not cleaned:
        raise ValueError("Email address cannot be empty.")

    # Reject obvious syntax anomalies
    if "@" not in cleaned:
        raise ValueError("Invalid email format: missing '@' symbol.")

    parts = cleaned.split("@")
    if len(parts) != 2:
        raise ValueError("Invalid email format: must contain exactly one '@'.")

    local_part, domain = parts
    if not local_part:
        raise ValueError("Invalid email format: missing username before '@'.")
    if not domain:
        raise ValueError("Invalid email format: missing domain after '@'.")

    if "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise ValueError("Invalid email format: domain must contain a valid top-level domain.")

    try:
        validated = validate_email(cleaned, check_deliverability=False)
        return validated.normalized
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email address: {str(e)}")


def validate_password_policy(password: str) -> Tuple[bool, str]:
    """
    Enforces password complexity:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character
    - Not in common passwords list
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if password.lower() in COMMON_PASSWORDS:
        return False, "Password is too common and easily guessed."

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)."

    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number (0-9)."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+[\]\\/`~;']", password):
        return False, "Password must contain at least one special character."

    return True, ""


def generate_secure_token() -> str:
    """Generates a cryptographically secure URL-safe token (32 bytes entropy)."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Computes SHA-256 hash of a token for secure database storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
