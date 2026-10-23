"""
Policy Knowledge Base for ReturnPilot AI RAG Pipeline.
Stores structured e-commerce policies for returns, exchanges, refunds, and replacements.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PolicySection(BaseModel):
    policy_id: str
    category: str
    section: str
    title: str
    content: str
    keywords: List[str]
    allowed_actions: List[str]
    return_window_days: Optional[int] = None
    conditions: List[str] = Field(default_factory=list)


DEFAULT_POLICIES: List[PolicySection] = [
    PolicySection(
        policy_id="GEN-01",
        category="General",
        section="Section 1.1: General Return Policy & Standard Window",
        title="Standard 7-Day Return Policy",
        content=(
            "Customers may return eligible items within 7 calendar days of delivery. "
            "Items must be in original condition with manufacturer packaging, manuals, "
            "warranty cards, and accessories intact. Proof of purchase (order number) is required. "
            "Upon receipt and inspection at our fulfillment center, approved refunds are initiated within 48 hours."
        ),
        keywords=["return", "general", "policy", "days", "window", "7 days", "refund", "standard", "packaging"],
        allowed_actions=["RETURN_REFUND", "REPLACEMENT"],
        return_window_days=7,
        conditions=[
            "Item must be initiated within 7 calendar days from delivery",
            "Original product packaging and barcodes must be intact",
            "Item must not show signs of physical wear or misuse",
        ],
    ),
    PolicySection(
        policy_id="APP-02",
        category="Apparel & Footwear",
        section="Section 2.1: Clothing, Shoes & Fashion Exchange Policy",
        title="Apparel Size & Color Exchange Policy (14-Day Window)",
        content=(
            "Clothing, footwear, and fashion accessories enjoy an extended 14-day return and exchange window. "
            "Customers may exchange for an alternate size or color at zero additional shipping cost. "
            "To qualify for exchange or refund, garments must be unworn, unwashed, and have all original tags attached. "
            "Footwear must be tried indoors on carpeted floors and returned in its undamaged original branded shoe box."
        ),
        keywords=["apparel", "clothing", "shoes", "size", "fit", "exchange", "footwear", "shirt", "jeans", "chhota", "bada"],
        allowed_actions=["EXCHANGE_SIZE", "RETURN_REFUND"],
        return_window_days=14,
        conditions=[
            "14-day window from confirmed delivery date",
            "Original tags and labels must be physically attached",
            "Unworn, unwashed, and free of odors or stains",
            "Footwear must include undamaged original shoe box",
        ],
    ),
    PolicySection(
        policy_id="ELE-03",
        category="Electronics",
        section="Section 3.1: Electronics, Audio & Gadgets Policy",
        title="Electronics Replacement & Defect Policy",
        content=(
            "Consumer electronics, headphones, smart devices, and chargers are eligible for free 7-day replacement "
            "if delivered damaged, defective, or dead-on-arrival (DOA). "
            "Serial numbers and IMEI codes must match order records. "
            "If an identical replacement unit is unavailable in inventory, a full refund will be processed. "
            "Beyond 7 days, products are covered under manufacturer warranty service."
        ),
        keywords=["electronics", "headphones", "gadgets", "defective", "audio", "charger", "broken", "dead", "kharab", "repair"],
        allowed_actions=["REPLACEMENT_DAMAGED", "PRODUCT_SUPPORT", "RETURN_REFUND"],
        return_window_days=7,
        conditions=[
            "7 calendar days from delivery for replacement",
            "Must report dead-on-arrival or functional failure",
            "Includes all cables, power adapters, and manuals",
            "Device must be factory reset with personal data removed",
        ],
    ),
    PolicySection(
        policy_id="BEA-04",
        category="Beauty & Personal Care",
        section="Section 4.1: Cosmetics, Fragrances & Hygiene Policy",
        title="Hygiene Exclusions & Damaged Delivery Policy",
        content=(
            "Due to health, safety, and hygiene regulations, beauty products, perfumes, grooming essentials, "
            "and personal care items are strictly non-returnable once opened or delivered with broken seals. "
            "However, if the product arrives damaged, leaking, expired, or different from what was ordered, "
            "customers are entitled to a full replacement or refund upon submitting photo proof within 48 hours."
        ),
        keywords=["beauty", "cosmetics", "perfume", "skincare", "hygiene", "opened", "non-returnable", "leaking", "expired"],
        allowed_actions=["REPLACEMENT_DAMAGED", "RETURN_REFUND"],
        return_window_days=2,
        conditions=[
            "Strictly non-returnable if opened or seal broken",
            "Report transit damage or leaks within 48 hours of delivery",
            "Photo evidence required for verification",
        ],
    ),
    PolicySection(
        policy_id="CUS-05",
        category="Custom & Final Sale",
        section="Section 5.1: Personalized & Final Sale Items",
        title="Custom Engraved & Clearance Policy",
        content=(
            "Personalized, custom-engraved, monogrammed, and clearance items clearly marked 'Final Sale' "
            "cannot be returned or exchanged. Exceptions are granted only if ReturnPilot AI or the retailer "
            "made an error in the custom inscription, or if the product sustained structural transit damage."
        ),
        keywords=["custom", "engraved", "personalized", "final sale", "clearance", "non-refundable"],
        allowed_actions=["REPLACEMENT_DAMAGED"],
        return_window_days=0,
        conditions=[
            "Final sale products are non-refundable and non-exchangeable",
            "Retailer engraving error or severe transit breakage only",
        ],
    ),
    PolicySection(
        policy_id="REF-06",
        category="Refunds",
        section="Section 6.1: Refund Processing & Timelines",
        title="Refund Methods and Processing Windows",
        content=(
            "Once a returned item is received and inspected at our fulfillment center (usually within 24 hours of pickup): "
            "1. Instant Store Credit: Credited to your account wallet immediately upon courier pickup confirmation. "
            "2. UPI / NetBanking / Debit Card: 2 to 4 business days depending on banking partner. "
            "3. Credit Card: 3 to 5 business days reflecting on credit billing cycle. "
            "Cash on Delivery (COD) orders are refunded via direct bank transfer (NEFT/UPI) upon providing bank details."
        ),
        keywords=["refund", "money", "timeline", "bank", "credit", "wallet", "paisa", "kitne din", "account"],
        allowed_actions=["RETURN_REFUND"],
        return_window_days=None,
        conditions=[
            "Inspection must confirm item condition matches return claim",
            "Original shipping fees are refundable if return is due to merchant error",
        ],
    ),
    PolicySection(
        policy_id="LOG-07",
        category="Logistics & Pickup",
        section="Section 7.1: Courier Doorstep Pickup Guidelines",
        title="Free Doorstep Courier Pickup",
        content=(
            "We provide 100% free courier doorstep pickup for all approved return and exchange requests. "
            "A verified pickup agent arrives at the customer address within 24 to 48 business hours. "
            "The courier conducts a brief physical inspection (checking tags, box, and serial number) "
            "and hands over an official return tracking receipt. Customers do not need to print any return labels."
        ),
        keywords=["pickup", "courier", "delivery boy", "doorstep", "address", "shipping", "receipt", "kahan aayega"],
        allowed_actions=["RETURN_REFUND", "EXCHANGE_SIZE", "REPLACEMENT_DAMAGED"],
        return_window_days=None,
        conditions=[
            "Customer must be available at shipping address during pickup hours",
            "Courier verifies SKU and condition against return authorization",
        ],
    ),
    PolicySection(
        policy_id="DAM-08",
        category="Defects & Damage",
        section="Section 8.1: Damaged, Defective or Wrong Item Delivered",
        title="Transit Damage & Incorrect Item Resolution",
        content=(
            "If you receive a package that is damaged, tampered with, defective, or contains a different item from "
            "what you purchased, please notify us immediately within 48 hours. "
            "You can upload a clear photograph of the defect or shipping label via the ReturnPilot AI assistant. "
            "We provide an expedited priority replacement or immediate 100% refund with doorstep reverse pickup."
        ),
        keywords=["damaged", "broken", "wrong", "different", "toota", "galat", "defective", "tampered", "photo"],
        allowed_actions=["REPLACEMENT_DAMAGED", "RETURN_REFUND"],
        return_window_days=2,
        conditions=[
            "Notify within 48 hours of delivery",
            "Upload photo proof of physical damage or wrong item received",
            "Retain external shipping box and invoice",
        ],
    ),
]


class PolicyStore:
    """Manages policy repository and indexing."""

    def __init__(self, policies: Optional[List[PolicySection]] = None):
        self._policies: Dict[str, PolicySection] = {}
        for p in (policies or DEFAULT_POLICIES):
            self._policies[p.policy_id] = p

    def get_all(self) -> List[PolicySection]:
        return list(self._policies.values())

    def get_by_id(self, policy_id: str) -> Optional[PolicySection]:
        return self._policies.get(policy_id)

    def add_or_update(self, section: PolicySection) -> None:
        self._policies[section.policy_id] = section

    def search_by_category(self, category: str) -> List[PolicySection]:
        cat_lower = category.lower()
        return [p for p in self._policies.values() if cat_lower in p.category.lower()]


# Global policy store instance
policy_store = PolicyStore()
