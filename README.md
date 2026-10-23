# ReturnPilot AI — E-Commerce Return Resolution & Authentication Suite

ReturnPilot AI is an automated return resolution platform with policy verification, automated eligibility evaluation, customer self-service return workflows, and an enterprise authentication and session management system.

---

## 🛠️ Tech Stack & Architecture

- **Backend**: FastAPI, Python 3.12, SQLAlchemy, SQLite, Pydantic v2
- **Security & Authentication**:
  - **Argon2id** password hashing (`argon2-cffi`)
  - **Email Validation & Normalization** (`email-validator`)
  - **Cryptographically Secure Tokens** (`secrets.token_urlsafe`)
  - **JWT & HttpOnly Session Cookies** with database-backed session revocation (`UserSession`)
  - **Sliding-Window Rate Limiting** on auth endpoints
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons

---

## 🔐 Authentication & Security Implementation

### 1. User Registration & Email Verification
- Strict email syntax validation rejecting formats like `rajni` or `rajni@`.
- Password policy enforcement:
  - Minimum 8 characters
  - At least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special symbol
  - Automatic rejection of common / vulnerable passwords
- Argon2id password hashing with distinct salts. Plaintext passwords and hashes are never exposed.
- Expiring, single-use, cryptographically secure 64-character verification tokens (valid 30 minutes).
- **Enforced Verification**: Unverified accounts are strictly prohibited from signing in (HTTP 403 `EMAIL_NOT_VERIFIED`).

### 2. Session Management & Revocation
- Dual-channel authentication: Secure `HttpOnly` cookie + `Authorization: Bearer <token>`.
- Cross-origin credentials enabled for local development.
- Each login records an active `UserSession` in the database.
- `/api/auth/logout` revokes the database session record and clears the cookie.
- Revoked sessions are immediately rejected on `/api/auth/me`.

### 3. Password Recovery Flow
- Generic responses on `/api/auth/forgot-password` to prevent account enumeration.
- Time-limited (15-minute), single-use reset tokens.
- On successful reset, all active user sessions across all devices are immediately revoked.

### 4. Sliding-Window Rate Limiting
- Prevents brute-force attacks and abuse on:
  - Registration (10/min per IP)
  - Sign in (15/min per IP)
  - Verification (20/min per IP)
  - Resend verification (60s cooldown per email, 5/hour max)
  - Password reset (10/15min per IP)

---

## 📧 Email Configuration (SMTP vs Development Outbox)

The system works out-of-the-box in development mode without requiring external credentials:

- If SMTP environment variables are **not set**, tokens are saved to an in-memory `dev_outbox` and returned via `X-Dev-Verification-Token` and `X-Dev-Reset-Token` HTTP headers. The frontend automatically surfaces a quick-fill assistant for development testing.
- For **production live email delivery**, configure standard SMTP environment variables:

```bash
# SMTP Configuration (.env or system environment)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_sendgrid_api_key
SMTP_FROM_EMAIL=no-reply@returnpilot.ai
SMTP_USE_TLS=true
```

---

## 🚀 Running the Project

### 1. Backend Setup & Startup

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Start FastAPI development server
uvicorn backend.main:app --reload --port 8000
```
- API Root: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup & Startup

```bash
cd frontend

# Install dependencies (if needed)
npm install

# Run dev server
npm run dev

# Run production build & type check
npm run build
```
- Frontend Web App: `http://localhost:5173`

---

## 🧪 Automated Test Suite

Run the full automated test suite (42 tests):

```bash
.\venv\Scripts\python.exe -m unittest discover -s backend/tests
```

### Test Coverage Summary:
- **`test_auth.py` (19 test cases)**:
  - Valid registration
  - Invalid email syntax rejection
  - Missing field rejection
  - Weak password rejection (<8 chars, missing character classes)
  - Password mismatch rejection
  - Common password rejection
  - Duplicate registration prevention
  - Unverified sign-in prevention (HTTP 403)
  - Verification with valid token
  - Bogus / invalid token rejection
  - Expired token rejection
  - Reused token rejection
  - Verified user sign-in & JWT/cookie issuance
  - Incorrect password rejection
  - Profile retrieval via `/me`
  - Unauthenticated rejection on `/me` (HTTP 401)
  - Logout session revocation
  - Full password reset lifecycle
  - Rate limiter enforcement
- **`test_orders.py` (11 test cases)**: Order creation, retrieval, lookup, validation.
- **`test_returns.py` (12 test cases)**: Return eligibility checking, 7-day delivery window validation, SKU verification, duplicate active request prevention.
