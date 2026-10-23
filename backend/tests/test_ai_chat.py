"""
Automated Test Suite for AI-Powered Multilingual Returns & Exchange System.
Tests:
- English, Hindi, and Hinglish intent recognition and response formatting.
- Policy RAG retrieval, citations, and irrelevant query handling.
- Deterministic eligibility boundary conditions and resolution option generation.
- Real order retrieval with cross-customer authorization protection.
- Return creation with explicit confirmation vs rejection without confirmation.
- Duplicate return request prevention.
- Photo defect analysis validation and size limit enforcement.
"""

from datetime import datetime, timedelta, timezone
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_db
from backend.app.core.security import hash_password
from backend.app.models.order import Order, OrderItem
from backend.app.models.return_request import ReturnRequest
from backend.app.models.user import User, UserSession
from backend.app.services.ai.conversation import extract_order_number, detect_issue_type, orchestrator
from backend.app.services.ai.llm_provider import detect_language
from backend.app.services.eligibility.engine import evaluate_eligibility
from backend.app.services.rag.retriever import retriever
from backend.app.services.vision.photo_analyzer import photo_analyzer
from backend.app.core.rate_limit import limiter
from backend.app.services.ai.conversation import _sessions
from backend.main import app

# Isolated SQLite in-memory database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestAIChatSystem(unittest.TestCase):
    def setUp(self):
        limiter.clear()
        _sessions.clear()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
        self.client = TestClient(app)

        # Create primary test customer: Alice
        self.alice = User(
            full_name="Alice Sharma",
            email="alice@example.com",
            hashed_password=hash_password("AliceSecure123!"),
            is_active=True,
            is_verified=True,
        )
        self.db.add(self.alice)

        # Create secondary test customer: Bob (for cross-authorization tests)
        self.bob = User(
            full_name="Bob Verma",
            email="bob@example.com",
            hashed_password=hash_password("BobSecure123!"),
            is_active=True,
            is_verified=True,
        )
        self.db.add(self.bob)
        self.db.commit()

        # Seed delivered order for Alice with 3 items (Apparel, Electronics, and Final Sale)
        now = datetime.now(timezone.utc)
        self.order_alice = Order(
            order_number="ORD-ALICE-101",
            customer_name="Alice Sharma",
            customer_email="alice@example.com",
            order_date=now - timedelta(days=5),
            delivery_date=now - timedelta(days=3),  # Delivered 3 days ago (well within 7 & 14 days)
            shipping_status="DELIVERED",
            total_amount=249.99,
        )
        self.db.add(self.order_alice)
        self.db.commit()

        # Items for Alice
        self.item_shoes = OrderItem(
            order_id=self.order_alice.id,
            product_name="Pro Athletic Running Shoes",
            sku="SHOE-PRO-9",
            quantity=1,
            price=120.00,
            is_returnable=True,
        )
        self.item_headphones = OrderItem(
            order_id=self.order_alice.id,
            product_name="Wireless Noise Cancelling Headphones",
            sku="AUDIO-NC-01",
            quantity=1,
            price=99.99,
            is_returnable=True,
        )
        self.item_engraved = OrderItem(
            order_id=self.order_alice.id,
            product_name="Custom Engraved Metal Keychain",
            sku="ENGRAVE-KC-01",
            quantity=1,
            price=30.00,
            is_returnable=False,  # Final sale
        )
        self.db.add_all([self.item_shoes, self.item_headphones, self.item_engraved])

        # Seed an expired order for Alice (Delivered 20 days ago)
        self.order_expired = Order(
            order_number="ORD-ALICE-EXPIRED",
            customer_name="Alice Sharma",
            customer_email="alice@example.com",
            order_date=now - timedelta(days=25),
            delivery_date=now - timedelta(days=20),
            shipping_status="DELIVERED",
            total_amount=50.00,
        )
        self.db.add(self.order_expired)
        self.db.commit()

        self.item_expired = OrderItem(
            order_id=self.order_expired.id,
            product_name="Basic USB Cable",
            sku="CABLE-USB-01",
            quantity=1,
            price=50.00,
            is_returnable=True,
        )
        self.db.add(self.item_expired)
        self.db.commit()

        # Seed Bob's order
        self.order_bob = Order(
            order_number="ORD-BOB-999",
            customer_name="Bob Verma",
            customer_email="bob@example.com",
            order_date=now - timedelta(days=2),
            delivery_date=now - timedelta(days=1),
            shipping_status="DELIVERED",
            total_amount=150.00,
        )
        self.db.add(self.order_bob)
        self.db.commit()

        self.item_bob = OrderItem(
            order_id=self.order_bob.id,
            product_name="Smart Fitness Watch",
            sku="WATCH-FIT-02",
            quantity=1,
            price=150.00,
            is_returnable=True,
        )
        self.db.add(self.item_bob)
        self.db.commit()

        # Login Alice to obtain auth token
        login_resp = self.client.post(
            "/api/auth/login",
            json={"email": "alice@example.com", "password": "AliceSecure123!"},
        )
        self.alice_token = login_resp.json()["access_token"]
        self.alice_headers = {"Authorization": f"Bearer {self.alice_token}"}

        # Login Bob to obtain auth token
        login_bob = self.client.post(
            "/api/auth/login",
            json={"email": "bob@example.com", "password": "BobSecure123!"},
        )
        self.bob_token = login_bob.json()["access_token"]
        self.bob_headers = {"Authorization": f"Bearer {self.bob_token}"}
        # Clear client cookies so explicit Bearer headers govern each request
        self.client.cookies.clear()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    # 1. Multilingual Language Detection & Routing
    def test_01_language_detection(self):
        self.assertEqual(detect_language("I want to return my order"), "en")
        self.assertEqual(detect_language("Mera refund abhi tak nahi aaya"), "hinglish")
        self.assertEqual(detect_language("Yaar shoes ka size chhota hai, exchange karne hain"), "hinglish")
        self.assertEqual(detect_language("नमस्ते मुझे रिटर्न पॉलिसी समझाइए"), "hi")

    # 2. Policy RAG Retrieval & Citations
    def test_02_policy_rag_retrieval(self):
        # Query 1: Size exchange
        res_size = retriever.retrieve("shoes ka size chhota hai")
        self.assertTrue(res_size.is_relevant)
        self.assertFalse(res_size.insufficient_evidence)
        self.assertTrue(any("APP-02" == c.policy_id for c in res_size.citations))

        # Query 2: Damaged / Broken
        res_dam = retriever.retrieve("I received a damaged cracked product")
        self.assertTrue(res_dam.is_relevant)
        self.assertTrue(any(c.policy_id in ["ELE-03", "DAM-08"] for c in res_dam.citations))

        # Query 3: Refund timeline
        res_ref = retriever.retrieve("When will my refund money reach my bank account?")
        self.assertTrue(res_ref.is_relevant)
        self.assertTrue(any("REF-06" == c.policy_id for c in res_ref.citations))

    # 3. Unsupported / Irrelevant Query Handling
    def test_03_irrelevant_query_rejection(self):
        irrelevant = retriever.retrieve("How do I bake chocolate chip cookies?")
        self.assertFalse(irrelevant.is_relevant)
        self.assertTrue(irrelevant.insufficient_evidence)
        self.assertEqual(len(irrelevant.citations), 0)

    # 4. Deterministic Eligibility: Eligible Item with Resolution Options
    def test_04_deterministic_eligibility_eligible(self):
        eval_res = evaluate_eligibility(
            db=self.db,
            order_number="ORD-ALICE-101",
            customer_email="alice@example.com",
            sku="SHOE-PRO-9",
            issue_category="SIZE_FIT",
        )
        self.assertTrue(eval_res.eligible)
        self.assertEqual(eval_res.return_window_days, 14)  # Apparel gets 14 days
        self.assertGreater(len(eval_res.permitted_resolutions), 1)

        # Verify resolution options include EXCHANGE_SIZE and RETURN_REFUND
        res_ids = [r.id for r in eval_res.permitted_resolutions]
        self.assertIn("EXCHANGE_SIZE", res_ids)
        self.assertIn("RETURN_REFUND", res_ids)

    # 5. Deterministic Eligibility: Expired Return Window
    def test_05_deterministic_eligibility_expired_window(self):
        eval_res = evaluate_eligibility(
            db=self.db,
            order_number="ORD-ALICE-EXPIRED",
            customer_email="alice@example.com",
            sku="CABLE-USB-01",
        )
        self.assertFalse(eval_res.eligible)
        self.assertIn("expired", eval_res.reason.lower())
        self.assertEqual(len(eval_res.permitted_resolutions), 0)

    # 6. Deterministic Eligibility: Non-returnable Item
    def test_06_deterministic_eligibility_non_returnable(self):
        eval_res = evaluate_eligibility(
            db=self.db,
            order_number="ORD-ALICE-101",
            customer_email="alice@example.com",
            sku="ENGRAVE-KC-01",
            issue_category="NOT_NEEDED",
        )
        self.assertFalse(eval_res.eligible)
        self.assertIn("non-returnable", eval_res.reason.lower())

    # 7. Cross-Customer Order Protection (Bob cannot view or evaluate Alice's order)
    def test_07_cross_customer_authorization_protection(self):
        eval_res = evaluate_eligibility(
            db=self.db,
            order_number="ORD-ALICE-101",
            customer_email="bob@example.com",  # Bob's email attempting to access Alice's order
            sku="SHOE-PRO-9",
        )
        self.assertFalse(eval_res.eligible)
        self.assertIn("does not match", eval_res.reason)

    # 8. Chat Endpoint: Hinglish Message Processing
    def test_08_chat_endpoint_hinglish_response(self):
        resp = self.client.post(
            "/api/chat/message",
            headers=self.alice_headers,
            json={
                "message": "Yaar shoes ka size chhota hai ORD-ALICE-101 me",
                "session_id": "test-sess-1",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["role"], "assistant")
        self.assertIn(data["language"], ["hinglish", "en"])
        # Should have detected the order and attached eligibility
        self.assertIsNotNone(data.get("eligibility"))
        self.assertTrue(data["eligibility"]["eligible"])
        self.assertTrue(data["confirmation_required"])

    # 9. Return Action Submission Without Confirmation Is Not Created
    def test_09_no_return_created_until_explicit_confirmation(self):
        # Sending chat message asks for confirmation but does NOT create record in database
        initial_count = self.db.query(ReturnRequest).count()
        resp = self.client.post(
            "/api/chat/message",
            headers=self.alice_headers,
            json={
                "message": "Mujhe running shoes return karne hain ORD-ALICE-101",
                "session_id": "test-sess-2",
            },
        )
        self.assertEqual(resp.status_code, 200)
        current_count = self.db.query(ReturnRequest).count()
        self.assertEqual(initial_count, current_count, "Chat dialogue must not create return record without explicit confirmation")

    # 10. Explicit Confirmation Creates Persistent ReturnRequest
    def test_10_explicit_confirmation_creates_return(self):
        confirm_resp = self.client.post(
            "/api/chat/confirm-action",
            headers=self.alice_headers,
            json={
                "session_id": "test-sess-2",
                "order_number": "ORD-ALICE-101",
                "sku": "SHOE-PRO-9",
                "resolution": "EXCHANGE_SIZE",
                "return_reason": "Size 9 is slightly tight, requesting size 10 exchange",
            },
        )
        self.assertEqual(confirm_resp.status_code, 201)
        data = confirm_resp.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["return_number"].startswith("RET-"))
        self.assertEqual(data["status"], "PENDING")

        # Verify record exists in database
        created = self.db.query(ReturnRequest).filter(ReturnRequest.return_number == data["return_number"]).first()
        self.assertIsNotNone(created)
        self.assertEqual(created.customer_email, "alice@example.com")
        self.assertEqual(created.sku, "SHOE-PRO-9")

    # 11. Duplicate Return Prevention on Same Item
    def test_11_duplicate_return_prevention(self):
        # First confirmation succeeds
        first = self.client.post(
            "/api/chat/confirm-action",
            headers=self.alice_headers,
            json={
                "session_id": "sess-dup",
                "order_number": "ORD-ALICE-101",
                "sku": "AUDIO-NC-01",
                "resolution": "RETURN_REFUND",
                "return_reason": "Don't need headphones anymore",
            },
        )
        self.assertEqual(first.status_code, 201)

        # Second attempt on identical item must be rejected (400)
        second = self.client.post(
            "/api/chat/confirm-action",
            headers=self.alice_headers,
            json={
                "session_id": "sess-dup",
                "order_number": "ORD-ALICE-101",
                "sku": "AUDIO-NC-01",
                "resolution": "RETURN_REFUND",
                "return_reason": "Trying duplicate return",
            },
        )
        self.assertEqual(second.status_code, 400)
        self.assertIn("already exists", second.json()["detail"])

    # 12. Cross-Customer Confirmation Forbidden (Bob cannot confirm return on Alice's order)
    def test_12_cross_customer_confirmation_forbidden(self):
        resp = self.client.post(
            "/api/chat/confirm-action",
            headers=self.bob_headers,  # Bob attempts to submit return on Alice's order
            json={
                "session_id": "sess-hack",
                "order_number": "ORD-ALICE-101",
                "sku": "SHOE-PRO-9",
                "resolution": "RETURN_REFUND",
                "return_reason": "Unauthorized attempt",
            },
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("another user", resp.json()["detail"].lower())

    # 13. Customer Orders Retrieval Endpoint (Lists only user's orders)
    def test_13_get_customer_orders_isolated(self):
        resp = self.client.get("/api/chat/orders", headers=self.alice_headers)
        self.assertEqual(resp.status_code, 200)
        orders = resp.json()
        self.assertEqual(len(orders), 2)  # Alice has 2 orders
        order_numbers = [o["order_number"] for o in orders]
        self.assertIn("ORD-ALICE-101", order_numbers)
        self.assertIn("ORD-ALICE-EXPIRED", order_numbers)
        self.assertNotIn("ORD-BOB-999", order_numbers, "Alice must never see Bob's orders")

    # 14. Photo Analysis: Valid Image with Scratch/Crack Defect
    def test_14_photo_analysis_valid_damage(self):
        # Fake 1KB JPEG file with valid magic bytes
        fake_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 1024
        res = photo_analyzer.analyze_photo(
            file_bytes=fake_jpeg,
            file_name="headphone_crack.jpg",
            content_type="image/jpeg",
            user_notes="Visible crack on left ear cup",
        )
        self.assertTrue(res.is_valid_image)
        self.assertEqual(res.detected_issue, "PHYSICAL_SURFACE_DAMAGE")
        self.assertGreaterEqual(res.confidence_score, 0.70)
        self.assertFalse(res.requires_human_review)

    # 15. Photo Analysis: Ambiguous Defect Routes to Human Review
    def test_15_photo_analysis_ambiguous_routes_to_human(self):
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 1024
        res = photo_analyzer.analyze_photo(
            file_bytes=fake_png,
            file_name="unclear.png",
            content_type="image/png",
            user_notes="unclear image of item, needs inspection",
        )
        self.assertTrue(res.is_valid_image)
        self.assertTrue(res.requires_human_review)
        self.assertTrue(res.is_ambiguous)

    # 16. Photo Upload Endpoint: Rejects Oversized File
    def test_16_upload_oversized_file_rejected(self):
        oversized = b"\xff\xd8\xff\xe0" + b"\x00" * (6 * 1024 * 1024)  # 6 MB
        resp = self.client.post(
            "/api/chat/upload-photo",
            headers=self.alice_headers,
            files={"file": ("large.jpg", oversized, "image/jpeg")},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("exceeds", resp.json()["detail"].lower())

    # 17. Photo Upload Endpoint: Rejects Unsupported MIME Type
    def test_17_upload_unsupported_mime_rejected(self):
        fake_exe = b"MZ" + b"\x00" * 500
        resp = self.client.post(
            "/api/chat/upload-photo",
            headers=self.alice_headers,
            files={"file": ("malware.exe", fake_exe, "application/octet-stream")},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("unsupported", resp.json()["detail"].lower())


if __name__ == "__main__":
    unittest.main()
