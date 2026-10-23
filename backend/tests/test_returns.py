"""
Automated test suite for Return Eligibility API and Return Request Management.
"""

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Add project root and backend directory to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent
for p in [str(BASE_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.main import app
    from backend.app.core.database import Base, get_db
    from backend.app.models.order import Order, OrderItem
    from backend.app.models.return_request import ReturnRequest
except ImportError:
    from main import app
    from app.core.database import Base, get_db
    from app.models.order import Order, OrderItem
    from app.models.return_request import ReturnRequest

# Set up isolated in-memory SQLite database
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class ReturnManagementTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=test_engine)
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

        # Seed test data
        db = TestingSessionLocal()
        now = datetime.now(timezone.utc)

        # 1. Order delivered 2 days ago (eligible window)
        order_delivered = Order(
            order_number="ORD-RET-ELIGIBLE",
            customer_name="Alice Smith",
            customer_email="alice@example.com",
            order_date=now - timedelta(days=5),
            delivery_date=now - timedelta(days=2),
            shipping_status="DELIVERED",
            total_amount=170.0,
        )
        order_delivered.items.append(
            OrderItem(
                product_name="Returnable Running Shoes",
                sku="SHOE-RET-01",
                quantity=1,
                price=100.0,
                is_returnable=True,
            )
        )
        order_delivered.items.append(
            OrderItem(
                product_name="Second Returnable Shirt",
                sku="SHIRT-RET-03",
                quantity=1,
                price=50.0,
                is_returnable=True,
            )
        )
        order_delivered.items.append(
            OrderItem(
                product_name="Final Sale Socks",
                sku="SOCK-NONRET-02",
                quantity=2,
                price=10.0,
                is_returnable=False,
            )
        )

        # 2. Order delivered 10 days ago (expired window > 7 days)
        order_expired = Order(
            order_number="ORD-RET-EXPIRED",
            customer_name="Bob Jones",
            customer_email="bob@example.com",
            order_date=now - timedelta(days=15),
            delivery_date=now - timedelta(days=10),
            shipping_status="DELIVERED",
            total_amount=50.0,
        )
        order_expired.items.append(
            OrderItem(
                product_name="Winter Jacket",
                sku="JACKET-EXP-01",
                quantity=1,
                price=50.0,
                is_returnable=True,
            )
        )

        # 3. Order without delivery date
        order_undelivered = Order(
            order_number="ORD-RET-PENDING",
            customer_name="Charlie Brown",
            customer_email="charlie@example.com",
            order_date=now - timedelta(days=1),
            delivery_date=None,
            shipping_status="SHIPPED",
            total_amount=30.0,
        )
        order_undelivered.items.append(
            OrderItem(
                product_name="Baseball Cap",
                sku="CAP-PEND-01",
                quantity=1,
                price=30.0,
                is_returnable=True,
            )
        )

        db.add_all([order_delivered, order_expired, order_undelivered])
        db.commit()
        db.close()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()

    # ------------------------------------------------------------------------
    # Return Eligibility Tests (POST /returns/check)
    # ------------------------------------------------------------------------

    def test_01_eligible_item_check(self):
        """Test item within 7-day delivery window and marked returnable is eligible."""
        payload = {
            "order_number": "ORD-RET-ELIGIBLE",
            "customer_email": "alice@example.com",
            "sku": "SHOE-RET-01",
        }
        response = self.client.post("/returns/check", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["eligible"])
        self.assertEqual(data["order_number"], "ORD-RET-ELIGIBLE")
        self.assertEqual(data["sku"], "SHOE-RET-01")
        self.assertIn("eligible", data["reason"].lower())

    def test_02_wrong_customer_email_check(self):
        """Test rejection when customer_email does not match order records."""
        payload = {
            "order_number": "ORD-RET-ELIGIBLE",
            "customer_email": "wrong_email@example.com",
            "sku": "SHOE-RET-01",
        }
        response = self.client.post("/returns/check", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["eligible"])
        self.assertEqual(data["order_number"], "ORD-RET-ELIGIBLE")
        self.assertEqual(data["sku"], "SHOE-RET-01")
        self.assertIn("customer email", data["reason"].lower())

    def test_03_missing_order_check(self):
        """Test rejection when order number does not exist."""
        payload = {
            "order_number": "ORD-NON-EXISTENT",
            "customer_email": "alice@example.com",
            "sku": "SHOE-RET-01",
        }
        response = self.client.post("/returns/check", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["eligible"])
        self.assertEqual(data["order_number"], "ORD-NON-EXISTENT")
        self.assertEqual(data["sku"], "SHOE-RET-01")
        self.assertIn("not found", data["reason"].lower())

    def test_04_non_returnable_item_check(self):
        """Test rejection when item is marked is_returnable=False."""
        payload = {
            "order_number": "ORD-RET-ELIGIBLE",
            "customer_email": "alice@example.com",
            "sku": "SOCK-NONRET-02",
        }
        response = self.client.post("/returns/check", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["eligible"])
        self.assertEqual(data["order_number"], "ORD-RET-ELIGIBLE")
        self.assertEqual(data["sku"], "SOCK-NONRET-02")
        self.assertIn("not marked as returnable", data["reason"].lower())

    def test_05_expired_return_window_check(self):
        """Test rejection when delivery date was more than 7 days ago."""
        payload = {
            "order_number": "ORD-RET-EXPIRED",
            "customer_email": "bob@example.com",
            "sku": "JACKET-EXP-01",
        }
        response = self.client.post("/returns/check", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["eligible"])
        self.assertEqual(data["order_number"], "ORD-RET-EXPIRED")
        self.assertEqual(data["sku"], "JACKET-EXP-01")
        self.assertIn("expired", data["reason"].lower())

    def test_06_missing_delivery_date_check(self):
        """Test rejection when delivery date is missing / order not delivered."""
        payload = {
            "order_number": "ORD-RET-PENDING",
            "customer_email": "charlie@example.com",
            "sku": "CAP-PEND-01",
        }
        response = self.client.post("/returns/check", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["eligible"])
        self.assertEqual(data["order_number"], "ORD-RET-PENDING")
        self.assertEqual(data["sku"], "CAP-PEND-01")
        self.assertIn("delivery date is missing", data["reason"].lower())

    def test_07_sku_not_in_order_check(self):
        """Test rejection when SKU is not found in the specified order."""
        payload = {
            "order_number": "ORD-RET-ELIGIBLE",
            "customer_email": "alice@example.com",
            "sku": "UNKNOWN-SKU-999",
        }
        response = self.client.post("/returns/check", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["eligible"])
        self.assertEqual(data["order_number"], "ORD-RET-ELIGIBLE")
        self.assertEqual(data["sku"], "UNKNOWN-SKU-999")
        self.assertIn("not found in order", data["reason"].lower())

    # ------------------------------------------------------------------------
    # Return Request Management Tests (POST /returns, GET /returns)
    # ------------------------------------------------------------------------

    def test_08_create_return_request_success(self):
        """Verify successful creation of a return request with PENDING status and RET-xxxx format."""
        payload = {
            "order_number": "ORD-RET-ELIGIBLE",
            "customer_email": "alice@example.com",
            "sku": "SHOE-RET-01",
            "return_reason": "Size is too large, need exchange",
        }
        response = self.client.post("/returns", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()

        self.assertRegex(data["return_number"], r"^RET-\d{4}$")
        self.assertEqual(data["status"], "PENDING")
        self.assertEqual(data["order_number"], "ORD-RET-ELIGIBLE")
        self.assertEqual(data["sku"], "SHOE-RET-01")
        self.assertEqual(data["return_reason"], "Size is too large, need exchange")
        self.assertTrue("id" in data)
        self.assertTrue("created_at" in data)

    def test_09_create_return_request_duplicate_active_rejected(self):
        """Verify that duplicate active return request for the same order item is rejected."""
        payload = {
            "order_number": "ORD-RET-ELIGIBLE",
            "customer_email": "alice@example.com",
            "sku": "SHOE-RET-01",
            "return_reason": "Second attempt to create return for same item",
        }
        response = self.client.post("/returns", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("active return request", data["detail"].lower())

    def test_10_create_return_request_ineligible_item_rejected(self):
        """Verify rejection when creating return for an item marked non-returnable."""
        payload = {
            "order_number": "ORD-RET-ELIGIBLE",
            "customer_email": "alice@example.com",
            "sku": "SOCK-NONRET-02",
            "return_reason": "Not satisfied with color",
        }
        response = self.client.post("/returns", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("not marked as returnable", data["detail"].lower())

    def test_11_create_return_request_wrong_email_rejected(self):
        """Verify rejection when customer email does not match order."""
        payload = {
            "order_number": "ORD-RET-ELIGIBLE",
            "customer_email": "wrong_customer@example.com",
            "sku": "SHIRT-RET-03",
            "return_reason": "Item arrived damaged",
        }
        response = self.client.post("/returns", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("customer email", data["detail"].lower())

    def test_12_create_return_request_missing_order_rejected(self):
        """Verify rejection when order does not exist."""
        payload = {
            "order_number": "ORD-NOT-FOUND-999",
            "customer_email": "alice@example.com",
            "sku": "SHIRT-RET-03",
            "return_reason": "Defective product",
        }
        response = self.client.post("/returns", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("not found", data["detail"].lower())

    def test_13_create_return_request_expired_window_rejected(self):
        """Verify rejection when return window is expired (> 7 days)."""
        payload = {
            "order_number": "ORD-RET-EXPIRED",
            "customer_email": "bob@example.com",
            "sku": "JACKET-EXP-01",
            "return_reason": "Too warm for spring",
        }
        response = self.client.post("/returns", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("expired", data["detail"].lower())

    def test_14_list_return_requests(self):
        """Verify GET /returns retrieves the list of return requests with filters."""
        # Also create a second return request for SHIRT-RET-03
        payload = {
            "order_number": "ORD-RET-ELIGIBLE",
            "customer_email": "alice@example.com",
            "sku": "SHIRT-RET-03",
            "return_reason": "Wrong size received",
        }
        res_create = self.client.post("/returns", json=payload)
        self.assertEqual(res_create.status_code, 201)

        # List all
        response = self.client.get("/returns")
        self.assertEqual(response.status_code, 200)
        returns = response.json()
        self.assertGreaterEqual(len(returns), 2)

        # Filter by order_number
        filter_res = self.client.get("/returns?order_number=ORD-RET-ELIGIBLE")
        self.assertEqual(filter_res.status_code, 200)
        self.assertGreaterEqual(len(filter_res.json()), 2)

        # Filter by non-existent order_number
        none_res = self.client.get("/returns?order_number=ORD-NONE")
        self.assertEqual(none_res.status_code, 200)
        self.assertEqual(len(none_res.json()), 0)

    def test_15_get_return_request_by_id(self):
        """Verify GET /returns/{return_id} retrieves a single request."""
        list_res = self.client.get("/returns")
        first_return = list_res.json()[0]
        return_id = first_return["id"]

        response = self.client.get(f"/returns/{return_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], return_id)
        self.assertEqual(response.json()["return_number"], first_return["return_number"])

        # Non-existent ID returns 404
        res_404 = self.client.get("/returns/999999")
        self.assertEqual(res_404.status_code, 404)

    def test_16_api_prefix_returns(self):
        """Verify /api/returns prefix works identically."""
        res = self.client.get("/api/returns")
        self.assertEqual(res.status_code, 200)


def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(ReturnManagementTestCase)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
