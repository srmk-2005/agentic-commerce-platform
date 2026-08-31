import React, { useEffect, useState } from 'react';
import { AIMerchantManifest, AIMerchantProfile, AuditLog, Merchant } from '../types';
import { commerceService } from '../services/commerceService';
import { auditService } from '../services/auditService';
import {
  CheckCircle2,
  Clock,
  Code,
  Copy,
  Cpu,
  Globe,
  History,
  Layers,
  RefreshCw,
  Search,
  ShieldCheck,
  ShoppingBag,
  Zap,
} from 'lucide-react';

interface AiCommercePageProps {
  currentMerchant: Merchant | null;
}

export const AiCommercePage: React.FC<AiCommercePageProps> = ({ currentMerchant }) => {
  const [manifest, setManifest] = useState<AIMerchantManifest | null>(null);
  const [profile, setProfile] = useState<AIMerchantProfile | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [jsonView, setJsonView] = useState(false);
  const [copied, setCopied] = useState(false);

  const fetchData = async () => {
    if (!currentMerchant) return;
    try {
      setLoading(true);
      const [manData, profData, logData] = await Promise.all([
        commerceService.getManifest(currentMerchant.id),
        commerceService.getProfile(currentMerchant.id),
        auditService.getLogs({ merchant_id: currentMerchant.id, limit: 25 }),
      ]);
      setManifest(manData);
      setProfile(profData);
      setLogs(logData.filter((l) => l.actor_type === 'AI_BUYER'));
    } catch (err) {
      console.error('Failed to load AI commerce data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [currentMerchant]);

  const handleCopyManifest = () => {
    if (manifest) {
      navigator.clipboard.writeText(JSON.stringify(manifest, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const capabilities = [
    { name: 'Machine-Readable Catalog', key: 'catalog', status: 'AVAILABLE', icon: <Layers size={18} />, endpoint: '/api/v1/ai/catalog' },
    { name: 'Deterministic Ranked Search', key: 'search', status: 'AVAILABLE', icon: <Search size={18} />, endpoint: '/api/v1/ai/search' },
    { name: 'Ground-Truth Product Specs', key: 'product_details', status: 'AVAILABLE', icon: <Cpu size={18} />, endpoint: '/api/v1/ai/products/{id}' },
    { name: 'Real-Time Inventory Availability', key: 'inventory', status: 'AVAILABLE', icon: <ShieldCheck size={18} />, endpoint: '/api/v1/ai/products/{id}' },
    { name: 'AI Order Creation & Idempotency', key: 'order_creation', status: 'AVAILABLE', icon: <ShoppingBag size={18} />, endpoint: '/api/v1/ai/orders' },
    { name: 'Payment Simulation (Razorpay)', key: 'payment', status: 'COMING_PHASE_5', icon: <Clock size={18} />, endpoint: 'Phase 5' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
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
          background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.12) 0%, rgba(99, 102, 241, 0.08) 100%)',
          borderColor: 'rgba(14, 165, 233, 0.3)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #0284C7 0%, #6366F1 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Globe size={26} color="white" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>
                AI Commerce Readiness & Manifest
              </h2>
              <span
                className="badge-tag"
                style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)' }}
              >
                <Zap size={12} /> Agent-Readable v1.0
              </span>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Structured endpoints enabling autonomous AI buyers to discover catalog items, query live stock, and prepare orders.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setJsonView(!jsonView)}
            style={{ gap: '6px' }}
          >
            <Code size={14} /> {jsonView ? 'Cards View' : 'Raw JSON'}
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={fetchData}
            disabled={loading}
            style={{ gap: '6px' }}
          >
            <RefreshCw size={14} className={loading ? 'spinning' : ''} /> Refresh
          </button>
        </div>
      </div>

      {/* Capabilities Readiness Matrix */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>
          Merchant Capability Checklist
        </h3>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '14px',
          }}
        >
          {capabilities.map((cap) => {
            const isAvailable = cap.status === 'AVAILABLE';
            return (
              <div
                key={cap.key}
                className="glass-card"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  padding: '16px 18px',
                  background: isAvailable ? 'rgba(15, 23, 42, 0.8)' : 'rgba(30, 41, 59, 0.4)',
                  borderColor: isAvailable ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: isAvailable ? '#38bdf8' : '#fbbf24' }}>
                    {cap.icon}
                    <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.9rem' }}>
                      {cap.name}
                    </span>
                  </div>
                  {isAvailable ? (
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '0.7rem',
                        fontWeight: 800,
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: 'rgba(16, 185, 129, 0.15)',
                        color: '#34d399',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                      }}
                    >
                      <CheckCircle2 size={12} /> AVAILABLE
                    </span>
                  ) : (
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '0.7rem',
                        fontWeight: 800,
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: 'rgba(245, 158, 11, 0.15)',
                        color: '#fbbf24',
                        border: '1px solid rgba(245, 158, 11, 0.3)',
                      }}
                    >
                      <Clock size={12} /> PHASE 5
                    </span>
                  )}
                </div>
                <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                  Endpoint: {cap.endpoint}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Manifest Viewer */}
      {jsonView ? (
        <div className="glass-card" style={{ padding: '20px', position: 'relative' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#818cf8' }}>
              Machine-Readable Discovery Manifest (GET /api/v1/ai/merchant/{currentMerchant?.id}/manifest)
            </h4>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={handleCopyManifest}
              style={{ gap: '6px', fontSize: '0.75rem' }}
            >
              <Copy size={13} /> {copied ? 'Copied!' : 'Copy JSON'}
            </button>
          </div>
          <pre
            className="mono"
            style={{
              padding: '16px',
              borderRadius: '8px',
              background: '#090d16',
              color: '#38bdf8',
              fontSize: '0.8rem',
              overflowX: 'auto',
              maxHeight: '340px',
            }}
          >
            {JSON.stringify(manifest, null, 2)}
          </pre>
        </div>
      ) : (
        profile && (
          <div
            className="glass-card"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
              padding: '20px',
            }}
          >
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                Store Categories
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                {profile.categories.map((cat) => (
                  <span
                    key={cat}
                    style={{
                      fontSize: '0.75rem',
                      padding: '3px 8px',
                      borderRadius: '6px',
                      background: 'rgba(99, 102, 241, 0.15)',
                      color: '#a5b4fc',
                    }}
                  >
                    {cat}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                Base Currency
              </div>
              <div className="mono" style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '4px' }}>
                {profile.currency}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                AI Protocol Compatibility
              </div>
              <div style={{ fontSize: '0.85rem', color: '#34d399', fontWeight: 600, marginTop: '4px' }}>
                ✓ Manifest v1.0 Ready
              </div>
            </div>
          </div>
        )
      )}

      {/* Live AI Commerce Activity Ledger */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '16px 20px',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <History size={18} color="#818cf8" />
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>
              External AI Buyer Activity Stream
            </h3>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Immutable audit logs for actor <strong>AI_BUYER</strong>
          </span>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Action</th>
                <th>Target Entity</th>
                <th>Status</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-dim)' }}>
                    No AI Buyer interactions logged yet. Open the AI Buyer simulator to generate live agent activity.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id}>
                    <td className="mono" style={{ fontSize: '0.775rem', color: 'var(--text-dim)' }}>
                      {new Date(log.created_at).toLocaleTimeString('en-IN', {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: '0.725rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: 'rgba(56, 189, 248, 0.15)',
                          color: '#38bdf8',
                        }}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-main)' }}>
                      {log.entity_type ? `${log.entity_type} #${log.entity_id || ''}` : 'Catalog / Manifest'}
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: '0.725rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: 'rgba(16, 185, 129, 0.15)',
                          color: '#34d399',
                        }}
                      >
                        {log.status}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)', maxWidth: '340px' }}>
                      {log.reason || log.metadata_json || 'Executed'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
