"""
Pydantic schemas package for request/response validation.
"""

from .order import (
    OrderItemBase,
    OrderItemCreate,
    OrderItemResponse,
    OrderBase,
    OrderCreate,
    OrderUpdate,
    OrderResponse,
)

from .returns import (
    ReturnCheckRequest,
    ReturnCheckResponse,
    ReturnCreateRequest,
    ReturnResponse,
)

from .auth import (
    UserRegisterRequest,
    UserLoginRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserResponse,
    AuthResponse,
    MessageResponse,
)

__all__ = [
    "OrderItemBase",
    "OrderItemCreate",
    "OrderItemResponse",
    "OrderBase",
    "OrderCreate",
    "OrderUpdate",
    "OrderResponse",
    "ReturnCheckRequest",
    "ReturnCheckResponse",
    "ReturnCreateRequest",
    "ReturnResponse",
    "UserRegisterRequest",
    "UserLoginRequest",
    "VerifyEmailRequest",
    "ResendVerificationRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "UserResponse",
    "AuthResponse",
    "MessageResponse",
]
