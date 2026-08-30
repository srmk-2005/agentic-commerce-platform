# AI Merchant Commerce Platform — Frontend Dashboard

Modern, glassmorphic React dashboard for merchants to manage catalog products, track transactions, review customer profiles, converse with the LangGraph AI Assistant, and govern growth action approvals.

---

## 🛠 Tech Stack

* **Framework**: React 18
* **Language**: TypeScript
* **Bundler & Tooling**: Vite 5.0
* **Routing**: React Router DOM v6
* **Icons**: Lucide React
* **Styling**: Vanilla CSS Design System with dark glassmorphism, responsive tables, and typography tokens

---

## 🚀 Setup & Running Locally

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment (Optional)

Create `.env` if you need to point to a custom backend URL:
```ini
VITE_API_URL=http://localhost:8000/api/v1
```

### 3. Run Development Server

```bash
npm run dev
```

The frontend dashboard will be live at: [http://localhost:5173](http://localhost:5173)

### 4. Build for Production

```bash
npm run build
```

---

## 📱 Features & Views

* **`/dashboard` (Executive Overview)**: Displays real-time KPIs for Total Revenue, Total Orders, Catalog Size, Active AI Opportunities, Pending Approvals, Active Campaigns, and Low Stock Inventory Alerts.
* **`/ai-assistant` (Merchant AI Copilot)**: Conversational chat interface with quick suggestion chips, live opportunity cards (with explicit FACT vs. AI INTERPRETATION separation), and interactive Action Proposal cards.
* **`/approvals` (Action Approvals Center)**: Human-In-The-Loop review queue for merchant growth proposals. Features detailed financial math breakdown (Original Bundle Price vs. Discounted Price), safety checks, and One-Click Approve / Reject actions with logged reasons.
* **`/campaigns` (Growth Campaign Manager)**: Overview and management of all active, draft, paused, and completed marketing campaigns with attached discount offers and product role mappings.
* **`/audit` (Activity & Compliance Ledger)**: Full chronological timeline of actions performed by `AI_AGENT`, `MERCHANT`, and `SYSTEM` actors, with status filters and structured JSON metadata inspection.
* **`/products` (Catalog Management)**: Product table with keyword search, category filtering, stock level badges, Add Product modal, and Edit/Delete operations.
* **`/orders` (Order Processing & Ledger)**: Transaction history with status filters, detailed line-item breakdown drawer, and interactive Order Creation modal with server-side price calculations.
* **`/customers` (Customer Directory)**: Customer records showing registration dates, total orders placed, and lifetime customer spend.
