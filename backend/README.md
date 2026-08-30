# AI Merchant Commerce Platform — Backend API (Phase 1)

Production-grade FastAPI backend service powering merchant catalog management, inventory safety validations, and order processing.

---

## 🛠 Tech Stack

* **Language**: Python 3.12+
* **Framework**: FastAPI
* **Validation**: Pydantic v2 & Pydantic Settings
* **ORM / Database**: SQLAlchemy 2.0 with SQLite (WAL mode, Foreign Keys explicitly enabled via `PRAGMA foreign_keys=ON;`)
* **Testing**: Pytest & HTTPX TestClient

---

## 🚀 Setup & Installation

### 1. Create and Activate Virtual Environment

```bash
cd backend
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Default configuration in `.env`:
```ini
DATABASE_URL=sqlite:///./merchant_commerce.db
APP_ENV=development
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
API_V1_STR=/api/v1
PROJECT_NAME="AI Merchant Commerce Platform"
```

---

## 📦 Database Seeding

Populate the database with demo merchant **Chennai Sports Store**, 5 catalog products, 5 customers, and 8 historical orders:

```bash
python seed.py
```

---

## 🧪 Running Automated Tests

Run the complete test suite (23 unit & integration tests):

```bash
pytest -v
```

Tests cover:
* Service Health endpoint
* Merchant CRUD & duplicate email constraint enforcement
* Product CRUD, keyword search, category & status filtering
* Customer creation & listing
* Order creation with server-side pricing calculations
* Inventory stock validation & insufficient stock rejection (HTTP 400)
* Cross-merchant product order rejection (HTTP 400)
* Invalid product reference rejection (HTTP 400)

---

## ⚡ Running the API Server

```bash
uvicorn app.main.app --reload --port 8000
```

* **API Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
* **Interactive OpenAPI Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔒 Important Security & Architecture Rules

1. **Server-Side Pricing**: The backend never accepts client-provided item prices or order totals. All unit prices are extracted from the verified product catalog and summed on the backend.
2. **Inventory Safety**: Orders are checked against real-time stock levels. Orders requesting more items than available are rejected with HTTP 400.
3. **SQLite Foreign Keys**: SQLite foreign key constraints are enforced at connection initialization.
