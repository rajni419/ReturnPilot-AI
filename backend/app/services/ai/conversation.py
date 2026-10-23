"""
Conversation Orchestrator for ReturnPilot AI Multilingual Assistant.
Coordinates dialogue state, multilingual intent, order retrieval, RAG policies, and return actions.
"""

from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...models.order import Order, OrderItem
from ...models.return_request import ReturnRequest
from ...models.user import User
from ..eligibility.engine import EligibilityEvaluation, evaluate_eligibility
from ..rag.retriever import PolicyCitation, retriever
from .llm_provider import detect_language, llm_provider


class ChatMessage(BaseModel):
    id: str
    role: str  # user | assistant | system
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    language: str = "en"
    citations: List[PolicyCitation] = Field(default_factory=list)
    eligibility: Optional[EligibilityEvaluation] = None
    orders: List[Dict[str, Any]] = Field(default_factory=list)
    selected_order_number: Optional[str] = None
    selected_sku: Optional[str] = None
    suggested_resolutions: List[Dict[str, Any]] = Field(default_factory=list)
    confirmation_required: bool = False
    confirmation_payload: Optional[Dict[str, Any]] = None
    action_result: Optional[Dict[str, Any]] = None


class ConversationSession(BaseModel):
    session_id: str
    user_email: str
    user_name: str
    preferred_language: str = "auto"
    active_order_number: Optional[str] = None
    active_sku: Optional[str] = None
    active_item_name: Optional[str] = None
    detected_issue: Optional[str] = None
    awaiting_confirmation: bool = False
    pending_action: Optional[Dict[str, Any]] = None
    messages: List[ChatMessage] = Field(default_factory=list)


# In-memory session store (keyed by session_id)
_sessions: Dict[str, ConversationSession] = {}


def get_or_create_session(session_id: str, user: User, preferred_language: str = "auto") -> ConversationSession:
    if session_id not in _sessions:
        _sessions[session_id] = ConversationSession(
            session_id=session_id,
            user_email=user.email,
            user_name=user.full_name,
            preferred_language=preferred_language,
        )
    sess = _sessions[session_id]
    if preferred_language != "auto":
        sess.preferred_language = preferred_language
    return sess


def extract_order_number(text: str) -> Optional[str]:
    """Matches patterns like ORD-1001, ORD-DEMO-1234, ORD1001."""
    m = re.search(r"\b(ORD[-\w\d]+)\b", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return None


def detect_issue_type(text: str) -> Optional[str]:
    """Classifies user reported issue category."""
    t = text.lower()
    if any(k in t for k in ["size", "chhota", "chota", "bada", "fit", "tight", "loose", "shoes"]):
        return "SIZE_FIT"
    if any(k in t for k in ["toota", "tuta", "damage", "damaged", "broken", "crack", "leak", "leaking"]):
        return "DAMAGED"
    if any(k in t for k in ["kharab", "defective", "working", "faulty", "dead", "doa"]):
        return "DEFECTIVE"
    if any(k in t for k in ["galat", "wrong", "different", "not what i ordered"]):
        return "WRONG_ITEM"
    if any(k in t for k in ["nahi chahiye", "dont want", "not needed", "disliked", "change of mind"]):
        return "NOT_NEEDED"
    return None


class ConversationOrchestrator:
    """Manages full dialogue lifecycle, intent routing, and state transitions."""

    def process_message(
        self,
        db: Session,
        session_id: str,
        user: User,
        user_message: str,
        preferred_language: str = "auto",
        direct_order_number: Optional[str] = None,
        direct_sku: Optional[str] = None,
    ) -> ChatMessage:
        sess = get_or_create_session(session_id, user, preferred_language)

        # 1. Determine active language
        if sess.preferred_language != "auto":
            active_lang = sess.preferred_language
        else:
            active_lang = detect_language(user_message)

        # 2. Extract potential entities from input
        detected_order = direct_order_number or extract_order_number(user_message)
        if detected_order:
            sess.active_order_number = detected_order

        detected_sku = direct_sku
        if detected_sku:
            sess.active_sku = detected_sku

        issue = detect_issue_type(user_message)
        if issue:
            sess.detected_issue = issue

        # 3. Check for order verification / listing intent
        user_orders = (
            db.query(Order)
            .filter(Order.customer_email.ilike(user.email.strip()))
            .order_by(Order.order_date.desc())
            .all()
        )

        serialized_orders = [
            {
                "order_number": o.order_number,
                "order_date": o.order_date.strftime("%Y-%m-%d") if o.order_date else "",
                "delivery_date": o.delivery_date.strftime("%Y-%m-%d") if o.delivery_date else None,
                "shipping_status": o.shipping_status,
                "total_amount": o.total_amount,
                "items": [
                    {
                        "product_name": item.product_name,
                        "sku": item.sku,
                        "quantity": item.quantity,
                        "price": item.price,
                        "is_returnable": item.is_returnable,
                    }
                    for item in o.items
                ],
            }
            for o in user_orders
        ]

        # 4. Check policy RAG
        rag_res = retriever.retrieve(user_message, top_k=2)

        # 5. Check return status inquiry intent
        if any(k in user_message.lower() for k in ["status", "track", "kahan pahuncha", "kahan hai", "paisa kab"]):
            existing_returns = (
                db.query(ReturnRequest)
                .filter(ReturnRequest.customer_email.ilike(user.email.strip()))
                .order_by(ReturnRequest.created_at.desc())
                .all()
            )
            if existing_returns:
                latest = existing_returns[0]
                if active_lang == "hi":
                    resp_text = (
                        f"आपके रिटर्न अनुरोध **{latest.return_number}** (ऑर्डर {latest.order_number}) की स्थिति "
                        f"वर्तमान में **'{latest.status}'** है।\n\n"
                        f"जैसे ही कोरियर पार्टनर पिकअप पूरा करेगा, आपको तुरंत अपडेट प्राप्त होगा।"
                    )
                elif active_lang == "hinglish":
                    resp_text = (
                        f"Aapke return request **{latest.return_number}** (Order {latest.order_number}) ka current status "
                        f"**'{latest.status}'** hai.\n\n"
                        f"Reverse pickup complete hote hi refund aapke account me initiate ho jayega."
                    )
                else:
                    resp_text = (
                        f"Your return request **{latest.return_number}** for order **{latest.order_number}** "
                        f"is currently **'{latest.status}'**.\n\n"
                        f"You can track detailed updates on the Return Tracking page."
                    )

                return ChatMessage(
                    id=f"msg-{len(sess.messages)+1}",
                    role="assistant",
                    content=resp_text,
                    language=active_lang,
                    citations=rag_res.citations,
                )

        # 6. If an order and SKU are active or resolved, run deterministic eligibility
        active_order = sess.active_order_number
        active_sku = sess.active_sku

        # If user picked order but no SKU specified, check if order has exactly 1 item OR match keywords
        if active_order and not active_sku:
            matched_ord = next((o for o in user_orders if o.order_number == active_order), None)
            if matched_ord:
                if len(matched_ord.items) == 1:
                    active_sku = matched_ord.items[0].sku
                    sess.active_sku = active_sku
                else:
                    # Check if user message mentions any product name keywords (e.g. "shoes", "headphones")
                    msg_words = set(re.findall(r"\b\w+\b", user_message.lower()))
                    for itm in matched_ord.items:
                        prod_words = set(re.findall(r"\b\w+\b", itm.product_name.lower()))
                        if prod_words.intersection(msg_words):
                            active_sku = itm.sku
                            sess.active_sku = active_sku
                            break

        # If both active_order and active_sku are ready, run evaluation!
        if active_order and active_sku:
            eval_res = evaluate_eligibility(
                db=db,
                order_number=active_order,
                customer_email=user.email,
                sku=active_sku,
                issue_category=sess.detected_issue,
            )

            sess.active_item_name = eval_res.product_name

            # Generate natural language response via LLM provider
            context = {
                "eligibility": eval_res.model_dump(),
                "citations": [c.model_dump() for c in rag_res.citations],
                "language": active_lang,
            }
            ai_text = llm_provider.generate(
                prompt=user_message,
                system_prompt="You are ReturnPilot AI, an intelligent return resolution assistant.",
                language=active_lang,
                context=context,
            )

            # Build confirmation payload if eligible
            confirmation_needed = eval_res.eligible
            confirm_payload = None
            if confirmation_needed:
                suggested_res = eval_res.suggested_resolution or "RETURN_REFUND"
                confirm_payload = {
                    "order_number": active_order,
                    "customer_email": user.email,
                    "sku": active_sku,
                    "product_name": eval_res.product_name,
                    "resolution": suggested_res,
                    "return_reason": user_message[:300],
                }
                sess.pending_action = confirm_payload
                sess.awaiting_confirmation = True

            return ChatMessage(
                id=f"msg-{len(sess.messages)+1}",
                role="assistant",
                content=ai_text,
                language=active_lang,
                citations=rag_res.citations,
                eligibility=eval_res,
                suggested_resolutions=[r.model_dump() for r in eval_res.permitted_resolutions],
                confirmation_required=confirmation_needed,
                confirmation_payload=confirm_payload,
                selected_order_number=active_order,
                selected_sku=active_sku,
            )

        # 7. If user mentioned return/exchange but has not selected an order, offer their orders
        wants_return = any(
            k in user_message.lower()
            for k in ["return", "exchange", "refund", "wapas", "badalna", "chhota", "size", "toota", "damaged", "wrong"]
        )

        if wants_return:
            if not user_orders:
                if active_lang == "hi":
                    resp_text = (
                        "आपके खाते में अभी कोई डिलीवर किया गया ऑर्डर नहीं मिला। "
                        "रिटर्न शुरू करने के लिए कृपया अपना ऑर्डर नंबर बताएं।"
                    )
                elif active_lang == "hinglish":
                    resp_text = (
                        "Aapke account me abhi koi delivered order nahi mila. "
                        "Return check karne ke liye please apna Order Number batayein."
                    )
                else:
                    resp_text = (
                        "I couldn't find any delivered orders associated with your account. "
                        "Please provide your order number (e.g., ORD-1001) so I can verify its eligibility."
                    )

                return ChatMessage(
                    id=f"msg-{len(sess.messages)+1}",
                    role="assistant",
                    content=resp_text,
                    language=active_lang,
                    citations=rag_res.citations,
                )

            # Orders are available: present orders for in-chat selection
            if active_lang == "hi":
                resp_text = (
                    "ज़रूर! कृपया नीचे दिए गए अपने ऑर्डर्स में से वह ऑर्डर चुनें जिसे आप रिटर्न या एक्सचेंज करना चाहते हैं:"
                )
            elif active_lang == "hinglish":
                resp_text = (
                    "Bilkul! Neeche diye gaye apne orders me se select karein jise aap return ya exchange karna chahte hain:"
                )
            else:
                resp_text = (
                    "Certainly! Here are your recent orders. Please select the order and item you would like to return or exchange:"
                )

            return ChatMessage(
                id=f"msg-{len(sess.messages)+1}",
                role="assistant",
                content=resp_text,
                language=active_lang,
                citations=rag_res.citations,
                orders=serialized_orders,
            )

        # 8. Policy inquiry or general inquiry fallback
        ai_text = llm_provider.generate(
            prompt=user_message,
            system_prompt="You are ReturnPilot AI, an intelligent e-commerce returns assistant.",
            language=active_lang,
            context={"citations": [c.model_dump() for c in rag_res.citations]},
        )

        return ChatMessage(
            id=f"msg-{len(sess.messages)+1}",
            role="assistant",
            content=ai_text,
            language=active_lang,
            citations=rag_res.citations,
        )


# Global orchestrator instance
orchestrator = ConversationOrchestrator()
