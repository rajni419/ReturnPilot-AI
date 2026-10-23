"""
Orders API router providing CRUD endpoints and lookup functionality.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.order import Order, OrderItem
from ..schemas.order import OrderCreate, OrderResponse, OrderUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description="Creates a new customer order with associated line items.",
)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
):
    # Check if order_number already exists
    existing = db.query(Order).filter(Order.order_number == order_in.order_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order with order number '{order_in.order_number}' already exists.",
        )

    # Compute total_amount if omitted
    total_amount = order_in.total_amount
    if total_amount is None:
        total_amount = sum(item.price * item.quantity for item in order_in.items)

    order = Order(
        order_number=order_in.order_number,
        customer_name=order_in.customer_name,
        customer_email=order_in.customer_email,
        order_date=order_in.order_date or datetime.now(timezone.utc),
        delivery_date=order_in.delivery_date,
        shipping_status=order_in.shipping_status or "DELIVERED",
        total_amount=round(total_amount, 2),
    )


    for item in order_in.items:
        order_item = OrderItem(
            product_name=item.product_name,
            sku=item.sku,
            quantity=item.quantity,
            price=round(item.price, 2),
            is_returnable=item.is_returnable,
        )
        order.items.append(order_item)

    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="List orders",
    description="Retrieve a paginated list of orders with optional filtering by email and status.",
)
def list_orders(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
    customer_email: Optional[str] = Query(None, description="Filter by customer email"),
    shipping_status: Optional[str] = Query(None, description="Filter by shipping status"),
    db: Session = Depends(get_db),
):
    query = db.query(Order)
    if customer_email:
        query = query.filter(Order.customer_email.ilike(f"%{customer_email}%"))
    if shipping_status:
        query = query.filter(Order.shipping_status.ilike(shipping_status))

    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders


@router.get(
    "/lookup/{order_number}",
    response_model=OrderResponse,
    summary="Lookup order by order number",
    description="Retrieve order details using customer-facing order number (e.g., ORD-1001).",
)
def lookup_order_by_number(
    order_number: str,
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with order number '{order_number}' not found.",
        )
    return order


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID",
    description="Retrieve order details by primary key ID.",
)
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found.",
        )
    return order


@router.patch(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Update order details",
    description="Update mutable fields of an order such as shipping status or delivery date.",
)
def update_order(
    order_id: int,
    order_in: OrderUpdate,
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found.",
        )

    if order_in.shipping_status is not None:
        order.shipping_status = order_in.shipping_status
    if order_in.delivery_date is not None:
        order.delivery_date = order_in.delivery_date
    if order_in.customer_name is not None:
        order.customer_name = order_in.customer_name
    if order_in.customer_email is not None:
        order.customer_email = order_in.customer_email

    db.commit()
    db.refresh(order)
    return order


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an order",
    description="Delete an order and its associated items.",
)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found.",
        )

    db.delete(order)
    db.commit()
    return None
