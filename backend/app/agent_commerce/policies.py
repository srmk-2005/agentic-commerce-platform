"""Deterministic Commerce Safety Policies and AI Readiness Scoring Engine."""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.agent_commerce.schemas import (
    CommerceReadinessResponse,
    CommerceReadinessScoreItem,
)
from app.db.models import (
    AuditLog,
    Merchant,
    MerchantAiPolicy,
    Product,
)


class ReadinessScorer:
    """Calculates deterministic AI Commerce Readiness score (0-100%) and checklist."""

    @staticmethod
    def calculate_readiness(db: Session, merchant_id: int) -> Optional[CommerceReadinessResponse]:
        merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not merchant:
            return None

        policy = db.query(MerchantAiPolicy).filter(MerchantAiPolicy.merchant_id == merchant_id).first()
        products = db.query(Product).filter(Product.merchant_id == merchant_id, Product.is_active == True).all()
        audit_count = db.query(AuditLog).filter(AuditLog.merchant_id == merchant_id).count()

        checklist: List[CommerceReadinessScoreItem] = []
        recommendations: List[str] = []

        # 1. Catalog Available (20%)
        has_catalog = len(products) > 0
        checklist.append(
            CommerceReadinessScoreItem(
                category="Catalog",
                name="AI-Readable Catalog",
                weight=20,
                passed=has_catalog,
                details=f"{len(products)} active product(s) available for AI querying." if has_catalog else "No active products found in catalog.",
            )
        )
        if not has_catalog:
            recommendations.append("Add products to your catalog to enable AI discovery.")

        # 2. Search Available (15%)
        # System has built-in ranked search
        checklist.append(
            CommerceReadinessScoreItem(
                category="Search",
                name="Ranked Multi-Factor Search",
                weight=15,
                passed=True,
                details="Deterministic weighted search endpoint (/api/v1/ai/search) active.",
            )
        )

        # 3. Structured Products (15%)
        has_structured = all(p.category and p.sku and p.price > 0 for p in products) if products else False
        checklist.append(
            CommerceReadinessScoreItem(
                category="Catalog",
                name="Structured Product Specifications",
                weight=15,
                passed=has_structured,
                details="All products contain canonical category, SKU, and non-negative pricing." if has_structured else "Some products lack complete SKU or category metadata.",
            )
        )
        if not has_structured and products:
            recommendations.append("Ensure all products have valid categories, prices, and unique SKUs.")

        # 4. Inventory API (15%)
        has_inventory = any(p.stock_quantity > 0 for p in products) if products else False
        checklist.append(
            CommerceReadinessScoreItem(
                category="Inventory",
                name="Real-Time Stock Verification",
                weight=15,
                passed=has_inventory,
                details="Stock quantities tracked deterministically with inventory safety rules." if has_inventory else "All catalog items are currently out of stock.",
            )
        )
        if not has_inventory:
            recommendations.append("Restock inventory to allow AI buyers to complete purchases.")

        # 5. Order API (15%)
        # System provides atomic stock deduction & idempotency keys
        checklist.append(
            CommerceReadinessScoreItem(
                category="Orders",
                name="Idempotent Order Creation",
                weight=15,
                passed=True,
                details="Server-side order pricing with Idempotency-Key duplicate protection enabled.",
            )
        )

        # 6. Payment Capability (10%)
        has_payment = policy.allow_ai_payment if policy else True
        checklist.append(
            CommerceReadinessScoreItem(
                category="Payments",
                name="Razorpay Test-Mode Integration",
                weight=10,
                passed=has_payment,
                details="Cryptographic HMAC-SHA256 signature verification & paise conversion active." if has_payment else "AI payment capability is disabled in merchant policy.",
            )
        )
        if not has_payment:
            recommendations.append("Enable 'allow_ai_payment' in merchant policy settings.")

        # 7. Policy Configuration (5%)
        has_policy = policy is not None and policy.max_ai_transaction_amount > 0 and policy.require_payment_approval
        checklist.append(
            CommerceReadinessScoreItem(
                category="Governance",
                name="Bounded Safety & Approval Gate",
                weight=5,
                passed=has_policy,
                details=f"Transaction cap: ₹{policy.max_ai_transaction_amount:,.2f}, Approval required: {policy.require_payment_approval}." if policy else "Merchant AI policy is missing.",
            )
        )
        if not has_policy:
            recommendations.append("Configure explicit transaction limits and approval requirements in policy.")

        # 8. Audit Trail (5%)
        has_audit = audit_count > 0
        checklist.append(
            CommerceReadinessScoreItem(
                category="Audit",
                name="Immutable Governance Ledger",
                weight=5,
                passed=has_audit,
                details=f"{audit_count} structured audit event(s) logged." if has_audit else "No audit events logged yet.",
            )
        )

        # Calculate final score
        total_score = sum(item.weight for item in checklist if item.passed)
        is_ready = total_score >= 80

        return CommerceReadinessResponse(
            merchant_id=merchant.id,
            merchant_name=merchant.name,
            readiness_score=total_score,
            is_ready=is_ready,
            checklist=checklist,
            recommendations=recommendations,
        )


readiness_scorer = ReadinessScorer()
