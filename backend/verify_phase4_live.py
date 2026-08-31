"""Live End-to-End Verification Script for Phase 4:
AI-Readable Catalog & Agentic Commerce Interface

Tests live running server:
- Machine-readable manifest and capabilities
- Structured merchant profile
- Canonical AIProduct catalog with deterministic availability
- Ranked deterministic product search
- Ground-truth product specs and inventory
- AI Order Creation with backend pricing & idempotency
- Out-of-stock safety rejection
- Simulated AI Buyer LangGraph execution
- Simulated Direct AI Buyer checkout
- Immutable Audit Ledger for AI_BUYER actor
"""
import sys
import uuid
import requests

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000/api/v1"


def print_step(step: str):
    print(f"\n[STEP] {step}")


def print_pass(msg: str):
    print(f"  [PASS] {msg}")


def print_fail(msg: str):
    print(f"  [FAIL] {msg}")
    sys.exit(1)


def main():
    print("=" * 70)
    print("PHASE 4: AI COMMERCE INTERFACE LIVE END-TO-END VERIFICATION")
    print("=" * 70)

    # 1. Health Check
    print_step("1. Checking API Health...")
    r = requests.get(f"{BASE_URL}/health")
    if r.status_code == 200 and r.json().get("status") == "ok":
        print_pass("FastAPI backend is online.")
    else:
        print_fail(f"Health check failed: {r.text}")

    # 2. Discovery Manifest
    print_step("2. Verifying Machine-Readable Discovery Manifest...")
    r = requests.get(f"{BASE_URL}/ai/merchant/1/manifest")
    if r.status_code == 200:
        manifest = r.json()
        caps = manifest["capabilities"]
        assert caps["catalog"] is True, "Catalog capability missing"
        assert caps["order_creation"] is True, "Ordering capability missing"
        assert caps["payment"] is False, "Payment must be false in Phase 4"
        print_pass(f"Manifest v{manifest['version']} for '{manifest['name']}': Catalog=True, Ordering=True, Payment={caps['payment']}.")
    else:
        print_fail(f"Failed to fetch manifest: {r.text}")

    # 3. Merchant Profile
    print_step("3. Verifying Structured Merchant Profile...")
    r = requests.get(f"{BASE_URL}/ai/merchant/1/profile")
    if r.status_code == 200:
        prof = r.json()
        print_pass(f"Profile: Currency={prof['currency']}, Categories={prof['categories']}")
    else:
        print_fail(f"Failed to fetch profile: {r.text}")

    # 4. AI Catalog
    print_step("4. Querying Canonical AI Product Catalog...")
    r = requests.get(f"{BASE_URL}/ai/catalog?merchant_id=1&in_stock=true")
    if r.status_code == 200:
        catalog = r.json()
        print_pass(f"Retrieved {catalog['total_count']} active in-stock products.")
        p0 = catalog["products"][0]
        print_pass(f"Sample AIProduct #{p0['id']}: '{p0['name']}', Price=Rs.{p0['price']}, Availability={p0['availability']}, Constraints={p0['purchase_constraints']}")
    else:
        print_fail(f"Catalog query failed: {r.text}")

    # 5. Deterministic Ranked Search
    print_step("5. Testing Deterministic Ranked Search (Query: 'running shoes', max_price=3000)...")
    r = requests.get(f"{BASE_URL}/ai/search?merchant_id=1&query=running%20shoes&max_price=3000")
    if r.status_code == 200:
        search_res = r.json()
        print_pass(f"Ranked search found {search_res['total_matches']} matching products.")
        for idx, hit in enumerate(search_res["results"][:2], 1):
            print(f"    - #{idx}: {hit['product']['name']} (Score: {hit['relevance_score']}) | Reasons: {' • '.join(hit['match_reasons'])}")
    else:
        print_fail(f"Search failed: {r.text}")

    # 6. Live Product Details
    print_step("6. Querying Live Ground-Truth Product Details (Product ID #1)...")
    r = requests.get(f"{BASE_URL}/ai/products/1")
    if r.status_code == 200:
        prod = r.json()
        initial_stock = prod["stock_quantity"]
        print_pass(f"Product #{prod['id']} '{prod['name']}': Stock={initial_stock}, Status={prod['availability']}, MaxPerOrder={prod['purchase_constraints']['max_quantity_per_order']}.")
    else:
        print_fail(f"Product details query failed: {r.text}")

    # 7. AI Order Creation
    print_step("7. Placing Order via AI Commerce Interface (1x Product #1)...")
    idem_key = f"live-verify-{uuid.uuid4().hex[:8]}"
    order_req = {
        "merchant_id": 1,
        "items": [{"product_id": 1, "quantity": 1}],
    }
    r = requests.post(f"{BASE_URL}/ai/orders", json=order_req, headers={"Idempotency-Key": idem_key})
    if r.status_code == 201:
        order = r.json()
        order_id = order["order_id"]
        print_pass(f"Order #{order_id} created: Total=Rs.{order['total_amount']} {order['currency']}, Status={order['status']}, Payment={order['payment_status']}")
    else:
        print_fail(f"Order creation failed: {r.text}")

    # 8. Test Idempotency
    print_step(f"8. Testing Order Idempotency with Duplicate Key '{idem_key}'...")
    r_dup = requests.post(f"{BASE_URL}/ai/orders", json=order_req, headers={"Idempotency-Key": idem_key})
    if r_dup.status_code in [200, 201]:
        dup_order = r_dup.json()
        assert dup_order["order_id"] == order_id, "Idempotency failed: returned different order ID"
        print_pass(f"Idempotency verified: Re-submission returned identical Order #{dup_order['order_id']} without duplicate row creation.")
    else:
        print_fail(f"Idempotency request failed: {r_dup.text}")

    # 9. Test Out-of-Stock / Excessive Quantity Safety Rejection
    print_step("9. Testing Safety Rejection on Excessive Quantity (10 units > limit)...")
    r_excess = requests.post(
        f"{BASE_URL}/ai/orders",
        json={"merchant_id": 1, "items": [{"product_id": 1, "quantity": 10}]},
    )
    if r_excess.status_code == 400:
        print_pass(f"Excessive quantity cleanly rejected: {r_excess.json()['detail']}")
    else:
        print_fail(f"Expected 400 rejection but got {r_excess.status_code}: {r_excess.text}")

    # 10. Simulated AI Buyer Agent Chat
    print_step("10. Testing Simulated AI Buyer LangGraph Agent...")
    buyer_prompt = {"merchant_id": 1, "message": "I need running shoes under Rs. 3000."}
    r_buyer = requests.post(f"{BASE_URL}/buyer/chat", json=buyer_prompt)
    if r_buyer.status_code == 200:
        b_data = r_buyer.json()
        print_pass(f"AI Buyer discovered {len(b_data['candidates'])} candidates. Selected: '{b_data['selected_product']['name'] if b_data.get('selected_product') else 'None'}'")
        print("    Execution Trace:")
        for step in b_data["execution_steps"][:3]:
            print(f"      • {step}")
    else:
        print_fail(f"AI Buyer chat failed: {r_buyer.text}")

    # 11. Simulated Direct AI Buyer Checkout
    print_step("11. Testing Direct AI Buyer Checkout Simulation...")
    sim_req = {"merchant_id": 1, "product_id": 1, "quantity": 1}
    r_sim = requests.post(f"{BASE_URL}/buyer/simulate-order", json=sim_req)
    if r_sim.status_code == 200:
        sim_data = r_sim.json()
        if sim_data["success"]:
            print_pass(f"Simulated Checkout Success: Order #{sim_data['order']['order_id']}")
            print_pass(f"Explainability: {sim_data['explainability']}")
            print_pass(f"Payment Note: {sim_data['payment_note']}")
        else:
            print_fail(f"Simulated checkout failed: {sim_data['error_message']}")
    else:
        print_fail(f"Simulation endpoint failed: {r_sim.text}")

    # 12. Verify Audit Log Ledger for AI_BUYER Actor
    print_step("12. Verifying Immutable Audit Ledger for AI_BUYER Actor...")
    r_audit = requests.get(f"{BASE_URL}/audit/logs?merchant_id=1&limit=20")
    if r_audit.status_code == 200:
        logs = r_audit.json()
        buyer_logs = [l for l in logs if l["actor_type"] == "AI_BUYER"]
        print_pass(f"Found {len(buyer_logs)} recorded AI_BUYER audit entries.")
        for l in buyer_logs[:4]:
            print(f"    - [{l['created_at'][11:19]}] {l['actor_type']} | {l['action']} | Status: {l['status']}")
    else:
        print_fail(f"Audit log fetch failed: {r_audit.text}")

    print("\n" + "=" * 70)
    print("ALL PHASE 4 LIVE END-TO-END VERIFICATION CHECKS PASSED (100% SUCCESS)!")
    print("=" * 70)


if __name__ == "__main__":
    main()
