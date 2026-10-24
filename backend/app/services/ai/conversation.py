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


def mask_email(email: str) -> str:
    """Masks customer email for security and privacy (e.g. s***h@example.com)."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


def is_policy_query(text: str) -> bool:
    """Detects general inquiries about return, refund, or exchange rules."""
    t = text.lower()
    policy_tokens = [
        "policy", "policies", "niyam", "shartein", "rule", "rules",
        "guideline", "guidelines", "condition", "conditions", "terms", "window"
    ]
    if any(tok in t for tok in policy_tokens):
        return True

    phrases = [
        "what is your return", "what is the return", "how do returns work",
        "return policy kya", "kya policy", "policy kya hai", "policy kya h",
        "return ke niyam", "retun policy", "kya return ho sakta", "kitne din me return",
        "how many days to return", "what can i return", "return window",
        "can i return", "can i exchange", "रिटर्न पॉलिसी", "नियम", "शर्तें"
    ]
    return any(p in t for p in phrases)


def is_refund_inquiry(text: str) -> bool:
    """Detects inquiries about refund status, delayed refunds, or payment timeline."""
    t = text.lower()
    refund_words = ["refund", "paisa", "paise", "money", "payment", "reimbursement", "रिफंड", "पैसे"]
    status_words = [
        "nahi aaya", "nahi mila", "ab tak nahi", "abhi tak", "kab aayega", "kab milega",
        "kya karun", "kya karein", "delayed", "not received", "haven't received", "where is",
        "timeline", "kitne din", "how long", "status", "track", "कहाँ है", "नहीं आया"
    ]
    has_refund = any(rw in t for rw in refund_words)
    has_status = any(sw in t for sw in status_words)
    if has_refund and (has_status or len(t.split()) <= 4):
        return True

    if any(k in t for k in ["kahan pahuncha", "kahan hai", "paisa kab", "track my return", "return status", "refund status"]):
        return True

    return False


def is_greeting(text: str) -> bool:
    """Detects conversational greetings without transactional intent."""
    t = text.lower().strip()
    greetings = [
        "hi", "hello", "hey", "hola", "namaste", "namaskar",
        "good morning", "good afternoon", "good evening", "kem cho", "kaise ho", "hlo", "hii"
    ]
    tokens = re.findall(r"\b\w+\b", t)
    return any(tok in greetings for tok in tokens) and len(tokens) <= 4


def find_matching_item(user_message: str, items: List[OrderItem]) -> Optional[OrderItem]:
    """Finds matching order item by SKU or product keywords."""
    msg_words = set(re.findall(r"\b\w+\b", user_message.lower()))
    for itm in items:
        if itm.sku and itm.sku.lower() in user_message.lower():
            return itm
        prod_words = set(re.findall(r"\b\w+\b", itm.product_name.lower()))
        prod_keywords = {w for w in prod_words if len(w) > 3 and w not in {"with", "from", "item"}}
        if prod_keywords.intersection(msg_words):
            return itm
    return None


def serialize_order(o: Order) -> Dict[str, Any]:
    """Serializes Order object for JSON transfer to frontend."""
    return {
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

        # 3. Retrieve policies for context
        rag_res = retriever.retrieve(user_message, top_k=2)

        # 4. Check for Greeting
        if is_greeting(user_message) and not detected_order and not detected_sku:
            if active_lang == "hi":
                resp_text = (
                    f"नमस्ते {user.full_name or ''}! मैं ReturnPilot AI सहायक हूँ। "
                    f"मैं आपके ऑर्डर्स की जांच करने, रिटर्न/एक्सचेंज पात्रता सत्यापित करने, स्टोर नीतियां समझाने "
                    f"या रिफंड स्थिति ट्रैक करने में सहायता कर सकता हूँ। आज मैं आपकी क्या सहायता करूँ?"
                )
            elif active_lang == "hinglish":
                resp_text = (
                    f"Namaste {user.full_name or ''}! Main ReturnPilot AI assistant hoon. "
                    f"Main aapke orders check karne, return/exchange eligibility verify karne, store policies explain karne, "
                    f"ya refund track karne me madad kar sakta hoon. Main aaj aapki kya help karoon?"
                )
            else:
                resp_text = (
                    f"Hello {user.full_name or 'there'}! I am your ReturnPilot AI assistant. "
                    f"I can help you verify return/exchange eligibility, explain store policies, "
                    f"resolve sizing issues, or track refunds. How can I assist you today?"
                )
            return ChatMessage(
                id=f"msg-{len(sess.messages)+1}",
                role="assistant",
                content=resp_text,
                language=active_lang,
            )

        # 5. Check for Policy Inquiry (User asking what is the return/exchange/refund policy)
        if is_policy_query(user_message) and not detected_order and not detected_sku:
            ai_text = llm_provider.generate(
                prompt=user_message,
                system_prompt="You are ReturnPilot AI, an intelligent return resolution assistant. Explain verified store policies clearly.",
                language=active_lang,
                context={"citations": [c.model_dump() for c in rag_res.citations]},
            )
            return ChatMessage(
                id=f"msg-{len(sess.messages)+1}",
                role="assistant",
                content=ai_text,
                language=active_lang,
                citations=rag_res.citations,
                orders=[],  # Crucial: do NOT present orders when user simply asks about policy
            )

        # 6. Check for Refund / Delay / Status Inquiry
        if is_refund_inquiry(user_message) and not detected_order and not detected_sku:
            existing_returns = (
                db.query(ReturnRequest)
                .filter(ReturnRequest.customer_email.ilike(user.email.strip()))
                .order_by(ReturnRequest.created_at.desc())
                .all()
            )
            # Ensure REF-06 is cited for refund queries
            ref06 = next((c for c in rag_res.citations if c.policy_id == "REF-06"), None)
            citations = list(rag_res.citations)
            if not ref06:
                from ..rag.policy_store import policy_store
                p_ref = policy_store.get("REF-06")
                if p_ref:
                    citations = [
                        PolicyCitation(
                            policy_id=p_ref.policy_id,
                            section=p_ref.section,
                            title=p_ref.title,
                            category=p_ref.category,
                            snippet=p_ref.content[:220] + "...",
                            similarity_score=0.95,
                            allowed_actions=p_ref.allowed_actions,
                        )
                    ] + citations

            if existing_returns:
                latest = existing_returns[0]
                if active_lang == "hi":
                    resp_text = (
                        f"आपके रिटर्न अनुरोध **{latest.return_number}** (ऑर्डर {latest.order_number}) की स्थिति वर्तमान में **'{latest.status}'** है।\n\n"
                        f"📋 **ReturnPilot रिफंड पॉलिसी (REF-06)**:\n"
                        f"• **स्टोर क्रेडिट**: पिकअप की पुष्टि होने पर तुरंत वॉलेट में जमा।\n"
                        f"• **UPI / नेटबैंकिंग**: रिवर्स पिकअप निरीक्षण के बाद 2 से 4 कार्य दिवस।\n"
                        f"• **क्रेडिट कार्ड**: 3 से 5 कार्य दिवस में बैंक खाते में।\n\n"
                        f"आप 'Return Tracking' पेज पर भी लाइव अपडेट देख सकते हैं।"
                    )
                elif active_lang == "hinglish":
                    resp_text = (
                        f"Aapke return request **{latest.return_number}** (Order {latest.order_number}) ka current status **'{latest.status}'** hai.\n\n"
                        f"📋 **ReturnPilot Refund Policy (REF-06)**:\n"
                        f"• **Store Credit**: Courier pickup confirm hote hi turant wallet me add hota hai.\n"
                        f"• **UPI / NetBanking**: Reverse pickup aur inspection ke baad 2 se 4 business days.\n"
                        f"• **Credit Card**: 3 se 5 business days me bank account me reflect hota hai.\n\n"
                        f"Aap Return Tracking tab me live updates bhi track kar sakte hain."
                    )
                else:
                    resp_text = (
                        f"Your return request **{latest.return_number}** for order **{latest.order_number}** is currently **'{latest.status}'**.\n\n"
                        f"📋 **ReturnPilot Refund Timelines (REF-06)**:\n"
                        f"• **Store Credit**: Instant upon doorstep courier pickup confirmation.\n"
                        f"• **UPI / NetBanking / Debit**: 2 to 4 business days after inspection.\n"
                        f"• **Credit Card**: 3 to 5 business days depending on banking cycle.\n\n"
                        f"You can monitor live progress on the Return Tracking page."
                    )
            else:
                if active_lang == "hi":
                    resp_text = (
                        f"यदि आपको अभी तक रिफंड नहीं मिला है, तो कृपया ध्यान दें कि रिफंड आइटम पिकअप और निरीक्षण के बाद प्रोसेस किया जाता है।\n\n"
                        f"📋 **ReturnPilot रिफंड पॉलिसी (REF-06)**:\n"
                        f"• **स्टोर क्रेडिट**: पिकअप पुष्टिकरण पर तुरंत।\n"
                        f"• **UPI / नेटबैंकिंग**: 2 से 4 कार्य दिवस।\n"
                        f"• **क्रेडिट कार्ड**: 3 से 5 कार्य दिवस।\n\n"
                        f"💡 **क्या करें?**\n"
                        f"आपके खाते में अभी कोई सक्रिय रिटर्न अनुरोध नहीं मिला। यदि आपने पहले ही आइटम वापस कर दिया है या नया रिटर्न दर्ज करना चाहते हैं, तो कृपया अपना **ऑर्डर नंबर** (जैसे ORD-DEMO-4827) साझा करें ताकि मैं स्थिति जांच सकूं।"
                    )
                elif active_lang == "hinglish":
                    resp_text = (
                        f"Agar aapka refund abhi tak nahi aaya hai, toh kripya dhyan dein ki refund item courier dwara pickup aur fulfillment center par inspect hone ke baad initiate hota hai.\n\n"
                        f"📋 **ReturnPilot Refund Policy (REF-06)**:\n"
                        f"• **Instant Store Credit**: Pickup confirm hote hi wallet me turant credit.\n"
                        f"• **UPI / NetBanking**: Pickup inspection ke baad 2 se 4 business days.\n"
                        f"• **Credit Card**: 3 se 5 business days me bank me credit.\n\n"
                        f"💡 **Aap kya kar sakte hain (Kya karun?)**:\n"
                        f"Aapke account par abhi koi active return request nahi mili. Agar aapne already item handover kar diya hai ya return raise karna chahte hain, kripya apna **Order Number** (jaise ORD-DEMO-4827) share karein taaki main status verify kar sakun."
                    )
                else:
                    resp_text = (
                        f"If you haven't received your refund yet, please note that refunds are initiated after the item is picked up and inspected at our fulfillment center.\n\n"
                        f"📋 **ReturnPilot Refund Policy (REF-06)**:\n"
                        f"• **Instant Store Credit**: Immediately upon courier pickup confirmation.\n"
                        f"• **UPI / NetBanking / Debit**: 2 to 4 business days post-inspection.\n"
                        f"• **Credit Card**: 3 to 5 business days reflecting on statement.\n\n"
                        f"💡 **Next Steps**:\n"
                        f"I could not locate an active return request for your account. If you have already handed over the item or wish to start a return, please provide your **Order Number** (e.g., ORD-DEMO-4827) so I can assist you directly."
                    )

            return ChatMessage(
                id=f"msg-{len(sess.messages)+1}",
                role="assistant",
                content=resp_text,
                language=active_lang,
                citations=citations,
                orders=[],
            )

        # 7. Check for Order Lookup / Action with detected order number
        if detected_order:
            db_order = db.query(Order).filter(Order.order_number.ilike(detected_order.strip())).first()

            # Case 7A: Order not found in database
            if not db_order:
                if active_lang == "hi":
                    resp_text = f"ऑर्डर **{detected_order}** हमारे रिकॉर्ड में नहीं मिला। कृपया अपना ऑर्डर नंबर पुनः जांचें।"
                elif active_lang == "hinglish":
                    resp_text = f"Order **{detected_order}** hamare database me nahi mila. Please sahi order number check karke dobara enter karein."
                else:
                    resp_text = f"Order **{detected_order}** was not found in our database. Please double-check your order number."
                return ChatMessage(
                    id=f"msg-{len(sess.messages)+1}",
                    role="assistant",
                    content=resp_text,
                    language=active_lang,
                    citations=rag_res.citations,
                    orders=[],
                )

            # Case 7B: Cross-Customer Authorization Check
            if db_order.customer_email.strip().lower() != user.email.strip().lower():
                masked = mask_email(db_order.customer_email)
                if active_lang == "hi":
                    resp_text = (
                        f"ऑर्डर **{db_order.order_number}** किसी अन्य ग्राहक खाते ({masked}) से संबंधित है। "
                        f"सुरक्षा और गोपनीयता कारणों से आप केवल अपने पंजीकृत ईमेल ({user.email}) के ऑर्डर देख सकते हैं।"
                    )
                elif active_lang == "hinglish":
                    resp_text = (
                        f"Order **{db_order.order_number}** kisi dusre customer account ({masked}) se registered hai. "
                        f"Security aur privacy protection ki wajah se, aap sirf apne registered account ({user.email}) ke orders check ya return kar sakte hain."
                    )
                else:
                    resp_text = (
                        f"Order **{db_order.order_number}** belongs to another customer account ({masked}). "
                        f"For security and privacy reasons, you can only access orders registered to your email ({user.email})."
                    )
                return ChatMessage(
                    id=f"msg-{len(sess.messages)+1}",
                    role="assistant",
                    content=resp_text,
                    language=active_lang,
                    citations=rag_res.citations,
                    orders=[],
                )

            # Case 7C: Authorized Order - Locate SKU or present items
            sess.active_order_number = db_order.order_number
            serialized_ord = serialize_order(db_order)

            # Check if SKU was specified or can be inferred
            matched_item: Optional[OrderItem] = None
            if detected_sku:
                matched_item = next((it for it in db_order.items if it.sku and it.sku.lower() == detected_sku.lower()), None)
            elif len(db_order.items) == 1 and (
                sess.detected_issue or any(k in user_message.lower() for k in ["return", "exchange", "refund", "size", "kharab", "defective", "damage", "broken"])
            ):
                matched_item = db_order.items[0]
            else:
                matched_item = find_matching_item(user_message, db_order.items)

            # If an item is matched AND user wants return/check on that item:
            if matched_item:
                sess.active_sku = matched_item.sku
                eval_res = evaluate_eligibility(
                    db=db,
                    order_number=db_order.order_number,
                    customer_email=user.email,
                    sku=matched_item.sku,
                    issue_category=sess.detected_issue,
                )
                sess.active_item_name = eval_res.product_name

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

                confirmation_needed = eval_res.eligible
                confirm_payload = None
                if confirmation_needed:
                    suggested_res = eval_res.suggested_resolution or "RETURN_REFUND"
                    confirm_payload = {
                        "order_number": db_order.order_number,
                        "customer_email": user.email,
                        "sku": matched_item.sku,
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
                    orders=[serialized_ord],
                    suggested_resolutions=[r.model_dump() for r in eval_res.permitted_resolutions],
                    confirmation_required=confirmation_needed,
                    confirmation_payload=confirm_payload,
                    selected_order_number=db_order.order_number,
                    selected_sku=matched_item.sku,
                )

            # No specific item resolved yet: present order details & items
            deliv_str = db_order.delivery_date.strftime("%d %b %Y") if db_order.delivery_date else "Recently"
            if active_lang == "hi":
                resp_text = (
                    f"मैंने आपका ऑर्डर **{db_order.order_number}** प्राप्त कर लिया है। "
                    f"यह {deliv_str} को डिलीवर हुआ था और इसमें {len(db_order.items)} आइटम शामिल हैं।\n\n"
                    f"आप किस आइटम के लिए रिटर्न या एक्सचेंज जांचना चाहते हैं? कृपया नीचे दिए गए आइटम पर क्लिक करें:"
                )
            elif active_lang == "hinglish":
                resp_text = (
                    f"Maine aapka order **{db_order.order_number}** check kar liya hai. "
                    f"Yeh {deliv_str} ko deliver hua tha aur isme {len(db_order.items)} item(s) hain.\n\n"
                    f"Aap kis item ke liye return ya exchange check karna chahte hain? Please neeche diye gaye item par click karein:"
                )
            else:
                resp_text = (
                    f"I located your order **{db_order.order_number}**. "
                    f"It was delivered on {deliv_str} and contains {len(db_order.items)} item(s).\n\n"
                    f"Please select the item below that you would like to return, exchange, or inspect:"
                )

            return ChatMessage(
                id=f"msg-{len(sess.messages)+1}",
                role="assistant",
                content=resp_text,
                language=active_lang,
                citations=rag_res.citations,
                orders=[serialized_ord],
                selected_order_number=db_order.order_number,
            )

        # 8. User wants return/exchange in general without order number specified
        wants_return = any(
            k in user_message.lower()
            for k in ["return", "exchange", "wapas", "badalna", "chhota", "size", "toota", "damaged", "wrong", "defective", "kharab"]
        )

        user_orders = (
            db.query(Order)
            .filter(Order.customer_email.ilike(user.email.strip()))
            .order_by(Order.order_date.desc())
            .all()
        )
        serialized_orders = [serialize_order(o) for o in user_orders]

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
                    orders=[],
                )

            # Orders are available: present orders for in-chat selection
            if active_lang == "hi":
                resp_text = "ज़रूर! कृपया नीचे दिए गए अपने ऑर्डर्स में से वह ऑर्डर चुनें जिसे आप रिटर्न या एक्सचेंज करना चाहते हैं:"
            elif active_lang == "hinglish":
                resp_text = "Bilkul! Neeche diye gaye apne orders me se select karein jise aap return ya exchange karna chahte hain:"
            else:
                resp_text = "Certainly! Here are your recent orders. Please select the order and item you would like to return or exchange:"

            return ChatMessage(
                id=f"msg-{len(sess.messages)+1}",
                role="assistant",
                content=resp_text,
                language=active_lang,
                citations=rag_res.citations,
                orders=serialized_orders,
            )

        # 9. General Policy / Dialogue fallback via LLM Provider
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
            orders=[],
        )


# Global orchestrator instance
orchestrator = ConversationOrchestrator()
