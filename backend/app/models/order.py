"""
SQLAlchemy models for Orders and Order Items.
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

try:
    from ..core.database import Base
except (ImportError, ValueError):
    try:
        from backend.app.core.database import Base
    except ImportError:
        from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(100), index=True, nullable=False)
    order_date = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    delivery_date = Column(DateTime(timezone=True), nullable=True)
    shipping_status = Column(String(50), default="DELIVERED", nullable=False)
    total_amount = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


    # Relationships
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(200), nullable=False)
    sku = Column(String(50), nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    price = Column(Float, default=0.0, nullable=False)
    is_returnable = Column(Boolean, default=True, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
