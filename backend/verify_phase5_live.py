"""Comprehensive Phase 5 Live End-to-End Verification Script.

Demonstrates:
Scenario A: Successful Bounded Payment Flow (Explainable, Bounded & Gated)
Scenario B: Blocked Payment Exceeding Limit
Scenario C: Merchant Explicit Rejection
Scenario D: Simulated Payment Failure & Safe State Handling
Scenario E: Idempotency & Replay Protection
"""
import sys
import json
import requests
from app.payments.razorpay_service import razorpay_adapter

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000/api/v1"


def print_step(title: str):
    print(f"\n{'='*70}\n📌 {title}\n{'='*70}")


def run_live_verification():
    print("\n🚀 STARTING PHASE 5 LIVE VERIFICATION SUITE\n")

    # 0. Health Check
    res = requests.get(f"{BASE_URL}/health")
    if res.status_code != 200:
        print("❌ Backend is not running on port 8000!")
        sys.exit(1)
    print("✅ Backend service is HEALTHY.")

    # 1. Merchant & Products Setup
    import uuid
    run_id = uuid.uuid4().hex[:6]
    print_step("STEP 1: Create Merchant with AI Policy")
    m_res = requests.post(f"{BASE_URL}/merchants", json={
        "name": "Apex Athletics Live Store",
        "email": f"apex_live_{run_id}@sports.com",
        "currency": "INR"
    }).json()
    m_id = m_res["id"]
    print(f"✅ Created Merchant #{m_id}: '{m_res['name']}'")

    p1 = requests.post(f"{BASE_URL}/products", json={
        "merchant_id": m_id,
        "name": "Apex Carbon Pro Running Shoes",
        "category": "Footwear",
        "price": 2499.0,
        "stock_quantity": 25,
        "sku": f"APX-LIVE-{run_id}-01"
    }).json()
    print(f"✅ Created Product #{p1['id']}: '{p1['name']}' (₹{p1['price']})")

    p_expensive = requests.post(f"{BASE_URL}/products", json={
        "merchant_id": m_id,
        "name": "Apex Ultra Titanium Edition",
        "category": "Footwear",
        "price": 9500.0,
        "stock_quantity": 5,
        "sku": f"APX-LUX-{run_id}-99"
    }).json()
    print(f"✅ Created Product #{p_expensive['id']}: '{p_expensive['name']}' (₹{p_expensive['price']})")

    # =========================================================================
    # SCENARIO A: SUCCESSFUL BOUNDED PAYMENT FLOW
    # =========================================================================
    print_step("SCENARIO A: AI Buyer Order -> Payment Intent -> Approval -> Razorpay Verification")

    # A1. AI Buyer Order
    order_res = requests.post(f"{BASE_URL}/ai/orders", json={
        "merchant_id": m_id,
        "items": [{"product_id": p1["id"], "quantity": 1}],
        "idempotency_key": f"live-order-scen-a-{run_id}"
    }).json()
    order_id = order_res["order_id"]
    print(f"1. AI Buyer created Order #{order_id} (Total: ₹{order_res['total_amount']:,.2f})")

    # A2. Propose Payment Intent
    intent_res = requests.post(f"{BASE_URL}/ai/payments/propose", json={
        "merchant_id": m_id,
        "order_id": order_id,
        "idempotency_key": f"live-pay-scen-a-{run_id}-{order_id}"
    }).json()
    intent_id = intent_res["id"]
    print(f"2. Payment Intent Proposed: #{intent_id}")
    print(f"   • Amount: ₹{intent_res['amount']:,.2f} {intent_res['currency']}")
    print(f"   • Status: {intent_res['status']}")
    print(f"   • Risk Tier: {intent_res['risk_level']}")
    print(f"   • Requires Approval: {intent_res['requires_approval']}")
    print(f"   • Explainability: \"{intent_res['explainability']}\"")
    assert intent_res["status"] == "PENDING_APPROVAL"

    # A3. Human / Merchant Explicit Approval
    print("\n3. Human/Merchant reviews payment proposal and executes [APPROVE & PAY]...")
    appr_res = requests.post(f"{BASE_URL}/ai/payments/{intent_id}/approve", json={
        "reviewed_by": "Store Manager (Live Verification)",
        "reason": "Authorized legitimate AI Buyer transaction."
    }).json()
    rzp_order_id = appr_res["razorpay_order_id"]
    print(f"   • Razorpay Test-Mode Order ID: {rzp_order_id}")
    print(f"   • Charged Amount: {appr_res['amount']} paise (₹{appr_res['amount']/100:,.2f})")
    print(f"   • Test Mode: {appr_res['is_test_mode']}")
    assert appr_res["amount"] == 249900  # Exact paise conversion

    # A4. Razorpay Test-Mode Signature Verification
    rzp_payment_id = "pay_test_live_998811"
    valid_sig = razorpay_adapter.generate_test_signature(rzp_order_id, rzp_payment_id)

    print("\n4. Submitting cryptographic HMAC-SHA256 signature for server verification...")
    verify_res = requests.post(f"{BASE_URL}/payments/verify", json={
        "payment_intent_id": intent_id,
        "razorpay_order_id": rzp_order_id,
        "razorpay_payment_id": rzp_payment_id,
        "razorpay_signature": valid_sig
    }).json()
    print(f"   • Verification Result: {verify_res['status']}")
    print(f"   • Message: {verify_res['message']}")
    assert verify_res["success"] is True
    assert verify_res["status"] == "CAPTURED"

    # A5. Verify Order & Audit State
    final_order = requests.get(f"{BASE_URL}/orders/{order_id}").json()
    print(f"5. Final Order #{order_id} Status: {final_order['status']} (Payment: {final_order['payment_status']})")
    assert final_order["status"] == "PAID"
    print("✅ SCENARIO A: 100% SUCCESS")

    # =========================================================================
    # SCENARIO B: BLOCKED PAYMENT EXCEEDING LIMIT
    # =========================================================================
    print_step("SCENARIO B: Blocked Payment Exceeding Merchant AI Limit (₹9,500 > ₹5,000)")

    order_b = requests.post(f"{BASE_URL}/ai/orders", json={
        "merchant_id": m_id,
        "items": [{"product_id": p_expensive["id"], "quantity": 1}]
    }).json()
    order_b_id = order_b["order_id"]
    print(f"1. AI Buyer created Order #{order_b_id} for ₹{order_b['total_amount']:,.2f}")

    intent_b = requests.post(f"{BASE_URL}/ai/payments/propose", json={
        "merchant_id": m_id,
        "order_id": order_b_id
    })
    print(f"2. Proposal Response Code: {intent_b.status_code}")
    print(f"   • Block Reason: {intent_b.json().get('detail')}")
    assert intent_b.status_code == 400
    assert "exceeds maximum allowed AI transaction limit" in intent_b.json().get("detail", "")
    print("✅ SCENARIO B: BLOCKED CORRECTLY BY DETERMINISTIC POLICY")

    # =========================================================================
    # SCENARIO C: MERCHANT EXPLICIT REJECTION
    # =========================================================================
    print_step("SCENARIO C: Human/Merchant Explicit Rejection of Payment Intent")

    order_c = requests.post(f"{BASE_URL}/ai/orders", json={
        "merchant_id": m_id,
        "items": [{"product_id": p1["id"], "quantity": 1}]
    }).json()
    intent_c = requests.post(f"{BASE_URL}/ai/payments/propose", json={
        "merchant_id": m_id,
        "order_id": order_c["order_id"]
    }).json()

    print(f"1. Payment Intent #{intent_c['id']} proposed for Order #{order_c['order_id']}")
    rej_res = requests.post(f"{BASE_URL}/ai/payments/{intent_c['id']}/reject", json={
        "reviewed_by": "Merchant Admin",
        "reason": "Suspicious buyer velocity"
    }).json()
    print(f"2. Rejection Output: Status={rej_res['status']}, Reviewed By={rej_res['approved_by']}")
    assert rej_res["status"] == "REJECTED"
    print("✅ SCENARIO C: REJECTED SAFELY WITHOUT RAZORPAY CHECKOUT")

    # =========================================================================
    # SCENARIO D: SIMULATED PAYMENT FAILURE & RECOVERY
    # =========================================================================
    print_step("SCENARIO D: Simulated Test-Mode Bank Decline Handling")

    order_d = requests.post(f"{BASE_URL}/ai/orders", json={
        "merchant_id": m_id,
        "items": [{"product_id": p1["id"], "quantity": 1}]
    }).json()
    intent_d = requests.post(f"{BASE_URL}/ai/payments/propose", json={
        "merchant_id": m_id,
        "order_id": order_d["order_id"]
    }).json()
    requests.post(f"{BASE_URL}/ai/payments/{intent_d['id']}/approve")

    fail_res = requests.post(
        f"{BASE_URL}/payments/simulate-failure?payment_intent_id={intent_d['id']}&failure_reason=Simulated%20Card%20Declined"
    ).json()
    print(f"1. Payment Failure Output: Status={fail_res['status']}, Reason='{fail_res['failure_reason']}'")
    assert fail_res["status"] == "FAILED"

    order_d_final = requests.get(f"{BASE_URL}/orders/{order_d['order_id']}").json()
    print(f"2. Order State: Status={order_d_final['status']}, Payment={order_d_final['payment_status']}")
    assert order_d_final["status"] == "PAYMENT_FAILED"
    print("✅ SCENARIO D: FAILED GRACEFULLY WITHOUT FALSE PAID STATUS")

    # =========================================================================
    # SCENARIO E: REPLAY & IDEMPOTENCY PROTECTION
    # =========================================================================
    print_step("SCENARIO E: Replay & Idempotent Verification Protection")

    replay_verify = requests.post(f"{BASE_URL}/payments/verify", json={
        "payment_intent_id": intent_id,
        "razorpay_order_id": rzp_order_id,
        "razorpay_payment_id": rzp_payment_id,
        "razorpay_signature": valid_sig
    }).json()
    print(f"1. Replay Verification Output: {replay_verify['message']} (Status={replay_verify['status']})")
    assert replay_verify["success"] is True
    assert "already verified" in replay_verify["message"]
    print("✅ SCENARIO E: IDEMPOTENT REPLAY SAFELY HANDLED")

    # =========================================================================
    # AUDIT TRAIL VERIFICATION
    # =========================================================================
    print_step("STEP 6: Audit Trail Inspection")
    audit_res = requests.get(f"{BASE_URL}/audit/logs?merchant_id={m_id}&limit=15").json()
    print(f"Found {len(audit_res)} structured audit entries for Merchant #{m_id}:")
    for a in audit_res[:6]:
        print(f" • [{a['actor_type']}] {a['action']} -> {a['status']} ({a.get('reason', '')[:60]}...)")

    print("\n🎉 ALL PHASE 5 LIVE VERIFICATION SCENARIOS PASSED WITH ZERO ERRORS!\n")


if __name__ == "__main__":
    run_live_verification()
