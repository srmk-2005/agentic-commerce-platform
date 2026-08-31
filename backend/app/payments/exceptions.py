"""Custom Exceptions for Payments & Bounded Money Actions."""
from fastapi import HTTPException, status


class PaymentPolicyViolationException(HTTPException):
    """Raised when a payment violates merchant AI policy or bounded limits."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class PaymentApprovalRequiredException(HTTPException):
    """Raised when payment execution is attempted without prior approval."""
    def __init__(self, detail: str = "Payment execution requires an approved payment intent."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class PaymentSignatureInvalidException(HTTPException):
    """Raised when Razorpay cryptographic signature verification fails."""
    def __init__(self, detail: str = "Invalid Razorpay payment signature."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class StaleApprovalException(HTTPException):
    """Raised when payment approval has expired or order amount changed."""
    def __init__(self, detail: str = "Payment approval has expired or order changed. Please create a new request."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class DuplicatePaymentException(HTTPException):
    """Raised when attempting to charge an already paid order."""
    def __init__(self, detail: str = "Order has already been paid or duplicate payment is active."):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class OrderNotPayableException(HTTPException):
    """Raised when an order is in an invalid state for payment."""
    def __init__(self, detail: str = "Order is not in a payable state."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
