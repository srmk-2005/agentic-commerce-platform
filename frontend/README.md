# AI Merchant Commerce Platform — Frontend Dashboard (Phase 1)

Modern, glassmorphic React dashboard for merchants to manage catalog products, track transactions, review customer profiles, and monitor revenue metrics.

---

## 🛠 Tech Stack

* **Framework**: React 18
* **Language**: TypeScript
* **Bundler**: Vite
* **Routing**: React Router DOM v6
* **Icons**: Lucide React
* **Styling**: Vanilla CSS Design System with dark glassmorphism, responsive tables, and custom tokens

---

## 🚀 Setup & Running Locally

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment (Optional)

Create `.env` if you need to point to a non-default backend port:
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

* **/dashboard**: Overview of Total Revenue, Orders, Products, Customers, low inventory alerts, and recent transactions.
* **/products**: Catalog table with live keyword search, category filtering, stock level badges, Add Product modal, and Edit/Delete actions.
* **/orders**: Transaction history with order status filters (Pending, Confirmed, Cancelled, Failed), detailed line item breakdown modal, and interactive Order Creation modal with live price estimation.
* **/customers**: Customer directory showing registration dates, total orders, and lifetime customer spend.
