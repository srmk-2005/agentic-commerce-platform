import React, { useEffect, useState } from 'react';
import { Approval, ApprovalStatus, Merchant } from '../types';
import { approvalService } from '../services/approvalService';
import { ApprovalCard } from '../components/ApprovalCard';
import { ShieldCheck, CheckCircle2, Clock, XCircle, RefreshCw, AlertCircle } from 'lucide-react';

interface ApprovalsPageProps {
  currentMerchant: Merchant | null;
}

export const ApprovalsPage: React.FC<ApprovalsPageProps> = ({ currentMerchant }) => {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<ApprovalStatus | 'ALL'>('PENDING');
  const [notice, setNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchApprovals = async () => {
    if (!currentMerchant) return;
    try {
      setLoading(true);
      const data = await approvalService.getApprovals({
        merchant_id: currentMerchant.id,
        status: statusFilter === 'ALL' ? undefined : statusFilter,
      });
      setApprovals(data);
    } catch (err) {
      console.error('Failed to load approvals:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, [currentMerchant, statusFilter]);

  const handleApprove = async (approvalId: number) => {
    try {
      const res = await approvalService.approve(approvalId, 'Merchant Owner');
      setNotice({ type: 'success', message: res.message || `Approval #${approvalId} executed successfully.` });
      fetchApprovals();
    } catch (err: any) {
      setNotice({ type: 'error', message: err.message || 'Approval execution failed.' });
    }
  };

  const handleReject = async (approvalId: number, reason?: string) => {
    try {
      const res = await approvalService.reject(approvalId, reason, 'Merchant Owner');
      setNotice({ type: 'success', message: res.message || `Approval #${approvalId} rejected.` });
      fetchApprovals();
    } catch (err: any) {
      setNotice({ type: 'error', message: err.message || 'Failed to reject action.' });
    }
  };

  const handleSimulateFailure = async (approvalId: number) => {
    try {
      await approvalService.simulateFailure(approvalId, 'Merchant Owner');
    } catch (err: any) {
      setNotice({
        type: 'error',
        message: `Simulated Failure Demonstrated: ${err.message}. Zero financial transactions were attempted.`,
      });
      fetchApprovals();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner */}
      <div
        className="glass-card"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          padding: '20px 24px',
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(16, 185, 129, 0.08) 100%)',
          borderColor: 'rgba(99, 102, 241, 0.3)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #6366F1 0%, #10B981 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShieldCheck size={26} color="white" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Merchant Approval Queue
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Human-in-the-loop control for AI growth proposals, bundles, and discount campaigns.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={fetchApprovals}
          disabled={loading}
          style={{ gap: '6px' }}
        >
          <RefreshCw size={14} className={loading ? 'spinning' : ''} /> Refresh
        </button>
      </div>

      {/* Notification Banner */}
      {notice && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            borderRadius: '10px',
            fontSize: '0.875rem',
            background: notice.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${notice.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            color: notice.type === 'success' ? '#6ee7b7' : '#fca5a5',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {notice.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
            <span>{notice.message}</span>
          </div>
          <button
            type="button"
            onClick={() => setNotice(null)}
            style={{ background: 'transparent', border: 'none', color: 'inherit', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
        {[
          { label: 'Pending Review', value: 'PENDING', icon: <Clock size={14} /> },
          { label: 'Approved & Active', value: 'APPROVED', icon: <CheckCircle2 size={14} /> },
          { label: 'Rejected', value: 'REJECTED', icon: <XCircle size={14} /> },
          { label: 'All History', value: 'ALL', icon: <ShieldCheck size={14} /> },
        ].map((tab) => (
          <button
            key={tab.value}
            type="button"
            className={`btn btn-sm ${statusFilter === tab.value ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setStatusFilter(tab.value as any)}
            style={{ gap: '6px', borderRadius: '8px' }}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Approval List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
            <RefreshCw size={24} className="spinning" style={{ margin: '0 auto 12px' }} />
            <div>Loading approval requests...</div>
          </div>
        ) : approvals.length === 0 ? (
          <div
            className="glass-card"
            style={{ textAlign: 'center', padding: '48px 24px', color: 'var(--text-muted)' }}
          >
            <ShieldCheck size={36} color="#6366F1" style={{ margin: '0 auto 12px', opacity: 0.7 }} />
            <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)' }}>
              No approvals found in this view
            </h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginTop: '4px' }}>
              When the AI assistant identifies high-confidence revenue opportunities, structured proposals will appear here for merchant consent.
            </p>
          </div>
        ) : (
          approvals.map((appr) => (
            <ApprovalCard
              key={appr.id}
              approval={appr}
              onApprove={handleApprove}
              onReject={handleReject}
              onSimulateFailure={handleSimulateFailure}
            />
          ))
        )}
      </div>
    </div>
  );
};
