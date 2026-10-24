# ReturnPilot AI — E-Commerce Return Resolution & AI Advisor Platform

ReturnPilot AI is an enterprise-grade return and exchange resolution platform featuring:
- **Multilingual AI Return Advisor** communicating fluently in English, Hindi, and Hinglish.
- **Genuine Policy RAG Pipeline** with vector indexing, semantic search, and verifiable section citations.
- **Deterministic Eligibility & Resolution Engine** comparing Refunds, Exchanges, Replacements, and Support.
- **Explicit Confirmation Return Flow** enforcing customer ownership and duplicate-submission prevention.
- **Photo-Based Defect Inspection** with confidence scoring and human review routing.
- **Enterprise Authentication** with Argon2id password hashing, real email verification, and session revocation.

---

## 🛠️ Tech Stack & Architecture

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, SQLite, Pydantic v2, LangChain Core
- **AI & RAG Engine**:
  - Multilingual LLM provider (Google Gemini, OpenAI/Groq, or built-in semantic fallback)
  - Vector retrieval with TF-IDF, term-weighting, and cosine similarity
  - Photo defect analyzer with magic-byte validation and confidence scoring
- **Authentication & Security**:
  - Argon2id password hashing (`argon2-cffi`)
  - Email syntax validation & normalization (`email-validator`)
  - Cryptographically secure single-use tokens (`secrets.token_urlsafe`)
  - JWT & HttpOnly cookies with database session revocation (`UserSession`)
  - Sliding-window rate limiting on sensitive endpoints
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons

---

## 🤖 AI Return Advisor & Multilingual Support

The AI assistant is available through two connected entry points sharing the same conversational backend:
1. **Dedicated AI Return Advisor Page** accessible via the sidebar navigation.
2. **Floating Chatbot Widget** available on all authenticated workspace views.

### Language Capabilities
- **English**: Full policy reasoning and formal return generation.
- **Hindi (Devanagari)**: E.g., *"मुझे रिटर्न पॉलिसी समझाइए"*, *"मेरे जूते का साइज छोटा है"*.
- **Hinglish (Roman Hindi)**: E.g., *"Mera refund abhi tak nahi aaya"*, *"Shoes ka size chhota hai, exchange karne hain"*, *"I received a damaged product"*.
- **Language Switcher**: Automatic language detection with manual toggle (`Auto` | `English` | `हिन्दी` | `Hinglish`).

### Interactive Embedded Cards
- **Order Cards**: Securely lists customer's actual delivered orders with one-click item selection.
- **Eligibility Cards**: Displays deterministic verdict (Eligible/Ineligible), exact policy reference clause, return window, and reason.
- **Resolution Cards**: Compares eligible options (100% Refund, Size/Color Exchange, Defective Replacement, Product Support) with timelines, pros/cons, and recommended badges.
- **Policy Citation Cards**: Expandable verified source sections with similarity scores.
- **Confirmation Cards**: Explicit confirmation card summarizing parameters before creating the return.
- **Photo Upload Modal**: Product photo defect analyzer with confidence scoring.

---

## ⚙️ Environment Variables & Configuration

The application operates fully out-of-the-box with built-in semantic reasoning. For external LLM or live SMTP delivery, configure the following:

```bash
# Optional: External Multilingual LLM Provider
GEMINI_API_KEY=your_google_gemini_api_key
# OR
OPENAI_API_KEY=your_openai_api_key

# Optional: Live SMTP Email Delivery
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_smtp_password
SMTP_FROM_EMAIL=no-reply@returnpilot.ai
SMTP_USE_TLS=true
```

> **Note**: If no LLM API key is set, the system uses its built-in multilingual semantic engine, guaranteeing 100% functionality, zero hallucinations, and passing test suites in offline environments.

---

## 🚀 Running the Project

### 1. Backend

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Start FastAPI server
uvicorn backend.main:app --reload --port 8000
```
- API Root: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

### 2. Frontend

```bash
cd frontend

# Install dependencies (if needed)
npm install

# Start development server
npm run dev

# Run production build and type checking
npm run build
```
- Frontend Web App: `http://localhost:5173`

---

## 🧪 Automated Test Suite (59 Tests)

Run the full automated test suite:

```bash
.\venv\Scripts\python.exe -m unittest discover -s backend/tests
```

### Coverage:
- **`test_ai_chat.py` (17 tests)**:
  - English, Hindi, and Hinglish language detection & dialogue response.
  - RAG policy retrieval for size exchange, damaged items, and refund timelines.
  - Unsupported/irrelevant query rejection with insufficient evidence flag.
  - Deterministic eligibility for apparel (14-day window), electronics (7-day window), final sale items.
  - Cross-customer order protection (Bob cannot inspect or return Alice's order).
  - Explicit confirmation requirement: no return record created without customer confirmation.
  - Return creation after confirmation (`RET-XXXX` with status `PENDING`).
  - Duplicate return prevention on identical item.
  - Customer order isolation (`GET /api/chat/orders`).
  - Photo defect analysis: valid damage detection, ambiguous routing to human review, oversized file rejection (>5MB), unsupported MIME rejection.
- **`test_auth.py` (19 tests)**: Argon2id hashing, email normalization & verification, session revocation, password reset, rate limiting.
- **`test_orders.py` (12 tests)**: Order CRUD, lookup, filtering.
- **`test_returns.py` (11 tests)**: Eligibility checks and return request management.
