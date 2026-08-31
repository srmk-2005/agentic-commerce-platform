import React from 'react';
import { Opportunity } from '../types';
import { ArrowUpRight, TrendingUp, Sparkles, AlertCircle, ShoppingCart, Zap, RefreshCw } from 'lucide-react';

interface OpportunityCardProps {
  opportunity: Opportunity;
  onReview: (opportunity: Opportunity) => void;
  onProposeAction?: (opportunity: Opportunity) => void;
  isProposing?: boolean;
}

export const OpportunityCard: React.FC<OpportunityCardProps> = ({
  opportunity,
  onReview,
  onProposeAction,
  isProposing = false,
}) => {
  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'CROSS_SELL':
        return {
          label: 'Cross-Sell Opportunity',
          color: '#818cf8',
          bg: 'rgba(99, 102, 241, 0.12)',
          border: 'rgba(99, 102, 241, 0.3)',
          icon: <ShoppingCart size={14} />,
        };
      case 'UPSELL':
        return {
          label: 'Upsell / Upgrade',
          color: '#34d399',
          bg: 'rgba(16, 185, 129, 0.12)',
          border: 'rgba(16, 185, 129, 0.3)',
          icon: <TrendingUp size={14} />,
        };
      case 'BUNDLE':
        return {
          label: 'Product Bundle',
          color: '#38bdf8',
          bg: 'rgba(56, 189, 248, 0.12)',
          border: 'rgba(56, 189, 248, 0.3)',
          icon: <Sparkles size={14} />,
        };
      case 'SLOW_MOVING_PRODUCT':
        return {
          label: 'Slow-Moving Stock',
          color: '#fbbf24',
          bg: 'rgba(245, 158, 11, 0.12)',
          border: 'rgba(245, 158, 11, 0.3)',
          icon: <AlertCircle size={14} />,
        };
      default:
        return {
          label: type,
          color: '#cbd5e1',
          bg: 'rgba(148, 163, 184, 0.12)',
          border: 'rgba(148, 163, 184, 0.3)',
          icon: <Sparkles size={14} />,
        };
    }
  };

  const badge = getTypeBadge(opportunity.type);
  const confidencePercent = Math.round(opportunity.confidence * 100);

  return (
    <div
      className="glass-card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        padding: '20px',
        position: 'relative',
        border: `1px solid ${badge.border}`,
        background: 'rgba(15, 23, 42, 0.7)',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            borderRadius: '20px',
            fontSize: '0.75rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            background: badge.bg,
            color: badge.color,
            border: `1px solid ${badge.border}`,
          }}
        >
          {badge.icon}
          {badge.label}
        </span>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Confidence:</span>
          <span
            className="mono"
            style={{
              fontSize: '0.8rem',
              fontWeight: 700,
              color: confidencePercent >= 80 ? '#34d399' : '#fbbf24',
              background: 'rgba(255, 255, 255, 0.05)',
              padding: '2px 8px',
              borderRadius: '4px',
            }}
          >
            {confidencePercent}%
          </span>
        </div>
      </div>

      {/* Title & Description */}
      <div>
        <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
          {opportunity.title}
        </h4>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
          {opportunity.description}
        </p>
      </div>

      {/* Explainability Section: FACT vs AI INTERPRETATION */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          padding: '12px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
          <span
            style={{
              fontSize: '0.675rem',
              fontWeight: 800,
              letterSpacing: '0.05em',
              background: 'rgba(99, 102, 241, 0.2)',
              color: '#a5b4fc',
              padding: '2px 6px',
              borderRadius: '4px',
              textTransform: 'uppercase',
              flexShrink: 0,
            }}
          >
            FACT
          </span>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-main)', lineHeight: '1.4' }}>
            {opportunity.fact_statement}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
          <span
            style={{
              fontSize: '0.675rem',
              fontWeight: 800,
              letterSpacing: '0.05em',
              background: 'rgba(16, 185, 129, 0.2)',
              color: '#6ee7b7',
              padding: '2px 6px',
              borderRadius: '4px',
              textTransform: 'uppercase',
              flexShrink: 0,
            }}
          >
            AI HYPOTHESIS
          </span>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
            {opportunity.ai_interpretation}
          </span>
        </div>
      </div>

      {/* Footer: Revenue Impact & Action Buttons */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          marginTop: 'auto',
          paddingTop: '10px',
        }}
      >
        <div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
            Est. Revenue Impact
          </div>
          <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 700, color: '#34d399' }}>
            ₹{opportunity.estimated_revenue_impact.toLocaleString()}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => onReview(opportunity)}
            style={{ gap: '4px' }}
          >
            Review <ArrowUpRight size={14} />
          </button>

          {onProposeAction && (
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => onProposeAction(opportunity)}
              disabled={isProposing}
              style={{
                gap: '6px',
                background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
                fontWeight: 700,
              }}
            >
              {isProposing ? (
                <>
                  <RefreshCw size={13} className="spinning" /> Proposing...
                </>
              ) : (
                <>
                  <Zap size={13} fill="#FCD34D" color="#FCD34D" /> Propose Campaign
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
