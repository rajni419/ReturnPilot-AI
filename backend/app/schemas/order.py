"""
Pydantic schemas for Order and OrderItem validation and serialization.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Order Item Schemas
# ============================================================================

class OrderItemBase(BaseModel):
    product_name: str = Field(..., description="Name of the product")
    sku: Optional[str] = Field(None, description="Stock Keeping Unit identifier")
    quantity: int = Field(default=1, ge=1, description="Quantity ordered")
    price: float = Field(default=0.0, ge=0.0, description="Price per unit")
    is_returnable: bool = Field(default=True, description="Whether this item is eligible for return")


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Order Schemas
# ============================================================================

class OrderBase(BaseModel):
    order_number: str = Field(..., description="Unique order reference (e.g., ORD-1001)")
    customer_name: str = Field(..., description="Full name of customer")
    customer_email: str = Field(..., description="Customer email address")
    order_date: Optional[datetime] = Field(None, description="Date and time when order was placed")
    delivery_date: Optional[datetime] = Field(None, description="Date and time when order was delivered")
    shipping_status: Optional[str] = Field(default="DELIVERED", description="Current shipping status")
    total_amount: Optional[float] = Field(default=None, ge=0.0, description="Total order amount")


class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(default_factory=list, description="List of items in this order")


class OrderUpdate(BaseModel):
    shipping_status: Optional[str] = Field(None, description="Updated shipping status")
    delivery_date: Optional[datetime] = Field(None, description="Updated delivery date")
    customer_name: Optional[str] = Field(None, description="Updated customer name")
    customer_email: Optional[str] = Field(None, description="Updated customer email")


class OrderResponse(OrderBase):
    id: int
    total_amount: float
    created_at: datetime
    items: List[OrderItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
