import { request } from './api';
import type {
  Payment,
  PaymentIntent,
  PaymentVerificationRequest,
  PaymentVerificationResponse,
  RazorpayOrder,
  TransactionDetail,
} from '../types';

export const paymentService = {
  /**
   * Propose a payment intent with bounded safety checks.
   */
  async proposePayment(
    orderId: number,
    merchantId: number = 1,
    idempotencyKey?: string
  ): Promise<PaymentIntent> {
    return request<PaymentIntent>('/ai/payments/propose', {
      method: 'POST',
      body: JSON.stringify({
        order_id: orderId,
        merchant_id: merchantId,
        idempotency_key: idempotencyKey,
      }),
    });
  },

  /**
   * Retrieve payment intent details and explainability breakdown.
   */
  async getPaymentIntent(intentId: number): Promise<PaymentIntent> {
    return request<PaymentIntent>(`/ai/payments/${intentId}`);
  },

  /**
   * Explicit Merchant / User Approval Gate -> Creates Razorpay Test Order.
   */
  async approvePayment(
    intentId: number,
    reviewedBy: string = 'Merchant Owner / User',
    reason: string = 'Authorized by merchant'
  ): Promise<RazorpayOrder> {
    return request<RazorpayOrder>(`/ai/payments/${intentId}/approve`, {
      method: 'POST',
      body: JSON.stringify({
        reviewed_by: reviewedBy,
        reason: reason,
      }),
    });
  },

  /**
   * Explicit Rejection of payment proposal.
   */
  async rejectPayment(
    intentId: number,
    reviewedBy: string = 'Merchant Owner / User',
    reason: string = 'Rejected by merchant'
  ): Promise<PaymentIntent> {
    return request<PaymentIntent>(`/ai/payments/${intentId}/reject`, {
      method: 'POST',
      body: JSON.stringify({
        reviewed_by: reviewedBy,
        reason: reason,
      }),
    });
  },

  /**
   * Submit Razorpay payment signature for cryptographic verification and capture.
   */
  async verifyPayment(req: PaymentVerificationRequest): Promise<PaymentVerificationResponse> {
    return request<PaymentVerificationResponse>('/payments/verify', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  /**
   * Simulate a payment failure in Razorpay test mode.
   */
  async simulateFailure(
    intentId: number,
    reason: string = 'Test-Mode Simulated Card Decline'
  ): Promise<Payment> {
    return request<Payment>(
      `/payments/simulate-failure?payment_intent_id=${intentId}&failure_reason=${encodeURIComponent(
        reason
      )}`,
      { method: 'POST' }
    );
  },

  /**
   * List all payment transactions for a merchant.
   */
  async listPayments(merchantId: number = 1, limit: number = 50): Promise<Payment[]> {
    return request<Payment[]>(`/payments?merchant_id=${merchantId}&limit=${limit}`);
  },

  /**
   * Retrieve full explainable transaction detail and decision chain.
   */
  async getTransactionDetail(paymentId: number): Promise<TransactionDetail> {
    return request<TransactionDetail>(`/payments/${paymentId}/detail`);
  },
};
