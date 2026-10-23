"""
ReturnPilot AI - Backend Application
An AI-powered e-commerce return and resolution system.
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure package imports work whether running from repo root or backend directory
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from backend.app.core.database import init_db
    from backend.app.api.orders import router as orders_router
    from backend.app.api.returns import router as returns_router
    from backend.app.api.auth import router as auth_router
except ImportError:
    from app.core.database import init_db
    from app.api.orders import router as orders_router
    from app.api.returns import router as returns_router
    from app.api.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events: initialize database tables on startup.
    """
    init_db()
    yield


# Initialize database tables on load
init_db()

# Initialize FastAPI application
app = FastAPI(
    title="ReturnPilot AI Backend",
    description="Backend API for ReturnPilot AI - E-commerce Return and Resolution System",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable Cross-Origin Resource Sharing (CORS) with credentials support
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register API Routers
app.include_router(orders_router, prefix="/api")
app.include_router(orders_router)
app.include_router(returns_router, prefix="/api")
app.include_router(returns_router)
app.include_router(auth_router, prefix="/api")
app.include_router(auth_router)


@app.get("/", tags=["General"])
def read_root():
    """
    Root endpoint to verify that the backend is running.
    """
    return {"message": "ReturnPilot AI Backend Running"}


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint to monitor API status.
    """
    return {"status": "healthy"}
