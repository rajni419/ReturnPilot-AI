"""
SQLAlchemy model for Return Requests.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

try:
    from ..core.database import Base
except (ImportError, ValueError):
    try:
        from backend.app.core.database import Base
    except ImportError:
        from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True, index=True)
    return_number = Column(String(50), unique=True, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True)
    order_number = Column(String(50), nullable=False, index=True)
    customer_email = Column(String(100), nullable=False, index=True)
    sku = Column(String(50), nullable=False)
    return_reason = Column(String(500), nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    order = relationship(
        "Order",
        backref=backref("return_requests", cascade="all, delete-orphan"),
    )
    order_item = relationship(
        "OrderItem",
        backref=backref("return_requests", cascade="all, delete-orphan"),
    )


