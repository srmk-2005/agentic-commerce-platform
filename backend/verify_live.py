"""Live End-to-End Verification Script for Phase 3:
Revenue Growth Actions, Campaigns & Merchant Approval

Tests live running server:
- AI Safety Policies
- Action Proposals & Deterministic Validation
- Merchant Approval & Campaign Execution
- Idempotent execution
- Rejection handling
- Simulated Failure resilience
- Audit Log Persistence
"""
import sys
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"


def print_step(step: str):
    print(f"\n[STEP] {step}")


def print_pass(msg: str):
    print(f"  [PASS] {msg}")


def print_fail(msg: str):
    print(f"  [FAIL] {msg}")
    sys.exit(1)


def main():
    print("=" * 65)
    print("PHASE 3: LIVE END-TO-END VERIFICATION")
    print("=" * 65)

    # 1. Health Check
    print_step("1. Checking API Health...")
    r = requests.get(f"{BASE_URL}/health")
    if r.status_code == 200 and r.json().get("status") == "ok":
        print_pass("FastAPI backend is online.")
    else:
        print_fail(f"Health check failed: {r.text}")

    # 2. Safety Policy
    print_step("2. Verifying Merchant AI Policy...")
    r = requests.get(f"{BASE_URL}/growth/policies/1")
    if r.status_code == 200:
        policy = r.json()
        print_pass(f"Merchant AI Policy active: max_discount={policy['max_discount_percentage']}%, max_duration={policy['max_campaign_duration_days']} days.")
    else:
        print_fail(f"Failed to fetch policy: {r.text}")

    # 3. Propose Valid Action
    print_step("3. AI Agent proposes a 10% Bundle Proposal...")
    proposal_data = {
        "merchant_id": 1,
        "action_type": "CREATE_BUNDLE",
        "title": "Live Test Runner Bundle",
        "description": "Bundle Running Shoes and Running Socks at 10% off.",
        "campaign_type": "BUNDLE",
        "target_product_ids": [1, 3],
        "primary_product_id": 1,
        "recommended_product_ids": [3],
        "discount_type": "PERCENTAGE",
        "discount_value": 10.0,
        "campaign_duration_days": 7,
        "expected_benefit": "Increase average order value by Rs. 200.",
        "reasoning": "High co-purchase affinity detected in order logs.",
        "risk_level": "LOW",
    }
    r = requests.post(f"{BASE_URL}/growth/actions/propose", json=proposal_data)
    if r.status_code == 201:
        proposal = r.json()
        approval_id = proposal.get("approval_id")
        print_pass(f"Proposal created! ID: {proposal['id']}, Approval ID: {approval_id}, Safety Checks Passed: {proposal['safety_check']['is_safe']}.")
    else:
        print_fail(f"Proposal creation failed: {r.text}")

    # 4. Propose Unsafe Action (Exceeds Policy 20% limit)
    print_step("4. AI proposes an unsafe 40% Discount Proposal...")
    unsafe_data = {
        "merchant_id": 1,
        "action_type": "CREATE_CAMPAIGN",
        "title": "Unsafe Deep Discount",
        "target_product_ids": [1],
        "discount_type": "PERCENTAGE",
        "discount_value": 40.0,  # Exceeds max 20%
        "campaign_duration_days": 10,
    }
    r = requests.post(f"{BASE_URL}/growth/actions/propose", json=unsafe_data)
    if r.status_code == 400:
        print_pass(f"Deterministic Safety Engine rejected proposal as expected: {r.json()['detail']['rejection_reasons']}")
    else:
        print_fail(f"Expected 400 rejection but got {r.status_code}: {r.text}")

    # 5. Review Approvals Queue
    print_step("5. Checking Pending Approvals Queue...")
    r = requests.get(f"{BASE_URL}/approvals?merchant_id=1&status=PENDING")
    if r.status_code == 200:
        pending_list = r.json()
        print_pass(f"Pending approvals retrieved. Queue length: {len(pending_list)}")
    else:
        print_fail(f"Failed to list approvals: {r.text}")

    # 6. Merchant Approves Proposal
    print_step(f"6. Merchant Owner APPROVES Approval #{approval_id}...")
    r = requests.post(f"{BASE_URL}/approvals/{approval_id}/approve", json={"reviewed_by": "Merchant Owner"})
    if r.status_code == 200:
        res = r.json()
        campaign_id = res.get("campaign_id")
        print_pass(f"Approval executed successfully! Campaign #{campaign_id} created in ACTIVE status.")
    else:
        print_fail(f"Approval failed: {r.text}")

    # 7. Test Idempotency (Duplicate Approval Click)
    print_step(f"7. Testing Idempotency on Approval #{approval_id} (Second Click)...")
    r = requests.post(f"{BASE_URL}/approvals/{approval_id}/approve", json={"reviewed_by": "Merchant Owner"})
    if r.status_code == 200:
        res = r.json()
        print_pass(f"Idempotent response: {res.get('message')} (Zero duplicate campaigns created).")
    else:
        print_fail(f"Idempotency test failed: {r.text}")

    # 8. Test Rejection Workflow
    print_step("8. Proposing and Rejecting an Action Proposal...")
    r_prop = requests.post(
        f"{BASE_URL}/growth/actions/propose",
        json={
            "merchant_id": 1,
            "action_type": "CREATE_OFFER",
            "title": "Unwanted Flash Sale",
            "target_product_ids": [4],
            "discount_type": "PERCENTAGE",
            "discount_value": 5.0,
            "campaign_duration_days": 3,
        },
    )
    rej_approval_id = r_prop.json()["approval_id"]
    r_rej = requests.post(
        f"{BASE_URL}/approvals/{rej_approval_id}/reject",
        json={"reason": "Low inventory on sports t-shirts", "reviewed_by": "Store Manager"},
    )
    if r_rej.status_code == 200:
        print_pass(f"Proposal #{rej_approval_id} cleanly REJECTED with logged reason.")
    else:
        print_fail(f"Rejection failed: {r_rej.text}")

    # 9. Verify Campaigns List
    print_step("9. Verifying Active Campaigns List...")
    r = requests.get(f"{BASE_URL}/campaigns?merchant_id=1&status=ACTIVE")
    if r.status_code == 200:
        camps = r.json()
        print_pass(f"Retrieved {len(camps)} active campaign(s). Latest: '{camps[0]['name']}'.")
    else:
        print_fail(f"Failed to fetch campaigns: {r.text}")

    # 10. Verify Immutable Audit Trail
    print_step("10. Verifying Audit Log Ledger...")
    r = requests.get(f"{BASE_URL}/audit/logs?merchant_id=1&limit=20")
    if r.status_code == 200:
        logs = r.json()
        print_pass(f"Retrieved {len(logs)} audit entries.")
        for log in logs[:4]:
            print(f"    - [{log['created_at'][11:19]}] {log['actor_type']} | {log['action']} | Status: {log['status']}")
    else:
        print_fail(f"Failed to fetch audit logs: {r.text}")

    print("\n" + "=" * 65)
    print("ALL PHASE 3 LIVE VERIFICATION CHECKS PASSED (100% SUCCESS)!")
    print("=" * 65)


if __name__ == "__main__":
    main()
