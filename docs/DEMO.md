# 🏆 Mercora — Hackathon Presentation & Live Demo Guide

> **Official Pitch**: *"Mercora helps merchants grow revenue and makes them safely transactable by AI buyers—without giving AI unrestricted control over money."*

---

## ⏱️ 3-Minute Live Presentation Script

### 🎬 Part 1: Merchant Growth & AI Readiness (0:00 – 0:30)
**Screen**: Navigate to **`/dashboard`** and **`/agent-commerce/readiness`**
- **Presenter Narration**:
  > "Welcome to **Mercora**. E-commerce is experiencing a massive paradigm shift. Today, merchants build websites for humans. Tomorrow, autonomous AI agents will be the primary buyers researching, negotiating, and purchasing on behalf of consumers.
  > 
  > Mercora is an enterprise-grade platform that solves two critical challenges:
  > 1. It helps merchants maximize revenue through LangGraph-driven growth recommendations (cross-sells, bundles, and slow-moving campaigns).
  > 2. It makes merchants machine-readable and transactable by external AI buyers with strict financial safety governance."
- **Key Visuals to Highlight**:
  - Executive Overview KPI cards: GMV Revenue, AOV, Conversion Rate.
  - **AI Growth Opportunities**: Explainable Recommendations with verifiable Database Facts vs AI Hypotheses.
  - **AI Commerce Readiness Meter (100%)**: 8-point weighted capability checklist (Catalog, Search, SKU specs, Real-time stock, Idempotent orders, Test payments, Spend limits, Audit trail).

---

### 🤖 Part 2: Autonomous AI Buyer Discovery & Ordering (0:30 – 1:00)
**Screen**: Navigate to **`/demo`** (3-Minute Judge Demo Screen)
- **Presenter Action**: Click **`[Run Successful Purchase Flow]`**
- **Presenter Narration**:
  > "Let's watch an external AI Buyer agent that received the prompt: *'I need running shoes under ₹3000.'*
  > 
  > Notice what happens in real time:
  > - **Step 1**: The AI Buyer connects to the Mercora API Gateway and negotiates the standardized `v1.0` discovery contract.
  > - **Step 2**: It queries the canonical machine-readable catalog with deterministic multi-factor search ranking.
  > - **Step 3**: It selects Product #1 (*Running Shoes* at ₹2,499.00).
  > - **Step 4**: Real-time server-side stock verification confirms available units.
  > - **Step 5**: An idempotent, server-priced order (#31) is created. The client/AI cannot dictate prices."

---

### 🛡️ Part 3: Explainable, Bounded & Gated Money Proposal (1:00 – 1:45)
**Screen**: Look at the right panel: **Human-In-The-Loop Approval Gate**
- **Presenter Narration**:
  > "Now observe our core safety invariant: **The AI cannot directly charge money or self-authorize payments.**
  > 
  > Instead, the system evaluates our deterministic Policy Engine:
  > - **Requested Amount**: ₹2,499.00
  > - **Configured Single-Transaction Limit**: ₹5,000.00
  > - **Risk Classification**: `MEDIUM`
  > - **Human Approval**: `REQUIRED`
  > 
  > The merchant receives a transparent explainability statement before any checkout happens."
- **Presenter Action**: Click **`[APPROVE & PAY (₹2,499.00)]`**

---

### 💳 Part 4: Razorpay Test-Mode Payment & Cryptographic Settlement (1:45 – 2:15)
**Screen**: Observe the verification badge and order confirmation
- **Presenter Narration**:
  > "Upon explicit merchant approval:
  > - A Razorpay Test-Mode checkout order is generated (`order_test_...`) with paise-level precision (249,900 paise).
  > - The external buyer completes payment and submits the cryptographic HMAC-SHA256 signature.
  > - The server independently verifies the signature, marks the order as `PAID`, and logs the transaction.
  > - API secrets and webhook secrets remain strictly isolated on the backend and are never exposed to LLM prompts."

---

### 🚫 Part 5: Security Boundary & Limit Breach Protection (2:15 – 2:45)
**Screen**: Click **`[Trigger Blocked Limit Breach]`**
- **Presenter Action**: Click button on `/demo` screen
- **Presenter Narration**:
  > "What happens if an AI buyer attempts an unconstrained or malicious transaction?
  > 
  > Here, the AI buyer orders 5 pairs of shoes totaling ₹12,495.00 against the merchant's configured ₹5,000 cap:
  > - **Result**: `BLOCKED SAFELY` by the Policy Engine (`PAYMENT_LIMIT_EXCEEDED`).
  > - **Razorpay Orders Created**: 0
  > - **Money Moved**: ₹0.00
  > - The attempted breach is permanently recorded in the immutable audit ledger."

---

### 🔍 Part 6: Trace Timeline, Protocol Inspector & Closing Invariant (2:45 – 3:00)
**Screen**: Navigate to **`/agent-commerce/inspector`**
- **Presenter Narration**:
  > "Judges can inspect every raw JSON protocol envelope in the **Protocol Inspector**—from `DISCOVER` and `SEARCH` to `CREATE_ORDER` and `PROPOSE_PAYMENT`.
  > 
  > In conclusion:
  > **Mercora makes merchants discoverable and sellable to the next generation of AI buyers while keeping every financial decision explainable, bounded, gated, and auditable.**"

---

## 💻 Standalone Terminal Demo Runner

For judges who want to inspect the protocol from the command line without the web browser:

```bash
cd backend
.\venv\Scripts\python.exe demo_external_buyer.py
```

This standalone script executes all 5 independent scenarios:
1. `SCENARIO 1`: Autonomous AI Purchase Flow (100% Success)
2. `SCENARIO 2`: Blocked Transaction Exceeding Merchant Limit (Policy Safety)
3. `SCENARIO 3`: Real-Time Out-of-Stock Recovery Handling
4. `SCENARIO 4`: Simulated Payment Decline & State Preservation
5. `SCENARIO 5`: Idempotent Duplicate Replay Protection

---

## 🛡️ Core Governance & Safety Matrix

| Guardrail | Enforcement Mechanism | Failure Defense |
| :--- | :--- | :--- |
| **Pricing Integrity** | Server computes all subtotals from database ground truth | Client price tampering rejected |
| **Inventory Protection** | Real-time database stock verification | Negative inventory or race conditions blocked |
| **Spend Boundaries** | Single transaction & daily limit policy engine | Limit breaches rejected with 0 charges |
| **Payment Authorization** | Human-In-The-Loop approval gate (`[APPROVE & PAY]`) | AI self-authorization prevented |
| **Cryptographic Verification** | HMAC-SHA256 signature verification in test mode | Unsigned or tampered callbacks rejected |
| **Idempotency** | Unique `Idempotency-Key` tracking | Duplicate requests return existing receipt |
| **Credential Safety** | Environment isolation; masked logging | Zero LLM prompt exposure |
