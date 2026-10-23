"""
API routes and endpoints package.
"""

from .orders import router as orders_router
from .returns import router as returns_router
from .auth import router as auth_router
from .chat import router as chat_router

__all__ = ["orders_router", "returns_router", "auth_router", "chat_router"]
