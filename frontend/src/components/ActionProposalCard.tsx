import React from 'react';
import { Link } from 'react-router-dom';
import { ActionProposal } from '../types';
import { ShieldCheck, ArrowRight } from 'lucide-react';

interface ActionProposalCardProps {
  proposal: ActionProposal;
}

export const ActionProposalCard: React.FC<ActionProposalCardProps> = ({ proposal }) => {
  return (
    <div
      className="glass-card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        padding: '18px 20px',
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%)',
        border: '1px solid rgba(99, 102, 241, 0.35)',
        borderRadius: '14px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
      }}
    >
      {/* Header Pill */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              fontSize: '0.7rem',
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              padding: '3px 8px',
              borderRadius: '6px',
              background: 'rgba(99, 102, 241, 0.2)',
              color: '#a5b4fc',
              border: '1px solid rgba(99, 102, 241, 0.4)',
            }}
          >
            ACTION PROPOSAL
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Status: <strong style={{ color: '#fbbf24' }}>PENDING APPROVAL</strong>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: '#34d399' }}>
          <ShieldCheck size={14} />
          <span>Safety Validated</span>
        </div>
      </div>

      {/* Title & Description */}
      <div>
        <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
          {proposal.title}
        </h4>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
          {proposal.description}
        </p>
      </div>

      {/* Target Products & Pricing */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '10px',
          padding: '12px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
            Target Products
          </div>
          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)', marginTop: '2px' }}>
            {proposal.target_product_names.join(' + ') || `${proposal.target_product_ids.length} item(s)`}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
            Discount Terms
          </div>
          <div className="mono" style={{ fontSize: '0.9rem', fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>
            {proposal.discount_value}% OFF ({proposal.campaign_duration_days} Days)
          </div>
        </div>

        {proposal.original_bundle_price != null && proposal.discounted_bundle_price != null && (
          <div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Bundle Price
            </div>
            <div className="mono" style={{ fontSize: '0.9rem', fontWeight: 700, color: '#34d399', marginTop: '2px' }}>
              ₹{proposal.discounted_bundle_price.toLocaleString()}{' '}
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textDecoration: 'line-through' }}>
                ₹{proposal.original_bundle_price.toLocaleString()}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Footer / CTA to Approvals */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
          Requires human review before campaign creation.
        </div>

        <Link
          to="/approvals"
          className="btn btn-primary btn-sm"
          style={{ gap: '6px', padding: '6px 14px' }}
        >
          Review in Approvals <ArrowRight size={14} />
        </Link>
      </div>
    </div>
  );
};
