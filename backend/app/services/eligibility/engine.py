"""
Deterministic Eligibility and Resolution Engine for ReturnPilot AI.
Enforces business rules, order status, return windows, category policies, and resolution options.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...models.order import Order, OrderItem
from ...models.return_request import ReturnRequest


class ResolutionOption(BaseModel):
    id: str  # RETURN_REFUND, EXCHANGE_SIZE, REPLACEMENT_DAMAGED, PRODUCT_SUPPORT
    title: str
    description: str
    timeline: str
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    badge: Optional[str] = None
    is_recommended: bool = False


class EligibilityEvaluation(BaseModel):
    eligible: bool
    order_number: str
    sku: str
    product_name: str
    customer_email: str
    policy_reference: str
    reason: str
    detailed_explanation: str
    return_window_days: int
    days_since_delivery: Optional[int] = None
    permitted_resolutions: List[ResolutionOption] = Field(default_factory=list)
    active_return_number: Optional[str] = None
    requires_human_review: bool = False
    suggested_resolution: Optional[str] = None


ACTIVE_STATUSES = ["PENDING", "APPROVED", "PROCESSING"]


def get_category_window_and_policy(product_name: str, sku: str) -> Tuple[int, str]:
    """
    Determines category-specific return window and policy clause based on product attributes.
    """
    name_lower = product_name.lower()
    sku_lower = sku.lower()

    # Apparel / Shoes: 14 days
    if any(k in name_lower for k in ["shoe", "sneaker", "boot", "shirt", "pant", "jeans", "jacket", "dress", "t-shirt"]) or \
       any(k in sku_lower for k in ["shoe", "footwear", "apparel", "wear"]):
        return (14, "Section 2.1: Apparel & Footwear 14-Day Exchange Policy")

    # Beauty / Cosmetics: 2 days (transit damage only)
    if any(k in name_lower for k in ["cream", "serum", "perfume", "cosmetic", "lipstick", "lotion"]):
        return (2, "Section 4.1: Beauty & Hygiene Policy")

    # Custom / Engraved: 0 days
    if any(k in name_lower for k in ["custom", "engraved", "engrave", "personalized", "monogram"]):
        return (0, "Section 5.1: Custom & Final Sale Items")

    # Electronics / Standard: 7 days
    if any(k in name_lower for k in ["headphone", "earphone", "charger", "cable", "case", "speaker", "watch"]):
        return (7, "Section 3.1: Electronics & Audio Defect Policy")

    return (7, "Section 1.1: Standard 7-Day Return Policy")


def evaluate_eligibility(
    db: Session,
    order_number: str,
    customer_email: str,
    sku: str,
    issue_category: Optional[str] = None,  # SIZE_FIT, DAMAGED, DEFECTIVE, WRONG_ITEM, NOT_NEEDED
) -> EligibilityEvaluation:
    """
    Deterministically evaluates return/exchange eligibility and builds permitted resolution options.
    """
    clean_order_num = order_number.strip()
    clean_email = customer_email.strip().lower()
    clean_sku = sku.strip()

    # 1. Lookup order
    order = db.query(Order).filter(Order.order_number == clean_order_num).first()
    if not order:
        return EligibilityEvaluation(
            eligible=False,
            order_number=clean_order_num,
            sku=clean_sku,
            product_name="Unknown Item",
            customer_email=clean_email,
            policy_reference="Order Lookup",
            reason=f"Order '{order_number}' was not found in our database.",
            detailed_explanation="Please verify the order number on your invoice or purchase confirmation email.",
            return_window_days=7,
        )

    # 2. Check customer ownership
    if order.customer_email.strip().lower() != clean_email:
        return EligibilityEvaluation(
            eligible=False,
            order_number=clean_order_num,
            sku=clean_sku,
            product_name="Protected Item",
            customer_email=clean_email,
            policy_reference="Account Verification",
            reason="Customer email does not match the order ownership records.",
            detailed_explanation="For privacy and security, returns can only be requested by the verified ordering account.",
            return_window_days=7,
        )

    # 3. Locate SKU in order items
    matching_item: Optional[OrderItem] = None
    for item in order.items:
        if item.sku and item.sku.strip().lower() == clean_sku.lower():
            matching_item = item
            break

    if not matching_item:
        return EligibilityEvaluation(
            eligible=False,
            order_number=clean_order_num,
            sku=clean_sku,
            product_name="Unknown Item",
            customer_email=clean_email,
            policy_reference="Item Line Matching",
            reason=f"Item with SKU '{sku}' is not part of order '{order_number}'.",
            detailed_explanation="Please select one of the items actually ordered in this purchase.",
            return_window_days=7,
        )

    product_name = matching_item.product_name
    window_days, policy_ref = get_category_window_and_policy(product_name, matching_item.sku or "")

    # 4. Check delivery status & date
    if order.shipping_status.upper() != "DELIVERED" or not order.delivery_date:
        return EligibilityEvaluation(
            eligible=False,
            order_number=clean_order_num,
            sku=clean_sku,
            product_name=product_name,
            customer_email=clean_email,
            policy_reference="Section 1.1: Delivery Requirement",
            reason="Order has not been delivered yet or delivery date is missing.",
            detailed_explanation=f"Current shipping status is '{order.shipping_status}'. Returns can only be initiated after delivery.",
            return_window_days=window_days,
        )

    # 5. Check if item is marked returnable
    if not matching_item.is_returnable:
        # Check if exception applies for transit damage or wrong product
        if issue_category in ["DAMAGED", "DEFECTIVE", "WRONG_ITEM"]:
            # Route to human review with exception
            return EligibilityEvaluation(
                eligible=True,
                order_number=clean_order_num,
                sku=clean_sku,
                product_name=product_name,
                customer_email=clean_email,
                policy_reference=policy_ref,
                reason="Non-returnable item is conditionally eligible for replacement due to reported defect/damage.",
                detailed_explanation="Although this item is marked Final Sale, transit damage or manufacturer defect qualifies for replacement review.",
                return_window_days=window_days,
                requires_human_review=True,
                suggested_resolution="REPLACEMENT_DAMAGED",
                permitted_resolutions=[
                    ResolutionOption(
                        id="REPLACEMENT_DAMAGED",
                        title="Brand New Replacement (Damage Claim)",
                        description="Reported defect will be reviewed with photo evidence and replaced free of charge.",
                        timeline="24-48h review + Express dispatch",
                        pros=["Free replacement unit", "No return shipping fee"],
                        cons=["Requires photo evidence verification"],
                        is_recommended=True,
                        badge="Special Exception",
                    )
                ],
            )

        return EligibilityEvaluation(
            eligible=False,
            order_number=clean_order_num,
            sku=clean_sku,
            product_name=product_name,
            customer_email=clean_email,
            policy_reference=policy_ref,
            reason=f"'{product_name}' is classified as non-returnable / final sale.",
            detailed_explanation="Custom engraved, clearance, or personal hygiene products cannot be returned once purchased.",
            return_window_days=window_days,
        )

    # 6. Check delivery date window
    now = datetime.now(timezone.utc)
    delivery = order.delivery_date
    if delivery.tzinfo is None:
        delivery = delivery.replace(tzinfo=timezone.utc)

    delta = now - delivery
    days_elapsed = max(0, delta.days)

    if days_elapsed > window_days:
        return EligibilityEvaluation(
            eligible=False,
            order_number=clean_order_num,
            sku=clean_sku,
            product_name=product_name,
            customer_email=clean_email,
            policy_reference=policy_ref,
            reason=f"Return window of {window_days} days has expired.",
            detailed_explanation=(
                f"Delivered on {delivery.strftime('%b %d, %Y')} ({days_elapsed} days ago). "
                f"The applicable return window is {window_days} days."
            ),
            return_window_days=window_days,
            days_since_delivery=days_elapsed,
        )

    # 7. Check for existing active return requests
    existing_active = (
        db.query(ReturnRequest)
        .filter(
            ReturnRequest.order_item_id == matching_item.id,
            ReturnRequest.status.in_(ACTIVE_STATUSES),
        )
        .first()
    )
    if existing_active:
        return EligibilityEvaluation(
            eligible=False,
            order_number=clean_order_num,
            sku=clean_sku,
            product_name=product_name,
            customer_email=clean_email,
            policy_reference="Duplicate Prevention",
            reason=f"An active return request ({existing_active.return_number}) already exists for this item.",
            detailed_explanation=f"Current status: {existing_active.status}. You can monitor progress on the Return Tracking page.",
            return_window_days=window_days,
            days_since_delivery=days_elapsed,
            active_return_number=existing_active.return_number,
        )

    # 8. Success: construct permitted resolution options based on product type and issue
    resolutions: List[ResolutionOption] = []
    is_apparel = window_days == 14 or any(k in product_name.lower() for k in ["shoe", "pant", "shirt", "jeans"])
    is_electronics = any(k in product_name.lower() for k in ["headphone", "audio", "case", "charger", "device"])

    # Option A: Refund
    resolutions.append(
        ResolutionOption(
            id="RETURN_REFUND",
            title="Return for 100% Refund",
            description="Free courier doorstep pickup; refund to original payment source or instant store wallet.",
            timeline="Pickup in 24-48h; refund in 2-4 business days",
            pros=["Full monetary refund to source account", "Option for instant store wallet credit"],
            cons=["Must package item in original box with tags"],
            badge="Standard",
            is_recommended=(issue_category == "NOT_NEEDED" or not is_apparel),
        )
    )

    # Option B: Size / Color Exchange (if apparel / footwear)
    if is_apparel:
        resolutions.append(
            ResolutionOption(
                id="EXCHANGE_SIZE",
                title="Exchange Size or Color",
                description="Fast-track exchange for another size without additional shipping charges.",
                timeline="Replacement dispatched upon courier pickup",
                pros=["Zero added shipping fee", "Keep same promotional price", "Faster than reordering"],
                cons=["Subject to alternate size inventory availability"],
                badge="Best for Fit",
                is_recommended=(issue_category in ["SIZE_FIT", None]),
            )
        )

    # Option C: Defective Replacement (if damaged or defective)
    if is_electronics or issue_category in ["DAMAGED", "DEFECTIVE", "WRONG_ITEM"]:
        resolutions.append(
            ResolutionOption(
                id="REPLACEMENT_DAMAGED",
                title="Brand New Unit Replacement",
                description="Free reverse pickup of defective unit and expedited shipping of a sealed replacement.",
                timeline="Replacement dispatched within 24 hours of pickup",
                pros=["Guaranteed new factory unit", "Priority courier handling"],
                cons=["Subject to stock availability; refund issued if out of stock"],
                badge="Priority",
                is_recommended=(issue_category in ["DAMAGED", "DEFECTIVE", "WRONG_ITEM"]),
            )
        )

    # Option D: Product Troubleshooting (if electronics)
    if is_electronics:
        resolutions.append(
            ResolutionOption(
                id="PRODUCT_SUPPORT",
                title="Guided Troubleshooting & Setup",
                description="Instant troubleshooting steps and certified brand technician support.",
                timeline="Instant digital guide & same-day support call",
                pros=["Resolve issue without waiting for return shipment", "Preserve current device"],
                cons=["Only applies to software/pairing/configuration issues"],
                badge="Fastest",
                is_recommended=False,
            )
        )

    # Determine recommended resolution
    rec = next((r.id for r in resolutions if r.is_recommended), resolutions[0].id)

    return EligibilityEvaluation(
        eligible=True,
        order_number=clean_order_num,
        sku=clean_sku,
        product_name=product_name,
        customer_email=clean_email,
        policy_reference=policy_ref,
        reason=f"Item is eligible for return or exchange under {policy_ref}.",
        detailed_explanation=(
            f"Delivered on {delivery.strftime('%b %d, %Y')} ({days_elapsed} of {window_days} days used). "
            f"You may choose from {len(resolutions)} available resolution options."
        ),
        return_window_days=window_days,
        days_since_delivery=days_elapsed,
        permitted_resolutions=resolutions,
        suggested_resolution=rec,
    )
