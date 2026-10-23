"""
Comprehensive test suite for ReturnPilot AI Authentication, Email Verification,
Session Invalidation, and Password Recovery.
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
    from backend.app.core.rate_limit import limiter
    from backend.app.core.security import hash_token
    from backend.app.models.user import EmailVerificationToken, PasswordResetToken, User, UserSession
    from backend.app.services.email import dev_outbox
except ImportError:
    from main import app
    from app.core.database import Base, get_db
    from app.core.rate_limit import limiter
    from app.core.security import hash_token
    from app.models.user import EmailVerificationToken, PasswordResetToken, User, UserSession
    from app.services.email import dev_outbox

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


class AuthenticationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=test_engine)
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()

    def setUp(self):
        # Clear rate limiters and outbox between tests
        limiter.clear()
        dev_outbox.clear()

    # 1. Valid registration
    def test_01_valid_registration(self):
        payload = {
            "full_name": "Rajni Sharma",
            "email": "rajni.sharma@example.com",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        }
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["email"], "rajni.sharma@example.com")
        self.assertEqual(data["full_name"], "Rajni Sharma")
        self.assertFalse(data["is_verified"])
        self.assertNotIn("password", data)
        self.assertNotIn("hashed_password", data)

    # 2. Invalid email format
    def test_02_invalid_email_format(self):
        for bad_email in ["rajni", "rajni@", "@example.com", "rajni@example..com"]:
            payload = {
                "full_name": "Test User",
                "email": bad_email,
                "password": "SecurePassword123!",
                "confirm_password": "SecurePassword123!",
            }
            res = self.client.post("/api/auth/register", json=payload)
            self.assertEqual(res.status_code, 422)

    # 3. Missing required fields
    def test_03_missing_required_fields(self):
        incomplete_payload = {
            "email": "missing.name@example.com",
            "password": "SecurePassword123!",
        }
        res = self.client.post("/api/auth/register", json=incomplete_payload)
        self.assertEqual(res.status_code, 422)

    # 4. Weak password
    def test_04_weak_password_rejected(self):
        # Short password (< 8 chars)
        res_short = self.client.post("/api/auth/register", json={
            "full_name": "Short Pass",
            "email": "short@example.com",
            "password": "Aa1!",
            "confirm_password": "Aa1!",
        })
        self.assertEqual(res_short.status_code, 422)

        # Common password
        res_common = self.client.post("/api/auth/register", json={
            "full_name": "Common Pass",
            "email": "common@example.com",
            "password": "password123",
            "confirm_password": "password123",
        })
        self.assertEqual(res_common.status_code, 422)

        # Missing uppercase or special char
        res_no_special = self.client.post("/api/auth/register", json={
            "full_name": "No Special",
            "email": "nospecial@example.com",
            "password": "passwordwithoutspecial123",
            "confirm_password": "passwordwithoutspecial123",
        })
        self.assertEqual(res_no_special.status_code, 422)

    # 5. Password mismatch
    def test_05_password_mismatch_rejected(self):
        payload = {
            "full_name": "Mismatch User",
            "email": "mismatch@example.com",
            "password": "SecurePassword123!",
            "confirm_password": "DifferentPassword123!",
        }
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 422)

    # 6. Duplicate registration
    def test_06_duplicate_registration_rejected(self):
        payload = {
            "full_name": "Rajni Sharma Duplicate",
            "email": "rajni.sharma@example.com",  # Already registered in test_01
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        }
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("already exists", res.json()["detail"].lower())

    # 7. Email verification success
    def test_07_email_verification_success(self):
        # Register a fresh user
        email = "verify.me@example.com"
        reg_res = self.client.post("/api/auth/register", json={
            "full_name": "Verify Me",
            "email": email,
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        })
        self.assertEqual(reg_res.status_code, 201)
        token = reg_res.headers.get("X-Dev-Verification-Token")
        self.assertIsNotNone(token)

        # Verify email with token
        verify_res = self.client.post("/api/auth/verify-email", json={"token": token})
        self.assertEqual(verify_res.status_code, 200)
        self.assertTrue(verify_res.json()["success"])

        # Check DB user is_verified
        db = TestingSessionLocal()
        u = db.query(User).filter(User.email == email).first()
        self.assertIsNotNone(u)
        self.assertTrue(u.is_verified)
        db.close()

    # 8. Invalid, expired, and reused verification tokens
    def test_08_invalid_expired_reused_tokens(self):
        # Invalid token
        res_invalid = self.client.post("/api/auth/verify-email", json={"token": "totally-fake-token-xyz"})
        self.assertEqual(res_invalid.status_code, 400)
        self.assertIn("invalid", res_invalid.json()["detail"].lower())

        # Register fresh user for reuse and expiration testing
        email = "token.test@example.com"
        reg_res = self.client.post("/api/auth/register", json={
            "full_name": "Token Test",
            "email": email,
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        })
        token = reg_res.headers.get("X-Dev-Verification-Token")

        # First verification succeeds
        v1 = self.client.post("/api/auth/verify-email", json={"token": token})
        self.assertEqual(v1.status_code, 200)

        # Reused token is rejected
        v_reused = self.client.post("/api/auth/verify-email", json={"token": token})
        self.assertEqual(v_reused.status_code, 400)
        self.assertIn("already been used", v_reused.json()["detail"].lower())

        # Expired token test
        db = TestingSessionLocal()
        u = db.query(User).filter(User.email == email).first()
        expired_raw = "expired-token-123456"
        expired_rec = EmailVerificationToken(
            user_id=u.id,
            token_hash=hash_token(expired_raw),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            used=False,
        )
        db.add(expired_rec)
        db.commit()
        db.close()

        v_exp = self.client.post("/api/auth/verify-email", json={"token": expired_raw})
        self.assertEqual(v_exp.status_code, 400)
        self.assertIn("expired", v_exp.json()["detail"].lower())

    # 9. Login with correct credentials
    def test_09_login_correct_credentials(self):
        # Register and verify
        email = "login.success@example.com"
        reg = self.client.post("/api/auth/register", json={
            "full_name": "Login User",
            "email": email,
            "password": "CorrectPassword123!",
            "confirm_password": "CorrectPassword123!",
        })
        token = reg.headers.get("X-Dev-Verification-Token")
        self.client.post("/api/auth/verify-email", json={"token": token})

        # Login
        login_res = self.client.post("/api/auth/login", json={
            "email": email,
            "password": "CorrectPassword123!",
        })
        self.assertEqual(login_res.status_code, 200)
        data = login_res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], email)
        self.assertTrue(data["user"]["is_verified"])

        # Check HttpOnly cookie was set
        self.assertIn("access_token", login_res.cookies)

    # 10. Login with incorrect credentials
    def test_10_login_incorrect_credentials(self):
        email = "login.success@example.com"
        login_res = self.client.post("/api/auth/login", json={
            "email": email,
            "password": "WrongPassword999!",
        })
        self.assertEqual(login_res.status_code, 401)
        self.assertIn("invalid", login_res.json()["detail"].lower())

    # 11. Login with an unregistered account
    def test_11_login_unregistered_account(self):
        login_res = self.client.post("/api/auth/login", json={
            "email": "unregistered@example.com",
            "password": "RandomPassword123!",
        })
        self.assertEqual(login_res.status_code, 401)
        self.assertIn("invalid", login_res.json()["detail"].lower())

    # 12. Login before email verification
    def test_12_login_before_verification_rejected(self):
        email = "unverified.login@example.com"
        # Register but do NOT verify
        self.client.post("/api/auth/register", json={
            "full_name": "Unverified User",
            "email": email,
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        })

        login_res = self.client.post("/api/auth/login", json={
            "email": email,
            "password": "SecurePassword123!",
        })
        self.assertEqual(login_res.status_code, 403)
        self.assertIn("verify your email", login_res.json()["detail"].lower())

    # 13. Protected routes without authentication
    def test_13_protected_route_without_auth(self):
        client_no_auth = TestClient(app)
        res = client_no_auth.get("/api/auth/me")
        self.assertEqual(res.status_code, 401)

    # 14. Session restoration after refresh (GET /api/auth/me)
    def test_14_session_restoration_via_cookie_or_header(self):
        email = "session.restore@example.com"
        reg = self.client.post("/api/auth/register", json={
            "full_name": "Session Restore User",
            "email": email,
            "password": "RestorePassword123!",
            "confirm_password": "RestorePassword123!",
        })
        token = reg.headers.get("X-Dev-Verification-Token")
        self.client.post("/api/auth/verify-email", json={"token": token})

        # Login to receive cookie and token
        login_res = self.client.post("/api/auth/login", json={
            "email": email,
            "password": "RestorePassword123!",
        })
        access_token = login_res.json()["access_token"]

        # 14a. Restore via Authorization Header
        header_res = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        self.assertEqual(header_res.status_code, 200)
        self.assertEqual(header_res.json()["email"], email)

        # 14b. Restore via HttpOnly Cookie (fresh client simulating browser refresh)
        browser_client = TestClient(app)
        browser_client.cookies.set("access_token", access_token)
        cookie_res = browser_client.get("/api/auth/me")
        self.assertEqual(cookie_res.status_code, 200)
        self.assertEqual(cookie_res.json()["email"], email)

    # 15. Logout and subsequent protected route access
    def test_15_logout_and_subsequent_access(self):
        email = "logout.test@example.com"
        reg = self.client.post("/api/auth/register", json={
            "full_name": "Logout User",
            "email": email,
            "password": "LogoutPassword123!",
            "confirm_password": "LogoutPassword123!",
        })
        token = reg.headers.get("X-Dev-Verification-Token")
        self.client.post("/api/auth/verify-email", json={"token": token})

        login_res = self.client.post("/api/auth/login", json={
            "email": email,
            "password": "LogoutPassword123!",
        })
        access_token = login_res.json()["access_token"]

        # Call logout
        logout_res = self.client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(logout_res.status_code, 200)

        # Verify access token is now rejected because session was revoked in database
        after_logout = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(after_logout.status_code, 401)

    # 16. Backend/network failures and password recovery flow
    def test_16_password_reset_flow(self):
        email = "reset.user@example.com"
        reg = self.client.post("/api/auth/register", json={
            "full_name": "Reset User",
            "email": email,
            "password": "OldPassword123!",
            "confirm_password": "OldPassword123!",
        })
        token = reg.headers.get("X-Dev-Verification-Token")
        self.client.post("/api/auth/verify-email", json={"token": token})

        # Request forgot password
        forgot_res = self.client.post("/api/auth/forgot-password", json={"email": email})
        self.assertEqual(forgot_res.status_code, 200)
        reset_token = forgot_res.headers.get("X-Dev-Reset-Token")
        self.assertIsNotNone(reset_token)

        # Reset password with new password
        reset_res = self.client.post("/api/auth/reset-password", json={
            "token": reset_token,
            "new_password": "NewBrandPassword123!",
            "confirm_password": "NewBrandPassword123!",
        })
        self.assertEqual(reset_res.status_code, 200)

        # Old password fails
        login_old = self.client.post("/api/auth/login", json={
            "email": email,
            "password": "OldPassword123!",
        })
        self.assertEqual(login_old.status_code, 401)

        # New password succeeds
        login_new = self.client.post("/api/auth/login", json={
            "email": email,
            "password": "NewBrandPassword123!",
        })
        self.assertEqual(login_new.status_code, 200)

    # 17. Existing order and return functionality remains intact
    def test_17_existing_order_and_return_endpoints_intact(self):
        # Health check
        res_health = self.client.get("/health")
        self.assertEqual(res_health.status_code, 200)

        # Root check
        res_root = self.client.get("/")
        self.assertEqual(res_root.status_code, 200)

        # Orders list
        res_orders = self.client.get("/api/orders/")
        self.assertEqual(res_orders.status_code, 200)

        # Returns check endpoint
        res_returns_check = self.client.post("/returns/check", json={
            "order_number": "NON-EXISTENT",
            "customer_email": "test@example.com",
            "sku": "NON-EXISTENT-SKU",
        })
        self.assertEqual(res_returns_check.status_code, 200)
        self.assertFalse(res_returns_check.json()["eligible"])


if __name__ == "__main__":
    unittest.main()
