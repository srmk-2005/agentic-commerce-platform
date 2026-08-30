import React, { useEffect, useState } from 'react';
import { ActorType, AuditLog, Merchant } from '../types';
import { auditService } from '../services/auditService';
import { History, RefreshCw, Bot, User, Cpu } from 'lucide-react';

interface AuditPageProps {
  currentMerchant: Merchant | null;
}

export const AuditPage: React.FC<AuditPageProps> = ({ currentMerchant }) => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [actorFilter, setActorFilter] = useState<ActorType | 'ALL'>('ALL');

  const fetchLogs = async () => {
    if (!currentMerchant) return;
    try {
      setLoading(true);
      const data = await auditService.getLogs({
        merchant_id: currentMerchant.id,
        limit: 100,
      });
      setLogs(data);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [currentMerchant]);

  const filteredLogs = actorFilter === 'ALL' ? logs : logs.filter((l) => l.actor_type === actorFilter);

  const getActorBadge = (actor: ActorType) => {
    switch (actor) {
      case 'AI_AGENT':
        return { icon: <Bot size={13} />, color: '#818cf8', bg: 'rgba(99, 102, 241, 0.15)', label: 'AI AGENT' };
      case 'MERCHANT':
        return { icon: <User size={13} />, color: '#34d399', bg: 'rgba(16, 185, 129, 0.15)', label: 'MERCHANT' };
      case 'SYSTEM':
        return { icon: <Cpu size={13} />, color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.15)', label: 'SYSTEM' };
      default:
        return { icon: <Bot size={13} />, color: '#cbd5e1', bg: 'rgba(148, 163, 184, 0.15)', label: actor };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div
        className="glass-card"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          padding: '20px 24px',
          background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%)',
          borderColor: 'rgba(168, 85, 247, 0.25)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #9333EA 0%, #6366F1 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <History size={24} color="white" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Audit Trail & Execution Ledger
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Immutable record of agent recommendations, safety evaluations, merchant decisions, and campaign activations.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={fetchLogs}
          disabled={loading}
          style={{ gap: '6px' }}
        >
          <RefreshCw size={14} className={loading ? 'spinning' : ''} /> Refresh
        </button>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
        {[
          { label: 'All Actors', value: 'ALL' },
          { label: 'AI Agent Actions', value: 'AI_AGENT' },
          { label: 'Merchant Decisions', value: 'MERCHANT' },
          { label: 'System Executions', value: 'SYSTEM' },
        ].map((tab) => (
          <button
            key={tab.value}
            type="button"
            className={`btn btn-sm ${actorFilter === tab.value ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActorFilter(tab.value as any)}
            style={{ borderRadius: '8px' }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Audit Table */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Target Entity</th>
                <th>Status</th>
                <th>Details / Reason</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '32px' }}>
                    <RefreshCw size={20} className="spinning" style={{ margin: '0 auto 8px' }} />
                    Loading audit trail...
                  </td>
                </tr>
              ) : filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '36px', color: 'var(--text-dim)' }}>
                    No audit records found.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => {
                  const actor = getActorBadge(log.actor_type);
                  const isSuccess = log.status === 'SUCCESS' || log.status === 'APPROVED' || log.status === 'EXECUTED';
                  const isFailed = log.status === 'FAILED';

                  return (
                    <tr key={log.id}>
                      <td className="mono" style={{ fontSize: '0.775rem', color: 'var(--text-dim)', whiteSpace: 'nowrap' }}>
                        {new Date(log.created_at).toLocaleTimeString('en-IN', {
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                        })}
                      </td>

                      <td>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            padding: '2px 8px',
                            borderRadius: '4px',
                            background: actor.bg,
                            color: actor.color,
                          }}
                        >
                          {actor.icon}
                          {actor.label}
                        </span>
                      </td>

                      <td style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.85rem' }}>
                        {log.action}
                      </td>

                      <td style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                        {log.entity_type ? `${log.entity_type} #${log.entity_id || ''}` : '—'}
                      </td>

                      <td>
                        <span
                          style={{
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            padding: '2px 8px',
                            borderRadius: '4px',
                            background: isSuccess
                              ? 'rgba(16, 185, 129, 0.15)'
                              : isFailed
                              ? 'rgba(239, 68, 68, 0.15)'
                              : 'rgba(245, 158, 11, 0.15)',
                            color: isSuccess ? '#34d399' : isFailed ? '#fca5a5' : '#fbbf24',
                          }}
                        >
                          {log.status}
                        </span>
                      </td>

                      <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)', maxWidth: '320px' }}>
                        {log.reason || log.metadata_json || 'Completed'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
