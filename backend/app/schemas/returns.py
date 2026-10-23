"""
Pydantic schemas for return eligibility checks.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ReturnCheckRequest(BaseModel):
    order_number: str = Field(..., description="Unique order reference (e.g., ORD-1001)")
    customer_email: str = Field(..., description="Email address associated with the order")
    sku: str = Field(..., description="Stock Keeping Unit of the item to return")


class ReturnCheckResponse(BaseModel):
    eligible: bool = Field(..., description="Whether the item is eligible for return")
    reason: str = Field(..., description="Explanation of eligibility status")
    order_number: str = Field(..., description="The order number checked")
    sku: str = Field(..., description="The SKU checked")

    model_config = ConfigDict(from_attributes=True)


class ReturnCreateRequest(BaseModel):
    order_number: str = Field(..., description="Unique order reference (e.g., ORD-1001)")
    customer_email: str = Field(..., description="Customer email address")
    sku: str = Field(..., description="Stock Keeping Unit of the item to return")
    return_reason: str = Field(..., description="Reason for requesting return", min_length=1, max_length=500)


class ReturnResponse(BaseModel):
    id: int
    return_number: str = Field(..., description="Unique return request identifier (e.g., RET-0001)")
    order_id: int
    order_item_id: int
    order_number: str
    customer_email: str
    sku: str
    return_reason: str
    status: str = Field(default="PENDING", description="Return request status (e.g. PENDING)")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

