import React, { useState, useEffect } from 'react';
import {
  CreditCard,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
  Layers,
} from 'lucide-react';
import { paymentService } from '../services/paymentService';
import type { Payment, TransactionDetail } from '../types';

export const TransactionsPage: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filter, setFilter] = useState<string>('ALL');
  const [selectedTxDetail, setSelectedTxDetail] = useState<TransactionDetail | null>(null);

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    setLoading(true);
    try {
      const data = await paymentService.listPayments(1, 50);
      setPayments(data);
    } catch (err) {
      console.error('Failed to load transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDetail = async (paymentId: number) => {
    try {
      const detail = await paymentService.getTransactionDetail(paymentId);
      setSelectedTxDetail(detail);
    } catch (err) {
      console.error('Failed to load transaction detail:', err);
    }
  };

  const filteredPayments = payments.filter((p) => {
    if (filter === 'ALL') return true;
    return p.status === filter;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'CAPTURED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
            <CheckCircle className="w-3 h-3 mr-1" /> CAPTURED (PAID)
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-400 border border-rose-800/60">
            <XCircle className="w-3 h-3 mr-1" /> FAILED
          </span>
        );
      case 'PENDING':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-400 border border-amber-800/60">
            <Clock className="w-3 h-3 mr-1" /> PENDING
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Phase 5: Financial Ledger
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Razorpay Test Mode Verified
            </span>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <CreditCard className="w-8 h-8 text-emerald-400" />
            Transaction Ledger & Decision Chains
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Auditable, explainable record of every AI-initiated payment intent and Razorpay verification.
          </p>
        </div>

        {/* Filter Buttons */}
        <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1 gap-1">
          {['ALL', 'CAPTURED', 'FAILED', 'PENDING'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                filter === f
                  ? 'bg-emerald-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-slate-400 space-y-3">
            <Activity className="w-8 h-8 text-indigo-500 animate-spin mx-auto" />
            <p className="text-sm">Loading transactions...</p>
          </div>
        ) : filteredPayments.length === 0 ? (
          <div className="p-12 text-center text-slate-400 space-y-3">
            <CreditCard className="w-12 h-12 text-slate-600 mx-auto" />
            <h3 className="text-base font-bold text-white">No Transactions Found</h3>
            <p className="text-xs">
              Simulate an order and approve a payment to generate transactions.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-4 px-6">Payment ID</th>
                  <th className="py-4 px-6">Order ID</th>
                  <th className="py-4 px-6">Amount</th>
                  <th className="py-4 px-6">Status</th>
                  <th className="py-4 px-6">Method</th>
                  <th className="py-4 px-6">Razorpay Order</th>
                  <th className="py-4 px-6">Timestamp</th>
                  <th className="py-4 px-6 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {filteredPayments.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-4 px-6 font-mono font-semibold text-white">
                      #{p.id}
                    </td>
                    <td className="py-4 px-6 font-mono text-indigo-400">
                      Order #{p.order_id}
                    </td>
                    <td className="py-4 px-6 font-bold text-emerald-400 text-sm">
                      ₹{p.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-4 px-6">{getStatusBadge(p.status)}</td>
                    <td className="py-4 px-6 text-slate-300 font-mono text-[11px]">
                      {p.payment_method}
                    </td>
                    <td className="py-4 px-6 font-mono text-slate-400 truncate max-w-[140px]">
                      {p.razorpay_order_id || '—'}
                    </td>
                    <td className="py-4 px-6 text-slate-400">
                      {new Date(p.created_at).toLocaleString()}
                    </td>
                    <td className="py-4 px-6 text-right">
                      <button
                        onClick={() => handleOpenDetail(p.id)}
                        className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 font-semibold transition border border-indigo-500/30 text-[11px] cursor-pointer"
                      >
                        Explain Decision →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Decision Chain & Transaction Explainability Modal */}
      {selectedTxDetail && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 shadow-2xl space-y-6 animate-scale-in">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Explainable Decision Chain
                </span>
                <h3 className="text-lg font-bold text-white flex items-center gap-2 mt-0.5">
                  Transaction #{selectedTxDetail.payment.id} Detail
                </h3>
              </div>
              <button
                onClick={() => setSelectedTxDetail(null)}
                className="text-slate-400 hover:text-white text-xs font-semibold"
              >
                ✕ Close
              </button>
            </div>

            {/* Financial Overview */}
            <div className="grid grid-cols-3 gap-3 p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs">
              <div>
                <span className="text-slate-400 block font-medium">Order Total</span>
                <span className="text-emerald-400 font-extrabold text-base">
                  ₹{selectedTxDetail.payment.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block font-medium">Status</span>
                <span className="font-semibold text-white">{selectedTxDetail.payment.status}</span>
              </div>
              <div>
                <span className="text-slate-400 block font-medium">Razorpay Order</span>
                <span className="font-mono text-slate-300 text-[11px] truncate block">
                  {selectedTxDetail.payment.razorpay_order_id || 'N/A'}
                </span>
              </div>
            </div>

            {/* Decision Narrative Chain */}
            <div className="space-y-3">
              <h4 className="text-xs uppercase tracking-wider text-indigo-400 font-bold flex items-center gap-2">
                <Layers className="w-4 h-4" />
                Step-by-Step Decision Rationale
              </h4>
              <div className="space-y-2">
                {selectedTxDetail.decision_chain.map((step, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs text-slate-200 flex items-start gap-2.5"
                  >
                    <div className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                      {idx + 1}
                    </div>
                    <span className="leading-relaxed">{step}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Related Order Items */}
            {selectedTxDetail.order?.items && selectedTxDetail.order.items.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <h4 className="text-xs uppercase tracking-wider text-slate-400 font-bold">
                  Order Items
                </h4>
                <div className="space-y-1.5">
                  {selectedTxDetail.order.items.map((item: any, idx: number) => (
                    <div
                      key={idx}
                      className="flex justify-between p-2 rounded-lg bg-slate-950/40 text-xs text-slate-300"
                    >
                      <span>{item.quantity}x {item.name}</span>
                      <span className="font-semibold text-white">
                        ₹{(item.quantity * item.unit_price).toLocaleString('en-IN')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
