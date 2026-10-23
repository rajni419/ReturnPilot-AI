"""
Returns API router for return eligibility check and resolution.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.order import Order, OrderItem
from ..models.return_request import ReturnRequest
from ..schemas.returns import (
    ReturnCheckRequest,
    ReturnCheckResponse,
    ReturnCreateRequest,
    ReturnResponse,
)

router = APIRouter(prefix="/returns", tags=["Returns"])

RETURN_WINDOW_DAYS = 7
ACTIVE_STATUSES = ["PENDING", "APPROVED", "PROCESSING"]


def verify_eligibility(
    db: Session,
    order_number: str,
    customer_email: str,
    sku: str,
) -> Tuple[bool, str, Optional[Order], Optional[OrderItem]]:
    """
    Core reusable logic to verify whether an order item is eligible for return.
    Returns (eligible, reason, order_obj, order_item_obj).
    """
    clean_order_number = order_number.strip()
    clean_email = customer_email.strip().lower()
    clean_sku = sku.strip()

    # 1. Verify that the order exists
    order = db.query(Order).filter(Order.order_number == clean_order_number).first()
    if not order:
        return (False, f"Order '{order_number}' was not found.", None, None)

    # 2. Verify that customer_email matches the order
    if order.customer_email.strip().lower() != clean_email:
        return (False, "Customer email does not match order records.", order, None)

    # 3. Find the requested SKU in that order
    matching_item = None
    for item in order.items:
        if item.sku and item.sku.strip().lower() == clean_sku.lower():
            matching_item = item
            break

    if not matching_item:
        return (False, f"Item with SKU '{sku}' was not found in order '{order_number}'.", order, None)

    # 4. Reject the return if the item is not marked returnable
    if not matching_item.is_returnable:
        return (False, f"Item with SKU '{sku}' is not marked as returnable.", order, matching_item)

    # 5. Check delivery date and 7-day return window
    if not order.delivery_date:
        return (False, "Order has not been delivered yet or delivery date is missing.", order, matching_item)

    now = datetime.now(timezone.utc)
    delivery = order.delivery_date
    if delivery.tzinfo is None:
        delivery = delivery.replace(tzinfo=timezone.utc)

    if (now - delivery) > timedelta(days=RETURN_WINDOW_DAYS):
        return (
            False,
            f"Return window of {RETURN_WINDOW_DAYS} days has expired (delivered on {delivery.strftime('%Y-%m-%d')}).",
            order,
            matching_item,
        )

    return (
        True,
        f"Item with SKU '{sku}' is eligible for return within the {RETURN_WINDOW_DAYS}-day return window.",
        order,
        matching_item,
    )


def generate_return_number(db: Session) -> str:
    """
    Generates a unique return request identifier, such as RET-0001.
    """
    last_return = db.query(ReturnRequest).order_by(ReturnRequest.id.desc()).first()
    next_id = (last_return.id + 1) if last_return else 1
    candidate = f"RET-{next_id:04d}"
    while db.query(ReturnRequest).filter(ReturnRequest.return_number == candidate).first():
        next_id += 1
        candidate = f"RET-{next_id:04d}"
    return candidate


@router.post(
    "/check",
    response_model=ReturnCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Check return eligibility",
    description="Check whether an order item is eligible for return based on customer credentials, item returnability, and the 7-day delivery window.",
)
def check_return_eligibility(
    payload: ReturnCheckRequest,
    db: Session = Depends(get_db),
):
    eligible, reason, _, _ = verify_eligibility(
        db,
        payload.order_number,
        payload.customer_email,
        payload.sku,
    )
    return ReturnCheckResponse(
        eligible=eligible,
        reason=reason,
        order_number=payload.order_number,
        sku=payload.sku,
    )


@router.post(
    "/",
    response_model=ReturnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a return request",
    description="Validates return eligibility and creates an actual return request with status PENDING.",
)
def create_return_request(
    payload: ReturnCreateRequest,
    db: Session = Depends(get_db),
):
    # 1. Reuse existing return eligibility logic
    eligible, reason, order, matching_item = verify_eligibility(
        db,
        payload.order_number,
        payload.customer_email,
        payload.sku,
    )
    if not eligible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason,
        )

    # 2. Prevent duplicate active return requests for the same order item
    existing_active = (
        db.query(ReturnRequest)
        .filter(
            ReturnRequest.order_item_id == matching_item.id,
            ReturnRequest.status.in_(ACTIVE_STATUSES),
        )
        .first()
    )
    if existing_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An active return request ({existing_active.return_number}) already exists for this order item.",
        )

    # 3. Create return request with unique return number and initial PENDING status
    new_return = ReturnRequest(
        return_number=generate_return_number(db),
        order_id=order.id,
        order_item_id=matching_item.id,
        order_number=order.order_number,
        customer_email=order.customer_email,
        sku=payload.sku,
        return_reason=payload.return_reason,
        status="PENDING",
    )

    db.add(new_return)
    db.commit()
    db.refresh(new_return)
    return new_return


@router.get(
    "/",
    response_model=List[ReturnResponse],
    summary="List return requests",
    description="Retrieve a paginated list of return requests with optional filtering.",
)
def list_return_requests(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
    order_number: Optional[str] = Query(None, description="Filter by order number"),
    customer_email: Optional[str] = Query(None, description="Filter by customer email"),
    status: Optional[str] = Query(None, description="Filter by return status"),
    db: Session = Depends(get_db),
):
    query = db.query(ReturnRequest)
    if order_number:
        query = query.filter(ReturnRequest.order_number == order_number.strip())
    if customer_email:
        query = query.filter(ReturnRequest.customer_email.ilike(f"%{customer_email.strip()}%"))
    if status:
        query = query.filter(ReturnRequest.status.ilike(status.strip()))

    return query.order_by(ReturnRequest.created_at.desc()).offset(skip).limit(limit).all()


@router.get(
    "/{return_id}",
    response_model=ReturnResponse,
    summary="Get return request by ID",
    description="Retrieve details of a single return request by its primary key ID.",
)
def get_return_request(
    return_id: int,
    db: Session = Depends(get_db),
):
    return_obj = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not return_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Return request with ID {return_id} not found.",
        )
    return return_obj
