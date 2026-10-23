"""
Authentication API router providing registration, verification, login, profile, logout, and password recovery.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from ..core.auth import extract_token_from_request, get_current_user
from ..core.database import get_db
from ..core.rate_limit import limiter
from ..core.security import (
    create_access_token,
    decode_access_token,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from ..models.user import EmailVerificationToken, PasswordResetToken, User, UserSession
from ..schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    MessageResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    VerifyEmailRequest,
)
from ..services.email import (
    dev_outbox,
    is_smtp_configured,
    send_password_reset_email,
    send_verification_email,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_ip(request: Request) -> str:
    """Extracts client IP address for rate limiting."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Creates a new account, generates an email verification token, and sends a verification link.",
)
def register_user(
    payload: UserRegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)
    allowed, retry_after = limiter.check_rate_limit(f"register:{ip}", max_requests=10, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many registration attempts. Please try again in {retry_after} seconds.",
        )

    # Check for existing email (case-insensitive normalized)
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Hash password with Argon2id
    hashed = hash_password(payload.password)

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email,
        hashed_password=hashed,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate cryptographically secure verification token (valid 30 mins)
    raw_token = generate_secure_token()
    token_rec = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        used=False,
    )
    db.add(token_rec)
    db.commit()

    # Dispatch verification email
    sent, _ = send_verification_email(user.email, user.full_name, raw_token)

    # If SMTP is not configured, attach dev token header in dev environments for testing convenience
    if not is_smtp_configured():
        response.headers["X-Dev-Verification-Token"] = raw_token

    return user


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify user email address",
    description="Validates the verification token and activates normal account sign-in.",
)
def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)
    allowed, retry_after = limiter.check_rate_limit(f"verify:{ip}", max_requests=20, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many verification attempts. Please try again in {retry_after} seconds.",
        )

    raw_token = payload.token.strip()
    token_h = hash_token(raw_token)

    token_rec = (
        db.query(EmailVerificationToken)
        .filter(EmailVerificationToken.token_hash == token_h)
        .first()
    )

    if not token_rec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token.",
        )

    if token_rec.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification token has already been used.",
        )

    now = datetime.now(timezone.utc)
    token_expires = token_rec.expires_at
    if token_expires.tzinfo is None:
        token_expires = token_expires.replace(tzinfo=timezone.utc)

    if token_expires < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please request a new verification email.",
        )

    # Mark token used
    token_rec.used = True

    # Mark user verified
    user = db.query(User).filter(User.id == token_rec.user_id).first()
    if user:
        user.is_verified = True
        user.verified_at = now

    db.commit()

    return MessageResponse(
        message="Email address verified successfully. You can now sign in.",
        success=True,
    )


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend email verification link",
    description="Sends a new verification token with cooldown rate limiting.",
)
def resend_verification(
    payload: ResendVerificationRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    email = payload.email

    # Enforce 60-second cooldown per email
    allowed_cooldown, retry_after = limiter.check_cooldown(f"resend_cooldown:{email}", cooldown_seconds=60)
    if not allowed_cooldown:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {retry_after} seconds before requesting another verification email.",
        )

    # Max 5 per hour
    allowed_hourly, retry_after_h = limiter.check_rate_limit(f"resend_hourly:{email}", max_requests=5, window_seconds=3600)
    if not allowed_hourly:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Hourly resend limit reached. Please try again in {retry_after_h} seconds.",
        )

    user = db.query(User).filter(User.email == email).first()

    # Generic response if user not found to prevent enumeration
    if not user:
        return MessageResponse(
            message="If an unverified account exists with this email, a verification link has been sent.",
            success=True,
        )

    if user.is_verified:
        return MessageResponse(
            message="This account is already verified. You can sign in.",
            success=True,
        )

    # Expire old unused tokens
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.used == False,
    ).update({"used": True})

    # Generate new token
    raw_token = generate_secure_token()
    token_rec = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        used=False,
    )
    db.add(token_rec)
    db.commit()

    send_verification_email(user.email, user.full_name, raw_token)

    dev_token = raw_token if not is_smtp_configured() else None
    if dev_token:
        response.headers["X-Dev-Verification-Token"] = dev_token

    return MessageResponse(
        message="A new verification email has been sent.",
        success=True,
        dev_token=dev_token,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="User sign in",
    description="Authenticates credentials, verifies email status, and issues an access token and HttpOnly cookie.",
)
def login_user(
    payload: UserLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)
    allowed, retry_after = limiter.check_rate_limit(f"login:{ip}", max_requests=15, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many sign-in attempts. Please try again in {retry_after} seconds.",
        )

    user = db.query(User).filter(User.email == payload.email).first()

    # Constant-time dummy verify if user not found to prevent timing side-channel
    if not user:
        # Run dummy Argon2 verify with fixed hash to equalize timing
        dummy_hash = "$argon2id$v=19$m=65536,t=2,p=1$fakefakepassworddummyhash$fakefakepassworddummyhashfakepass"
        verify_password("wrong", dummy_hash)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support.",
        )

    # Enforce email verification requirement
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not verified. Please verify your email before logging in.",
        )

    # Create persistent session record in database
    session_token = generate_secure_token()
    now = datetime.now(timezone.utc)
    session_expires = now + timedelta(days=7)

    new_session = UserSession(
        user_id=user.id,
        session_token=session_token,
        expires_at=session_expires,
        is_revoked=False,
    )
    db.add(new_session)
    db.commit()

    # Generate JWT access token
    token_claims = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.full_name,
        "sid": session_token,
    }
    access_token = create_access_token(token_claims, expires_delta=timedelta(days=7))

    # Set secure HttpOnly cookie
    is_secure = request.url.is_secure or request.headers.get("X-Forwarded-Proto") == "https"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=7 * 86400,
    )

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        message="Signed in successfully.",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="User sign out",
    description="Invalidates current session and clears the authentication cookie.",
)
def logout_user(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token = extract_token_from_request(request)
    if token:
        payload = decode_access_token(token)
        if payload and payload.get("sid"):
            session_token = payload["sid"]
            session_rec = (
                db.query(UserSession)
                .filter(UserSession.session_token == session_token)
                .first()
            )
            if session_rec:
                session_rec.is_revoked = True
                db.commit()

    # Delete HttpOnly cookie
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
    )

    return MessageResponse(
        message="Signed out successfully.",
        success=True,
    )


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Generates a password reset token and dispatches reset instructions.",
)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)
    allowed, retry_after = limiter.check_rate_limit(f"forgot:{ip}", max_requests=10, window_seconds=900)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many password reset requests. Please try again in {retry_after} seconds.",
        )

    user = db.query(User).filter(User.email == payload.email).first()

    dev_token = None
    if user and user.is_active:
        # Invalidate existing unused reset tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,
        ).update({"used": True})

        raw_token = generate_secure_token()
        token_rec = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            used=False,
        )
        db.add(token_rec)
        db.commit()

        send_password_reset_email(user.email, user.full_name, raw_token)

        if not is_smtp_configured():
            dev_token = raw_token
            response.headers["X-Dev-Reset-Token"] = raw_token

    # Always return identical generic response to prevent account enumeration
    return MessageResponse(
        message="If an account exists with this email address, password reset instructions have been sent.",
        success=True,
        dev_token=dev_token,
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset",
    description="Validates the reset token, updates password, and revokes all active user sessions.",
)
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)
    allowed, retry_after = limiter.check_rate_limit(f"reset:{ip}", max_requests=10, window_seconds=900)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many reset attempts. Please try again in {retry_after} seconds.",
        )

    raw_token = payload.token.strip()
    token_h = hash_token(raw_token)

    token_rec = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_h)
        .first()
    )

    if not token_rec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unrecognized password reset token.",
        )

    if token_rec.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has already been used.",
        )

    now = datetime.now(timezone.utc)
    token_expires = token_rec.expires_at
    if token_expires.tzinfo is None:
        token_expires = token_expires.replace(tzinfo=timezone.utc)

    if token_expires < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired. Please request a new one.",
        )

    user = db.query(User).filter(User.id == token_rec.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated user account not found.",
        )

    # Hash new password with Argon2id
    user.hashed_password = hash_password(payload.new_password)
    user.updated_at = now

    # Mark token used
    token_rec.used = True

    # Revoke all active sessions of this user (forces re-login across all devices)
    db.query(UserSession).filter(UserSession.user_id == user.id).update({"is_revoked": True})

    db.commit()

    return MessageResponse(
        message="Password has been reset successfully. You can now sign in with your new password.",
        success=True,
    )
