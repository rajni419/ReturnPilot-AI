"""
FastAPI authentication dependencies for current user retrieval and token verification.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .database import get_db
from .security import decode_access_token
from ..models.user import User, UserSession


def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Extracts authentication token from Authorization header or HttpOnly cookie.
    Explicit Authorization header takes precedence.
    """
    # 1. Check Authorization Bearer header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    # 2. Check HttpOnly cookie
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        # If stored as 'Bearer <token>' in cookie, strip prefix
        if cookie_token.startswith("Bearer "):
            return cookie_token[7:].strip()
        return cookie_token.strip()

    return None


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that validates session and returns current authenticated User.
    Raises HTTP 401 if token is missing, expired, revoked, or user not found.
    """
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    session_token = payload.get("sid")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed user identifier.",
        )

    user = db.query(User).filter(User.id == user_id_int).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    # Validate active session in database (ensures logout revocation works across tokens)
    if session_token:
        now = datetime.now(timezone.utc)
        session_record = (
            db.query(UserSession)
            .filter(
                UserSession.session_token == session_token,
                UserSession.user_id == user.id,
            )
            .first()
        )
        if not session_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired or was revoked.",
            )

        if session_record.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been revoked.",
            )

        session_expires = session_record.expires_at
        if session_expires.tzinfo is None:
            session_expires = session_expires.replace(tzinfo=timezone.utc)

        if session_expires < now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired.",
            )

    return user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Requires that the authenticated user has verified their email address.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address has not been verified.",
        )
    return current_user
