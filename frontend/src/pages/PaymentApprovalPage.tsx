import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Shield,
  CheckCircle,
  XCircle,
  AlertTriangle,
  CreditCard,
  Lock,
  Info,
  Clock,
  Activity,
} from 'lucide-react';
import { paymentService } from '../services/paymentService';
import type { PaymentIntent, RazorpayOrder } from '../types';

export const PaymentApprovalPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [intent, setIntent] = useState<PaymentIntent | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Approval & Checkout State
  const [approving, setApproving] = useState<boolean>(false);
  const [rejecting, setRejecting] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>('Unacceptable payment velocity or price');
  const [showRejectModal, setShowRejectModal] = useState<boolean>(false);

  // Razorpay Test Checkout Modal State
  const [activeRazorpayOrder, setActiveRazorpayOrder] = useState<RazorpayOrder | null>(null);
  const [isProcessingCheckout, setIsProcessingCheckout] = useState<boolean>(false);
  const [paymentSuccessData, setPaymentSuccessData] = useState<any>(null);

  useEffect(() => {
    if (id) {
      loadIntent(Number(id));
    }
  }, [id]);

  const loadIntent = async (intentId: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await paymentService.getPaymentIntent(intentId);
      setIntent(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load payment intent');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAndPay = async () => {
    if (!intent) return;
    setApproving(true);
    setError(null);
    try {
      const rzpOrder = await paymentService.approvePayment(
        intent.id,
        'Merchant Owner / User',
        'Explicit authorization from Payment Approval Gate'
      );
      setActiveRazorpayOrder(rzpOrder);
      // Reload intent to show APPROVED
      await loadIntent(intent.id);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Payment approval failed');
    } finally {
      setApproving(false);
    }
  };

  const handleReject = async () => {
    if (!intent) return;
    setRejecting(true);
    setError(null);
    try {
      const rejectedIntent = await paymentService.rejectPayment(
        intent.id,
        'Merchant Owner / User',
        rejectReason
      );
      setIntent(rejectedIntent);
      setShowRejectModal(false);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Payment rejection failed');
    } finally {
      setRejecting(false);
    }
  };

  const handleSimulateSuccessfulPayment = async () => {
    if (!activeRazorpayOrder || !intent) return;
    setIsProcessingCheckout(true);
    try {
      const mockPaymentId = `pay_test_${Math.random().toString(36).substring(2, 10)}`;
      // In test mode, our backend supports simulated signature verification
      const verifyRes = await paymentService.verifyPayment({
        payment_intent_id: intent.id,
        razorpay_order_id: activeRazorpayOrder.razorpay_order_id,
        razorpay_payment_id: mockPaymentId,
        razorpay_signature: 'mock_test_signature_valid',
      });
      setPaymentSuccessData(verifyRes);
      setActiveRazorpayOrder(null);
      await loadIntent(intent.id);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Verification failed');
    } finally {
      setIsProcessingCheckout(false);
    }
  };

  const handleSimulateBankDecline = async () => {
    if (!activeRazorpayOrder || !intent) return;
    setIsProcessingCheckout(true);
    try {
      await paymentService.simulateFailure(intent.id, 'Simulated Card Declined (Test Mode)');
      setActiveRazorpayOrder(null);
      await loadIntent(intent.id);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failure simulation error');
    } finally {
      setIsProcessingCheckout(false);
    }
  };

  const getRiskBadge = (level: string) => {
    switch (level) {
      case 'LOW':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
            <CheckCircle className="w-3 h-3 mr-1" /> Risk: LOW (≤25% limit)
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-400 border border-amber-800/60">
            <AlertTriangle className="w-3 h-3 mr-1" /> Risk: MEDIUM (25%-75% limit)
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-orange-950/80 text-orange-400 border border-orange-800/60">
            <AlertTriangle className="w-3 h-3 mr-1" /> Risk: HIGH (&gt;75% limit)
          </span>
        );
      case 'BLOCKED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-red-950/80 text-red-400 border border-red-800/60">
            <XCircle className="w-3 h-3 mr-1" /> Risk: BLOCKED (Exceeds Policy)
          </span>
        );
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING_APPROVAL':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Clock className="w-3.5 h-3.5 mr-1 animate-pulse" /> Awaiting Human Approval
          </span>
        );
      case 'APPROVED':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <CheckCircle className="w-3.5 h-3.5 mr-1" /> Approved & Checkout Created
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle className="w-3.5 h-3.5 mr-1" /> Payment Captured (PAID)
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
            <XCircle className="w-3.5 h-3.5 mr-1" /> Rejected by Merchant
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3.5 h-3.5 mr-1" /> Payment Failed
          </span>
        );
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <Activity className="w-10 h-10 text-indigo-500 animate-spin mx-auto" />
          <p className="text-slate-400 text-sm">Evaluating payment safety bounds...</p>
        </div>
      </div>
    );
  }

  if (error || !intent) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="bg-red-950/40 border border-red-800/60 p-6 rounded-2xl text-center space-y-4">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto" />
          <h2 className="text-xl font-bold text-white">Payment Proposal Error</h2>
          <p className="text-slate-300 text-sm">{error || 'Payment intent could not be loaded.'}</p>
          <div className="pt-2">
            <button
              onClick={() => navigate('/buyer')}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium transition"
            >
              ← Return to AI Buyer Simulator
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Phase 5: Razorpay Test Mode
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Zero Production Money Movement
            </span>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <Shield className="w-8 h-8 text-emerald-400" />
            Payment Approval & Explainability Gate
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Every money action is explainable, bounded and gated before any test payment execution.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {getStatusBadge(intent.status)}
          {getRiskBadge(intent.risk_level)}
        </div>
      </div>

      {/* Main Approval Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Core Financial Proposal & Safety Ledger */}
        <div className="lg:col-span-2 space-y-6">
          {/* Financial Breakdown Card */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-2xl -mr-10 -mt-10" />

            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Proposal Reference
                </span>
                <h3 className="text-lg font-bold text-white flex items-center gap-2 mt-0.5">
                  Payment Intent #{intent.id}
                  <span className="text-xs font-normal text-slate-400">
                    for Order #{intent.order_id}
                  </span>
                </h3>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Requested Amount
                </span>
                <div className="text-2xl font-extrabold text-emerald-400">
                  ₹{intent.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  <span className="text-xs font-semibold text-slate-400 ml-1.5">
                    {intent.currency}
                  </span>
                </div>
              </div>
            </div>

            {/* Explainability Narrative */}
            <div className="mt-5 p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
              <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider">
                <Info className="w-4 h-4" /> Why this payment is permitted
              </div>
              <p className="text-slate-200 text-sm leading-relaxed font-sans">
                {intent.explainability || intent.reason}
              </p>
            </div>

            {/* Bounded Limits & Policy Details */}
            {intent.policy_check && (
              <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-800/60">
                <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/40">
                  <span className="text-[11px] text-slate-400 block font-medium">Single Limit</span>
                  <span className="text-sm font-semibold text-white">
                    ₹{intent.policy_check.max_transaction_limit.toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/40">
                  <span className="text-[11px] text-slate-400 block font-medium">Daily Limit</span>
                  <span className="text-sm font-semibold text-white">
                    ₹{intent.policy_check.daily_limit.toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/40">
                  <span className="text-[11px] text-slate-400 block font-medium">Today's Spend</span>
                  <span className="text-sm font-semibold text-amber-400">
                    ₹{intent.policy_check.today_spent.toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/40">
                  <span className="text-[11px] text-slate-400 block font-medium">
                    Remaining Daily
                  </span>
                  <span className="text-sm font-semibold text-emerald-400">
                    ₹{intent.policy_check.remaining_daily_limit.toLocaleString('en-IN')}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Action Gate Section */}
          {intent.status === 'PENDING_APPROVAL' && (
            <div className="bg-gradient-to-r from-emerald-950/30 via-slate-900 to-slate-900 border border-emerald-500/30 rounded-2xl p-6 shadow-2xl space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  <Lock className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-base font-bold text-white">
                    Human-in-the-Loop Authorization Gate
                  </h4>
                  <p className="text-xs text-slate-400">
                    Autonomous money movement is strictly disabled. You must explicitly authorize
                    this charge.
                  </p>
                </div>
              </div>

              <div className="pt-3 flex flex-col sm:flex-row gap-3">
                <button
                  id="btn-approve-pay"
                  onClick={handleApproveAndPay}
                  disabled={approving}
                  className="flex-1 flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-lg shadow-emerald-950 transition active:scale-[0.98] disabled:opacity-50 cursor-pointer"
                >
                  <Lock className="w-4 h-4" />
                  {approving ? 'Creating Razorpay Order...' : 'APPROVE & PAY'}
                </button>

                <button
                  id="btn-reject-proposal"
                  onClick={() => setShowRejectModal(true)}
                  disabled={approving}
                  className="px-5 py-3.5 rounded-xl bg-slate-800 hover:bg-red-950/60 hover:text-red-300 text-slate-300 font-semibold text-sm border border-slate-700 transition active:scale-[0.98] cursor-pointer"
                >
                  Reject Proposal
                </button>
              </div>
            </div>
          )}

          {/* Successful Payment Notification */}
          {paymentSuccessData && (
            <div className="p-5 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-200 space-y-3">
              <div className="flex items-center gap-3 text-emerald-400 font-bold">
                <CheckCircle className="w-6 h-6" />
                <span>Payment Verified & Order Marked PAID!</span>
              </div>
              <p className="text-xs text-emerald-300/90 leading-relaxed">
                Cryptographic HMAC-SHA256 signature verified by the server. Razorpay payment ID:{' '}
                <code>{paymentSuccessData.payment_id}</code>. Order #{paymentSuccessData.order_id}{' '}
                has moved to <strong>PAID</strong> status.
              </p>
              <div className="pt-2 flex gap-3">
                <Link
                  to={`/transactions`}
                  className="px-4 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-semibold transition"
                >
                  View in Transactions Ledger →
                </Link>
                <Link
                  to={`/orders`}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition"
                >
                  View Order List
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Invariants & Meta */}
        <div className="space-y-6">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4">
            <h4 className="text-xs uppercase tracking-wider text-slate-400 font-bold flex items-center gap-2">
              <Shield className="w-4 h-4 text-indigo-400" />
              Safety Guarantee Invariants
            </h4>

            <ul className="space-y-3 text-xs text-slate-300">
              <li className="flex items-start gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                <span>
                  <strong>Explainable:</strong> Detailed justification is generated deterministically before charging.
                </span>
              </li>
              <li className="flex items-start gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                <span>
                  <strong>Bounded:</strong> Single payment is bounded to ₹5,000 max & ₹25,000 daily spend limit.
                </span>
              </li>
              <li className="flex items-start gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                <span>
                  <strong>Gated:</strong> Requires human authorization via explicit <code>[APPROVE & PAY]</code>.
                </span>
              </li>
              <li className="flex items-start gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                <span>
                  <strong>Secret Isolation:</strong> Razorpay secret key is kept on the server and never sent to LLM or frontend.
                </span>
              </li>
            </ul>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3 text-xs text-slate-400">
            <h4 className="text-xs uppercase tracking-wider text-slate-400 font-bold flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-500" />
              Metadata & Expiry
            </h4>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span>Proposed At:</span>
              <span className="text-slate-200">{new Date(intent.created_at).toLocaleTimeString()}</span>
            </div>
            {intent.approved_by && (
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span>Authorized By:</span>
                <span className="text-slate-200">{intent.approved_by}</span>
              </div>
            )}
            {intent.idempotency_key && (
              <div className="flex justify-between py-1">
                <span>Idempotency Key:</span>
                <span className="font-mono text-slate-300 truncate max-w-[120px]">{intent.idempotency_key}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Razorpay Test-Mode Simulated Checkout Modal */}
      {activeRazorpayOrder && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-5 animate-scale-in">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-black text-sm">
                  R
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Razorpay Test Checkout</h3>
                  <span className="text-[11px] text-blue-400 font-medium">Test Mode Simulation</span>
                </div>
              </div>
              <button
                onClick={() => setActiveRazorpayOrder(null)}
                className="text-slate-400 hover:text-white text-xs font-semibold"
              >
                ✕ Cancel
              </button>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
              <div className="flex justify-between text-slate-400">
                <span>Order ID:</span>
                <span className="font-mono text-white font-medium">{activeRazorpayOrder.razorpay_order_id}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Amount:</span>
                <span className="text-emerald-400 font-bold text-sm">
                  ₹{(activeRazorpayOrder.amount / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Smallest Unit (Paise):</span>
                <span className="font-mono text-slate-300">{activeRazorpayOrder.amount} paise</span>
              </div>
            </div>

            {/* Test Payment Simulation Details */}
            <div className="p-3.5 rounded-xl bg-blue-950/40 border border-blue-800/40 text-[11px] text-blue-300 space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-blue-200">
                <CreditCard className="w-3.5 h-3.5" /> Simulated Test Instrument
              </div>
              <div>Card: <code>4111 •••• •••• 1111</code> (Test Card)</div>
              <div>Zero live money is moved. Demonstrates HMAC signature verification.</div>
            </div>

            {/* Simulated Checkout Buttons */}
            <div className="space-y-2.5 pt-2">
              <button
                id="btn-complete-rzp-test"
                onClick={handleSimulateSuccessfulPayment}
                disabled={isProcessingCheckout}
                className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm transition shadow-lg shadow-blue-950 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {isProcessingCheckout ? 'Verifying HMAC Signature...' : 'Simulate Successful Payment'}
              </button>

              <button
                id="btn-decline-rzp-test"
                onClick={handleSimulateBankDecline}
                disabled={isProcessingCheckout}
                className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-rose-950/60 hover:text-rose-300 text-slate-400 text-xs font-semibold border border-slate-700 transition cursor-pointer disabled:opacity-50"
              >
                Simulate Bank Decline (Test Recovery)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Proposal Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <XCircle className="w-5 h-5 text-red-400" /> Reject Payment Proposal
            </h3>
            <p className="text-xs text-slate-400">
              Provide a reason for rejecting this AI payment request. It will be recorded in the immutable audit trail.
            </p>
            <div>
              <label className="text-xs text-slate-300 font-medium block mb-1.5">Rejection Reason</label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white text-xs focus:outline-none focus:border-red-500"
              />
            </div>
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleReject}
                disabled={rejecting}
                className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs transition disabled:opacity-50"
              >
                {rejecting ? 'Rejecting...' : 'Confirm Rejection'}
              </button>
              <button
                onClick={() => setShowRejectModal(false)}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
