"""
Integration and unit tests for ReturnPilot AI Orders API and SQLite Database.
"""

import sys
import unittest
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
except ImportError:
    from main import app
    from app.core.database import Base, get_db


# Set up isolated in-memory SQLite database for tests
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


class OrdersApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=test_engine)
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()

    def test_01_root_and_health(self):
        """Verify root and health endpoints remain functional."""
        res_root = self.client.get("/")
        self.assertEqual(res_root.status_code, 200)
        self.assertEqual(res_root.json(), {"message": "ReturnPilot AI Backend Running"})

        res_health = self.client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json(), {"status": "healthy"})

    def test_02_create_order_with_items(self):
        """Verify creating an order with line items."""
        order_payload = {
            "order_number": "ORD-1001",
            "customer_name": "Jane Doe",
            "customer_email": "jane@example.com",
            "shipping_status": "DELIVERED",
            "items": [
                {
                    "product_name": "Wireless Noise-Cancelling Headphones",
                    "sku": "HEADPHONE-001",
                    "quantity": 1,
                    "price": 149.99,
                    "is_returnable": True,
                },
                {
                    "product_name": "USB-C Fast Charging Cable",
                    "sku": "CABLE-002",
                    "quantity": 2,
                    "price": 12.50,
                    "is_returnable": True,
                },
            ],
        }

        response = self.client.post("/api/orders/", json=order_payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()

        self.assertEqual(data["order_number"], "ORD-1001")
        self.assertEqual(data["customer_name"], "Jane Doe")
        self.assertEqual(data["customer_email"], "jane@example.com")
        self.assertEqual(data["shipping_status"], "DELIVERED")
        self.assertEqual(data["total_amount"], 174.99)
        self.assertEqual(len(data["items"]), 2)
        self.assertTrue("id" in data)
        self.assertTrue("id" in data["items"][0])

    def test_03_create_duplicate_order_rejected(self):
        """Verify duplicate order_number returns 400."""
        duplicate_payload = {
            "order_number": "ORD-1001",
            "customer_name": "Duplicate User",
            "customer_email": "dup@example.com",
            "items": [],
        }
        response = self.client.post("/api/orders/", json=duplicate_payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("already exists", response.json()["detail"])

    def test_04_list_orders(self):
        """Verify listing orders and query filtering."""
        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, 200)
        orders = response.json()
        self.assertGreaterEqual(len(orders), 1)

        # Filter by email
        filter_res = self.client.get("/api/orders/?customer_email=jane@example.com")
        self.assertEqual(filter_res.status_code, 200)
        self.assertEqual(len(filter_res.json()), 1)

        # Filter non-matching
        none_res = self.client.get("/api/orders/?customer_email=nobody@nowhere.com")
        self.assertEqual(none_res.status_code, 200)
        self.assertEqual(len(none_res.json()), 0)

    def test_05_lookup_order_by_number(self):
        """Verify customer lookup by order number."""
        response = self.client.get("/api/orders/lookup/ORD-1001")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["order_number"], "ORD-1001")

        # Non-existent
        res_404 = self.client.get("/api/orders/lookup/ORD-NONEXISTENT")
        self.assertEqual(res_404.status_code, 404)

    def test_06_get_order_by_id(self):
        """Verify getting order by ID."""
        list_res = self.client.get("/api/orders/")
        order_id = list_res.json()[0]["id"]

        response = self.client.get(f"/api/orders/{order_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], order_id)

        # Non-existent ID
        res_404 = self.client.get("/api/orders/999999")
        self.assertEqual(res_404.status_code, 404)

    def test_07_update_order(self):
        """Verify updating order shipping status."""
        list_res = self.client.get("/api/orders/")
        order_id = list_res.json()[0]["id"]

        patch_payload = {"shipping_status": "RETURN_REQUESTED"}
        response = self.client.patch(f"/api/orders/{order_id}", json=patch_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["shipping_status"], "RETURN_REQUESTED")

    def test_08_delete_order(self):
        """Verify deleting an order cascades and removes items."""
        # Create a disposable order
        payload = {
            "order_number": "ORD-DISPOSABLE",
            "customer_name": "Temporary",
            "customer_email": "temp@example.com",
            "items": [{"product_name": "Temp Item", "price": 10.0, "quantity": 1}],
        }
        create_res = self.client.post("/api/orders/", json=payload)
        self.assertEqual(create_res.status_code, 201)
        temp_id = create_res.json()["id"]

        del_res = self.client.delete(f"/api/orders/{temp_id}")
        self.assertEqual(del_res.status_code, 204)

        # Verify not found
        get_res = self.client.get(f"/api/orders/{temp_id}")
        self.assertEqual(get_res.status_code, 404)

    def test_09_direct_orders_alias(self):
        """Verify routes are accessible via /orders alias as well."""
        res = self.client.get("/orders/")
        self.assertEqual(res.status_code, 200)


def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(OrdersApiTestCase)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
