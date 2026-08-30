import React, { useState } from 'react';
import { Approval } from '../types';
import {
  CheckCircle,
  XCircle,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Check,
  X,
  RefreshCw,
} from 'lucide-react';

interface ApprovalCardProps {
  approval: Approval;
  onApprove: (approvalId: number) => Promise<void>;
  onReject: (approvalId: number, reason?: string) => Promise<void>;
  onSimulateFailure: (approvalId: number) => Promise<void>;
}

export const ApprovalCard: React.FC<ApprovalCardProps> = ({
  approval,
  onApprove,
  onReject,
  onSimulateFailure,
}) => {
  const [loading, setLoading] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  const meta = approval.metadata_parsed || {};
  const isPending = approval.status === 'PENDING';
  const isApproved = approval.status === 'APPROVED';
  const isRejected = approval.status === 'REJECTED';

  const handleApprove = async () => {
    try {
      setLoading(true);
      await onApprove(approval.id);
    } finally {
      setLoading(false);
    }
  };

  const handleRejectConfirm = async () => {
    try {
      setLoading(true);
      await onReject(approval.id, rejectReason || undefined);
      setRejecting(false);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateFail = async () => {
    try {
      setLoading(true);
      await onSimulateFailure(approval.id);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="glass-card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        padding: '22px',
        background: isPending
          ? 'rgba(15, 23, 42, 0.85)'
          : isApproved
          ? 'rgba(16, 185, 129, 0.04)'
          : 'rgba(239, 68, 68, 0.04)',
        borderColor: isPending
          ? 'rgba(99, 102, 241, 0.3)'
          : isApproved
          ? 'rgba(16, 185, 129, 0.3)'
          : 'rgba(239, 68, 68, 0.3)',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 800,
                textTransform: 'uppercase',
                padding: '3px 8px',
                borderRadius: '6px',
                background: 'rgba(99, 102, 241, 0.15)',
                color: '#a5b4fc',
              }}
            >
              {approval.action_type.replace(/_/g, ' ')}
            </span>
            <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
              Request #{approval.id}
            </span>
          </div>

          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '6px' }}>
            {meta.title || approval.reason || 'AI Growth Action'}
          </h3>
        </div>

        {/* Status Badge */}
        <div>
          {isPending && (
            <span
              className="badge-tag"
              style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.3)' }}
            >
              <Clock size={13} /> Requires Merchant Approval
            </span>
          )}
          {isApproved && (
            <span
              className="badge-tag"
              style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#6ee7b7', border: '1px solid rgba(16, 185, 129, 0.3)' }}
            >
              <CheckCircle size={13} /> Approved & Executed
            </span>
          )}
          {isRejected && (
            <span
              className="badge-tag"
              style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5', border: '1px solid rgba(239, 68, 68, 0.3)' }}
            >
              <XCircle size={13} /> Rejected
            </span>
          )}
        </div>
      </div>

      {/* Target Products & Terms Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
          padding: '14px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
            Associated Products
          </div>
          <div style={{ fontWeight: 600, color: 'var(--text-main)', marginTop: '2px', fontSize: '0.875rem' }}>
            {meta.target_product_names?.join(' + ') || meta.products?.join(' + ') || 'Target Catalog Products'}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
            Proposed Discount
          </div>
          <div className="mono" style={{ fontWeight: 700, color: '#38bdf8', marginTop: '2px', fontSize: '0.95rem' }}>
            {meta.discount_value}% OFF ({meta.campaign_duration_days || meta.duration_days || 7} Days)
          </div>
        </div>

        {meta.original_bundle_price !== undefined && meta.discounted_bundle_price !== undefined && (
          <div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Final Bundle Pricing
            </div>
            <div className="mono" style={{ fontWeight: 700, color: '#34d399', marginTop: '2px', fontSize: '0.95rem' }}>
              ₹{meta.discounted_bundle_price.toLocaleString()}{' '}
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textDecoration: 'line-through' }}>
                ₹{meta.original_bundle_price.toLocaleString()}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Strategic Reason & Objective */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#818cf8', textTransform: 'uppercase' }}>
            Strategic Why & Data Grounding:
          </span>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginTop: '2px', lineHeight: '1.4' }}>
            {approval.reason || meta.description || 'Action proposed by merchant AI analysis.'}
          </p>
        </div>

        {meta.expected_benefit && (
          <div>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#34d399', textTransform: 'uppercase' }}>
              Expected Goal:
            </span>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              {meta.expected_benefit}
            </p>
          </div>
        )}
      </div>

      {/* Deterministic Safety Verification Checklist */}
      <div
        style={{
          padding: '12px 14px',
          background: 'rgba(16, 185, 129, 0.03)',
          borderRadius: '8px',
          border: '1px solid rgba(16, 185, 129, 0.15)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 700, color: '#6ee7b7', textTransform: 'uppercase', marginBottom: '8px' }}>
          <ShieldCheck size={14} /> Backend Safety Policy Checks
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '6px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Check size={14} color="#10B981" /> Discount within merchant limit (≤ 20%)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Check size={14} color="#10B981" /> Products belong to this merchant
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Check size={14} color="#10B981" /> Products active with stock
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Check size={14} color="#10B981" /> Duration within limit (≤ 30 days)
          </div>
        </div>
      </div>

      {/* Rejection Details if rejected */}
      {isRejected && approval.reason && (
        <div style={{ padding: '10px 14px', background: 'rgba(239, 68, 68, 0.08)', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.8rem', color: '#fca5a5' }}>
          <strong>Rejection Reason:</strong> {approval.reason}
        </div>
      )}

      {/* Reviewer & Timestamp metadata */}
      {!isPending && approval.reviewed_at && (
        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
          Reviewed by <strong>{approval.reviewed_by || 'Merchant Owner'}</strong> on{' '}
          {new Date(approval.reviewed_at).toLocaleString()}
        </div>
      )}

      {/* Action Buttons for Pending Approvals */}
      {isPending && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginTop: '6px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
          {rejecting ? (
            <div style={{ display: 'flex', gap: '8px', width: '100%', flexWrap: 'wrap' }}>
              <input
                type="text"
                className="form-input"
                placeholder="Optional reason for rejection (e.g. 'Margin too tight')..."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                style={{ flex: 1, minWidth: '220px' }}
                disabled={loading}
              />
              <button
                type="button"
                className="btn btn-danger btn-sm"
                onClick={handleRejectConfirm}
                disabled={loading}
              >
                Confirm Rejection
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setRejecting(false)}
                disabled={loading}
              >
                Cancel
              </button>
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleApprove}
                  disabled={loading}
                  style={{ gap: '6px', padding: '8px 20px', background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)' }}
                >
                  {loading ? <RefreshCw size={16} className="spinning" /> : <Check size={16} />}
                  Approve & Execute Campaign
                </button>

                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setRejecting(true)}
                  disabled={loading}
                  style={{ gap: '6px' }}
                >
                  <X size={16} /> Reject
                </button>
              </div>

              {/* Live Hackathon Demonstration: Failure Simulation */}
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={handleSimulateFail}
                disabled={loading}
                title="Test simulated transient activation failure (proves zero financial corruption)"
                style={{ fontSize: '0.75rem', color: '#fbbf24', borderColor: 'rgba(245, 158, 11, 0.3)' }}
              >
                <AlertTriangle size={13} /> Simulate Failure
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
};
