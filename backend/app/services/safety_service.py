"""Deterministic Safety Policy Service for AI Merchant Growth Actions."""
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.db.models import Merchant, MerchantAiPolicy, Product
from app.schemas.growth import ActionProposalCreate, SafetyCheckItem, SafetyCheckResult


class SafetyService:
    """
    Enforces deterministic business boundaries and safety constraints.
    The LLM never determines whether an action is permissible.
    """

    @staticmethod
    def get_or_create_policy(db: Session, merchant_id: int) -> MerchantAiPolicy:
        """Fetch or initialize default merchant AI safety policy."""
        policy = db.query(MerchantAiPolicy).filter(MerchantAiPolicy.merchant_id == merchant_id).first()
        if not policy:
            policy = MerchantAiPolicy(
                merchant_id=merchant_id,
                max_discount_percentage=20.0,
                max_discount_amount=1000.0,
                auto_approve_non_financial=False,
                require_approval_for_campaigns=True,
                require_approval_for_discounts=True,
                max_campaign_duration_days=30,
                is_enabled=True,
            )
            db.add(policy)
            db.commit()
            db.refresh(policy)
        return policy

    @classmethod
    def validate_action_proposal(
        cls,
        db: Session,
        proposal: ActionProposalCreate,
    ) -> SafetyCheckResult:
        """
        Runs comprehensive deterministic checks against merchant policies and catalog facts.
        """
        checks: List[SafetyCheckItem] = []
        rejections: List[str] = []

        # 1. Merchant Validity & Feature Enabled
        merchant = db.query(Merchant).filter(Merchant.id == proposal.merchant_id).first()
        policy = cls.get_or_create_policy(db, proposal.merchant_id)

        merchant_valid = merchant is not None and merchant.is_active
        policy_enabled = policy.is_enabled

        checks.append(SafetyCheckItem(
            check_name="Merchant Active & AI Policy Enabled",
            passed=bool(merchant_valid and policy_enabled),
            details=f"Merchant active: {merchant_valid}, AI growth features enabled: {policy_enabled}",
        ))
        if not merchant_valid:
            rejections.append("Merchant does not exist or is inactive.")
        if not policy_enabled:
            rejections.append("AI growth policies are disabled for this merchant.")

        # 2. Product Ownership, Active Status, and Inventory Stock
        all_product_ids = list(set(proposal.target_product_ids + [
            pid for pid in ([proposal.primary_product_id] if proposal.primary_product_id else []) + proposal.recommended_product_ids
        ]))

        products = db.query(Product).filter(Product.id.in_(all_product_ids)).all()
        products_by_id = {p.id: p for p in products}

        # Check all requested products exist
        missing_ids = [pid for pid in all_product_ids if pid not in products_by_id]
        if missing_ids:
            checks.append(SafetyCheckItem(
                check_name="Product Existence",
                passed=False,
                details=f"Product IDs not found in catalog: {missing_ids}",
            ))
            rejections.append(f"Products with IDs {missing_ids} do not exist.")
        else:
            checks.append(SafetyCheckItem(
                check_name="Product Existence",
                passed=True,
                details=f"All {len(all_product_ids)} referenced products exist in database.",
            ))

        # Check merchant ownership
        foreign_products = [p.name for p in products if p.merchant_id != proposal.merchant_id]
        if foreign_products:
            checks.append(SafetyCheckItem(
                check_name="Product Ownership",
                passed=False,
                details=f"Products belong to other merchants: {foreign_products}",
            ))
            rejections.append(f"Products {foreign_products} do not belong to merchant {proposal.merchant_id}.")
        else:
            checks.append(SafetyCheckItem(
                check_name="Product Ownership",
                passed=True,
                details="All products verified as owned by this merchant.",
            ))

        # Check active status
        inactive_products = [p.name for p in products if not p.is_active]
        if inactive_products:
            checks.append(SafetyCheckItem(
                check_name="Active Product Catalog",
                passed=False,
                details=f"Inactive products cannot be promoted: {inactive_products}",
            ))
            rejections.append(f"Products {inactive_products} are currently inactive.")
        else:
            checks.append(SafetyCheckItem(
                check_name="Active Product Catalog",
                passed=True,
                details="All target products are active in the catalog.",
            ))

        # Check stock quantity (cannot promote 0-stock products)
        out_of_stock = [p.name for p in products if p.stock_quantity <= 0]
        if out_of_stock:
            checks.append(SafetyCheckItem(
                check_name="Inventory Stock Availability",
                passed=False,
                details=f"Out-of-stock products cannot be promoted: {out_of_stock}",
            ))
            rejections.append(f"Products {out_of_stock} have zero available inventory.")
        else:
            checks.append(SafetyCheckItem(
                check_name="Inventory Stock Availability",
                passed=True,
                details="All target items have positive stock availability.",
            ))

        # 3. Discount Percentage Limits
        if proposal.discount_type == "PERCENTAGE":
            discount_pct_ok = (0.0 <= proposal.discount_value <= policy.max_discount_percentage)
            checks.append(SafetyCheckItem(
                check_name="Discount Percentage Limit",
                passed=discount_pct_ok,
                details=f"Proposed: {proposal.discount_value}%, Configured Maximum: {policy.max_discount_percentage}%",
            ))
            if proposal.discount_value < 0:
                rejections.append("Discount percentage cannot be negative.")
            elif proposal.discount_value > policy.max_discount_percentage:
                rejections.append(
                    f"Proposed discount of {proposal.discount_value}% exceeds merchant maximum limit of {policy.max_discount_percentage}%."
                )
        else:
            # Fixed amount discount check
            discount_val_ok = (0.0 <= proposal.discount_value <= policy.max_discount_amount)
            checks.append(SafetyCheckItem(
                check_name="Fixed Discount Amount Limit",
                passed=discount_val_ok,
                details=f"Proposed: ₹{proposal.discount_value}, Configured Maximum: ₹{policy.max_discount_amount}",
            ))
            if proposal.discount_value < 0:
                rejections.append("Discount amount cannot be negative.")
            elif proposal.discount_value > policy.max_discount_amount:
                rejections.append(
                    f"Proposed discount of ₹{proposal.discount_value} exceeds maximum allowed discount amount of ₹{policy.max_discount_amount}."
                )

        # 4. Campaign Duration Limits
        duration_ok = (0 < proposal.campaign_duration_days <= policy.max_campaign_duration_days)
        checks.append(SafetyCheckItem(
            check_name="Campaign Duration Limit",
            passed=duration_ok,
            details=f"Proposed: {proposal.campaign_duration_days} days, Configured Maximum: {policy.max_campaign_duration_days} days",
        ))
        if proposal.campaign_duration_days <= 0:
            rejections.append("Campaign duration must be greater than 0 days.")
        elif proposal.campaign_duration_days > policy.max_campaign_duration_days:
            rejections.append(
                f"Proposed duration of {proposal.campaign_duration_days} days exceeds maximum allowed duration of {policy.max_campaign_duration_days} days."
            )

        is_safe = len(rejections) == 0
        return SafetyCheckResult(
            is_safe=is_safe,
            checks=checks,
            rejection_reasons=rejections,
        )
