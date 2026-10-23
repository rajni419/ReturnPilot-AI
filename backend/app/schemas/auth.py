"""
Pydantic schemas for User Authentication, Email Verification, and Password Reset.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..core.security import normalize_and_validate_email, validate_password_policy


class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of user")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User account password")
    confirm_password: str = Field(..., description="Password confirmation")

    @model_validator(mode="after")
    def validate_registration(self):
        # 1. Normalize and validate email
        self.email = normalize_and_validate_email(self.email)

        # 2. Check password and confirmation match
        if self.password != self.confirm_password:
            raise ValueError("Password and password confirmation do not match.")

        # 3. Check password complexity policy
        is_valid, error_msg = validate_password_policy(self.password)
        if not is_valid:
            raise ValueError(error_msg)

        return self


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")

    @model_validator(mode="after")
    def validate_login(self):
        self.email = normalize_and_validate_email(self.email)
        return self


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1, description="Verification token")
    email: Optional[str] = Field(None, description="Optional email address")


class ResendVerificationRequest(BaseModel):
    email: str = Field(..., description="Registered email address")

    @model_validator(mode="after")
    def validate_email_field(self):
        self.email = normalize_and_validate_email(self.email)
        return self


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="Account email address")

    @model_validator(mode="after")
    def validate_email_field(self):
        self.email = normalize_and_validate_email(self.email)
        return self


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1, description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")

    @model_validator(mode="after")
    def validate_reset(self):
        if self.new_password != self.confirm_password:
            raise ValueError("New password and confirm password do not match.")

        is_valid, error_msg = validate_password_policy(self.new_password)
        if not is_valid:
            raise ValueError(error_msg)

        return self


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    message: Optional[str] = None


class MessageResponse(BaseModel):
    message: str
    success: bool = True
    dev_token: Optional[str] = None
