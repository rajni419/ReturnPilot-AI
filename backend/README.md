# ReturnPilot AI - Backend

AI-Powered E-Commerce Return & Resolution System backend built with **FastAPI**, **SQLite**, and **SQLAlchemy**.

## Tech Stack
- **Python 3.12+**
- **FastAPI**: Modern, high-performance web framework for building APIs.
- **Uvicorn**: Lightning-fast ASGI server.
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping (ORM) library.
- **SQLite**: Lightweight database.

---

## Getting Started

### 1. Set Up the Virtual Environment

From the project root (`ReturnPilot-AI`):

```bash
# Using Python 3.12:
py -3.12 -m venv venv

# Activate virtual environment (Windows PowerShell):
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Run the Development Server

Navigate into the `backend` directory or run from the project root:

```bash
# From the project root:
uvicorn backend.main:app --reload --port 8000

# Or navigate to backend folder:
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Endpoints & Interactive Docs

- **Root API**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) - Returns `{"message": "ReturnPilot AI Backend Running"}`
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) - Returns `{"status": "healthy"}`
- **Orders API**:
  - `POST /api/orders/`: Create new order with line items
  - `GET /api/orders/`: List all orders (supports pagination, `customer_email`, `shipping_status` filters)
  - `GET /api/orders/{order_id}`: Retrieve order by ID
  - `GET /api/orders/lookup/{order_number}`: Lookup order by order number (e.g. `ORD-1001`)
  - `PATCH /api/orders/{order_id}`: Update order status or customer details
  - `DELETE /api/orders/{order_id}`: Delete an order and its line items
- **Returns API**:
  - `POST /returns/check` (also `/api/returns/check`): Check item return eligibility (order existence, email match, SKU verification, `is_returnable`, and 7-day delivery window).
  - `POST /returns` (also `/api/returns`): Create a new return request with status `PENDING` and unique ID (e.g. `RET-0001`); rejects duplicate active requests.
  - `GET /returns` (also `/api/returns`): List return requests (supports pagination and filtering by `order_number`, `customer_email`, `status`).
  - `GET /returns/{return_id}` (also `/api/returns/{return_id}`): Retrieve single return request details by ID.
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)


### 5. Running Tests

```bash
# Run all tests:
.\venv\Scripts\python.exe -m unittest discover -s backend/tests

# Or run individual test suites:
.\venv\Scripts\python.exe backend/tests/test_orders.py
.\venv\Scripts\python.exe backend/tests/test_returns.py
```


