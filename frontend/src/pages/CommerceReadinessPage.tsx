import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  RefreshCw,
  Sparkles,
  XCircle,
} from 'lucide-react';
import { agentCommerceService } from '../services/agentCommerceService';
import type { CommerceReadinessResponse, Merchant } from '../types';

interface CommerceReadinessPageProps {
  currentMerchant: Merchant | null;
}

export const CommerceReadinessPage: React.FC<CommerceReadinessPageProps> = ({ currentMerchant }) => {
  const [readiness, setReadiness] = useState<CommerceReadinessResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadReadiness();
  }, [currentMerchant]);

  const loadReadiness = async () => {
    try {
      setLoading(true);
      const data = await agentCommerceService.getReadiness(currentMerchant?.id || 1);
      setReadiness(data);
    } catch (err) {
      console.error('Failed to load readiness score:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Banner */}
      <div
        className="glass-card"
        style={{
          padding: '24px',
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Sparkles size={22} color="#ffffff" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-main)' }}>
              AI Commerce Readiness Score
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Mathematical capability verification for autonomous AI buyer discoverability and ordering.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="btn btn-outline"
          onClick={loadReadiness}
          disabled={loading}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px' }}
        >
          <RefreshCw size={15} className={loading ? 'spinning' : ''} /> Refresh Audit
        </button>
      </div>

      {/* Score Summary Card */}
      {readiness && (
        <div
          className="glass-card"
          style={{
            padding: '28px',
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(15, 23, 42, 0.7) 100%)',
            border: `1px solid ${readiness.is_ready ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '20px',
          }}
        >
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Merchant: {readiness.merchant_name}
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: 900, color: readiness.is_ready ? '#34D399' : '#fbbf24', marginTop: '4px' }}>
              {readiness.readiness_score}%
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Status:{' '}
              <strong style={{ color: readiness.is_ready ? '#34D399' : '#fbbf24' }}>
                {readiness.is_ready ? 'FULLY AI-COMMERCE READY' : 'ACTION REQUIRED'}
              </strong>
            </div>
          </div>

          <div
            style={{
              padding: '16px 20px',
              borderRadius: '12px',
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--border-subtle)',
              maxWidth: '420px',
            }}
          >
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '6px' }}>
              Deterministic Scoring Formula
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: '1.4', margin: 0 }}>
              Readiness is derived from active catalog products (20%), ranked search (15%), structured SKUs (15%), inventory tracking (15%), order APIs (15%), test payments (10%), policy caps (5%), and audit ledger (5%).
            </p>
          </div>
        </div>
      )}

      {/* Weighted Capability Checklist */}
      {readiness && (
        <div
          className="glass-card"
          style={{
            padding: '24px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '16px' }}>
            Capability Verification Checklist
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {readiness.checklist.map((item, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  background: item.passed ? 'rgba(16, 185, 129, 0.03)' : 'rgba(239, 68, 68, 0.04)',
                  border: `1px solid ${item.passed ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.25)'}`,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {item.passed ? <CheckCircle2 size={20} color="#10B981" /> : <XCircle size={20} color="#EF4444" />}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-main)' }}>
                        {item.name}
                      </span>
                      <span
                        style={{
                          fontSize: '0.675rem',
                          fontWeight: 700,
                          padding: '1px 6px',
                          borderRadius: '6px',
                          background: 'rgba(255, 255, 255, 0.05)',
                          color: 'var(--text-dim)',
                        }}
                      >
                        {item.category}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.775rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {item.details}
                    </div>
                  </div>
                </div>

                <div className="mono" style={{ fontSize: '0.85rem', fontWeight: 800, color: item.passed ? '#34D399' : 'var(--text-dim)' }}>
                  +{item.weight}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
