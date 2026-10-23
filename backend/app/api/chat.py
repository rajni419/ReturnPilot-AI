"""
Chat API Router for ReturnPilot AI Multilingual Assistant.
Provides endpoints for AI dialogue, order retrieval, policy RAG, photo analysis, and confirmed return execution.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.auth import get_current_user
from ..core.database import get_db
from ..models.order import Order, OrderItem
from ..models.return_request import ReturnRequest
from ..models.user import User
from ..services.ai.conversation import ChatMessage, orchestrator
from ..services.eligibility.engine import evaluate_eligibility
from ..services.rag.policy_store import PolicySection, policy_store
from ..services.rag.retriever import retriever
from ..services.vision.photo_analyzer import PhotoAnalysisResult, photo_analyzer

router = APIRouter(prefix="/chat", tags=["AI Assistant"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(default="default-session")
    preferred_language: Optional[str] = Field(default="auto")  # auto | en | hi | hinglish
    order_number: Optional[str] = None
    sku: Optional[str] = None


class ActionConfirmRequest(BaseModel):
    session_id: str
    order_number: str
    sku: str
    resolution: str  # RETURN_REFUND | EXCHANGE_SIZE | REPLACEMENT_DAMAGED | PRODUCT_SUPPORT
    return_reason: str = Field(..., min_length=3, max_length=500)


class ActionConfirmResponse(BaseModel):
    success: bool
    message: str
    return_number: str
    status: str
    order_number: str
    sku: str
    resolution: str
    created_at: str


def generate_return_number(db: Session) -> str:
    """Generates unique return number like RET-0001."""
    last_return = db.query(ReturnRequest).order_by(ReturnRequest.id.desc()).first()
    next_id = (last_return.id + 1) if last_return else 1
    candidate = f"RET-{next_id:04d}"
    while db.query(ReturnRequest).filter(ReturnRequest.return_number == candidate).first():
        next_id += 1
        candidate = f"RET-{next_id:04d}"
    return candidate


@router.post(
    "/message",
    response_model=ChatMessage,
    status_code=status.HTTP_200_OK,
    summary="Send message to Multilingual AI Assistant",
    description="Processes natural language in English, Hindi, or Hinglish with RAG policy retrieval and order binding.",
)
def send_chat_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session_id = payload.session_id or f"sess-{current_user.id}"
    chat_msg = orchestrator.process_message(
        db=db,
        session_id=session_id,
        user=current_user,
        user_message=payload.message.strip(),
        preferred_language=payload.preferred_language or "auto",
        direct_order_number=payload.order_number,
        direct_sku=payload.sku,
    )
    return chat_msg


@router.post(
    "/confirm-action",
    response_model=ActionConfirmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Explicitly confirm and execute return/exchange submission",
    description="Validates eligibility and creates persistent ReturnRequest only after explicit customer confirmation.",
)
def confirm_return_action(
    payload: ActionConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    clean_order_num = payload.order_number.strip()
    clean_sku = payload.sku.strip()

    # 1. Enforce order ownership
    order = db.query(Order).filter(Order.order_number == clean_order_num).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{clean_order_num}' not found.",
        )

    if order.customer_email.strip().lower() != current_user.email.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot execute returns on orders belonging to another user.",
        )

    # 2. Locate item
    item = next((i for i in order.items if i.sku and i.sku.strip().lower() == clean_sku.lower()), None)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with SKU '{clean_sku}' not found in order '{clean_order_num}'.",
        )

    # 3. Deterministic eligibility verification
    eval_res = evaluate_eligibility(
        db=db,
        order_number=clean_order_num,
        customer_email=current_user.email,
        sku=clean_sku,
    )
    if not eval_res.eligible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item is ineligible for return: {eval_res.reason}",
        )

    # 4. Prevent duplicate active returns
    existing_active = (
        db.query(ReturnRequest)
        .filter(
            ReturnRequest.order_item_id == item.id,
            ReturnRequest.status.in_(["PENDING", "APPROVED", "PROCESSING"]),
        )
        .first()
    )
    if existing_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An active return request ({existing_active.return_number}) already exists for this item.",
        )

    # 5. Create persistent ReturnRequest
    return_num = generate_return_number(db)
    new_return = ReturnRequest(
        return_number=return_num,
        order_id=order.id,
        order_item_id=item.id,
        order_number=order.order_number,
        customer_email=current_user.email,
        sku=clean_sku,
        return_reason=f"[{payload.resolution}] {payload.return_reason.strip()}",
        status="PENDING",
    )
    db.add(new_return)
    db.commit()
    db.refresh(new_return)

    return ActionConfirmResponse(
        success=True,
        message=f"Return request {return_num} successfully created and scheduled for reverse pickup.",
        return_number=return_num,
        status="PENDING",
        order_number=order.order_number,
        sku=clean_sku,
        resolution=payload.resolution,
        created_at=new_return.created_at.isoformat(),
    )


@router.get(
    "/orders",
    summary="List authenticated customer's orders for chat selection",
)
def get_customer_orders_for_chat(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orders = (
        db.query(Order)
        .filter(Order.customer_email.ilike(current_user.email.strip()))
        .order_by(Order.order_date.desc())
        .all()
    )
    return [
        {
            "id": o.id,
            "order_number": o.order_number,
            "order_date": o.order_date.strftime("%Y-%m-%d") if o.order_date else "",
            "delivery_date": o.delivery_date.strftime("%Y-%m-%d") if o.delivery_date else None,
            "shipping_status": o.shipping_status,
            "total_amount": o.total_amount,
            "items": [
                {
                    "id": item.id,
                    "product_name": item.product_name,
                    "sku": item.sku,
                    "quantity": item.quantity,
                    "price": item.price,
                    "is_returnable": item.is_returnable,
                }
                for item in o.items
            ],
        }
        for o in orders
    ]


@router.post(
    "/upload-photo",
    response_model=PhotoAnalysisResult,
    summary="Upload product photo for defect analysis",
)
async def upload_defect_photo(
    file: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    # Validate MIME type
    if file.content_type.lower() not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. Please upload JPEG, PNG, or WebP.",
        )

    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 5MB limit.",
        )

    result = photo_analyzer.analyze_photo(
        file_bytes=file_bytes,
        file_name=file.filename or "upload.jpg",
        content_type=file.content_type,
        user_notes=notes,
    )
    return result


@router.get(
    "/policies",
    response_model=List[PolicySection],
    summary="List all store return policies",
)
def get_all_policies():
    return policy_store.get_all()
