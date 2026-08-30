# AI Merchant Commerce Platform — Backend Service

Production-grade FastAPI backend service powering merchant catalog management, LangGraph agentic revenue intelligence, deterministic pricing safety, and Human-In-The-Loop (HITL) approval workflows.

---

## 🛠 Tech Stack

* **Language**: Python 3.12+
* **Framework**: FastAPI (Asynchronous REST API, auto-generated OpenAPI & Swagger docs)
* **Agentic Framework**: LangGraph & LangChain Core
* **LLM Providers**: `langchain-google-genai` (Google Gemini 2.5 / 1.5 Flash), `langchain-groq` (Groq Llama 3.3 70B)
* **Validation**: Pydantic v2 & Pydantic-Settings
* **ORM & Database**: SQLAlchemy 2.0 with SQLite (WAL mode, explicit foreign keys enabled via `PRAGMA foreign_keys=ON;`)
* **Testing**: Pytest & HTTPX TestClient (60 automated unit & integration tests)

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

Key environment variables in `.env`:
```ini
DATABASE_URL=sqlite:///./merchant_commerce.db
APP_ENV=development
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
API_V1_STR=/api/v1
PROJECT_NAME="AI Merchant Commerce Platform"

# LLM Configuration
PRIMARY_LLM_PROVIDER=gemini # or "groq"
GEMINI_API_KEY="your_gemini_key"
GEMINI_MODEL=gemini-2.5-flash
GROQ_API_KEY="your_groq_key"
GROQ_MODEL=llama-3.3-70b-versatile
MOCK_AI_MODE=false
```

---

## 📦 Database Seeding

Populate the database with demo merchant **Chennai Sports Store**, catalog products, customers, and historical order co-purchases:

```bash
python seed.py
```

---

## 🧪 Automated Testing

Run the complete test suite (60 unit, integration, and safety tests):

```bash
.\venv\Scripts\python.exe -m pytest -v
```

### Test Coverage Highlights:
* **Agent Execution & Graph**: Multi-node LangGraph pipeline execution, merchant context loading, co-purchase affinity extraction.
* **LLM Failover**: Gemini $\leftrightarrow$ Groq failover and deterministic local mock engine fallback.
* **Safety Boundaries**: Rejection of price modification attempts, discount ceiling violations, and inactive/out-of-stock product promotions.
* **Growth Action Proposals**: Server-side deterministic bundle price calculations, margin checks, and discount calculations.
* **Merchant Approvals**: One-click approval, rejection reason logging, and pre-execution inventory revalidation.
* **Idempotency & Resilience**: Duplicate approval deduplication and simulated failure rollback.
* **Commerce Foundation**: Server-side order pricing, stock level decrements, and foreign key integrity.

---

## ⚡ Running the API Server

```bash
uvicorn app.main:app --reload --port 8000
```

* **Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
* **Interactive OpenAPI Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔒 Security & Architecture Principles

1. **Strict Read-Only Agent Boundary**: The AI Agent is purely analytical. It has zero capability to mutate prices, charge cards, or activate campaigns without merchant review.
2. **Server-Side Pricing Engine**: The backend never accepts client-provided item prices or order totals. All unit prices are pulled from verified product records and calculated on the backend.
3. **Deterministic Safety Policies**: All action proposals are checked against `MerchantAiPolicy` limits (max discount %, max duration, active product status).
4. **Pre-Execution Revalidation**: Before activating an approved campaign, the system re-validates current real-time stock levels.
5. **Immutable Audit Logging**: Every action by `AI_AGENT`, `MERCHANT`, or `SYSTEM` is recorded in `audit_logs` and `agent_actions`.
