import React, { useState } from 'react';
import { Modal } from './Modal';
import { Opportunity } from '../types';
import { ShieldCheck, Zap, RefreshCw, Sparkles } from 'lucide-react';

interface OpportunityDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  opportunity: Opportunity | null;
  onProposeAction?: (opportunity: Opportunity, discountValue: number, durationDays: number) => void;
  isProposing?: boolean;
}

export const OpportunityDetailsModal: React.FC<OpportunityDetailsModalProps> = ({
  isOpen,
  onClose,
  opportunity,
  onProposeAction,
  isProposing = false,
}) => {
  const [discountValue, setDiscountValue] = useState<number>(10);
  const [durationDays, setDurationDays] = useState<number>(7);

  if (!opportunity) return null;

  const handlePropose = () => {
    if (onProposeAction) {
      onProposeAction(opportunity, discountValue, durationDays);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={opportunity.title}
      maxWidth="720px"
    >
      <div className="modal-content" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Overview Header */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px',
            padding: '16px',
            background: 'rgba(255, 255, 255, 0.02)',
            borderRadius: '10px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Opportunity Type
            </div>
            <div style={{ fontWeight: 700, color: '#818cf8', marginTop: '2px' }}>
              {opportunity.type.replace(/_/g, ' ')}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Confidence Score
            </div>
            <div className="mono" style={{ fontWeight: 700, color: '#34d399', marginTop: '2px' }}>
              {Math.round(opportunity.confidence * 100)}%
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Est. Gross Revenue Impact
            </div>
            <div className="mono" style={{ fontWeight: 700, color: '#34d399', marginTop: '2px', fontSize: '1.1rem' }}>
              ₹{opportunity.estimated_revenue_impact.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Target vs Attached Products */}
        <div>
          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px' }}>
            Associated Products
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <div
              style={{
                flex: 1,
                minWidth: '220px',
                padding: '12px',
                background: 'rgba(99, 102, 241, 0.06)',
                border: '1px solid rgba(99, 102, 241, 0.2)',
                borderRadius: '8px',
              }}
            >
              <span style={{ fontSize: '0.7rem', color: '#a5b4fc', textTransform: 'uppercase', fontWeight: 700 }}>
                Primary Target Product
              </span>
              <div style={{ fontWeight: 600, color: 'var(--text-main)', marginTop: '4px' }}>
                {opportunity.primary_product_name}
              </div>
              <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                Product ID: #{opportunity.primary_product_id}
              </div>
            </div>

            {opportunity.recommended_product_names.length > 0 && (
              <div
                style={{
                  flex: 1,
                  minWidth: '220px',
                  padding: '12px',
                  background: 'rgba(16, 185, 129, 0.06)',
                  border: '1px solid rgba(16, 185, 129, 0.2)',
                  borderRadius: '8px',
                }}
              >
                <span style={{ fontSize: '0.7rem', color: '#6ee7b7', textTransform: 'uppercase', fontWeight: 700 }}>
                  Recommended Item(s)
                </span>
                <div style={{ fontWeight: 600, color: 'var(--text-main)', marginTop: '4px' }}>
                  {opportunity.recommended_product_names.join(', ')}
                </div>
                <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                  IDs: {opportunity.recommended_product_ids.map((id) => `#${id}`).join(', ')}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Explainability Breakdown */}
        <div>
          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px' }}>
            Empirical Evidence & Strategic Reasoning
          </div>
          <div
            style={{
              padding: '16px',
              background: 'rgba(255, 255, 255, 0.02)',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <div>
              <span style={{ fontSize: '0.725rem', fontWeight: 800, color: '#818cf8', textTransform: 'uppercase' }}>
                GROUND TRUTH (DATABASE FACT)
              </span>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginTop: '2px' }}>
                {opportunity.fact_statement}
              </p>
            </div>

            <div>
              <span style={{ fontSize: '0.725rem', fontWeight: 800, color: '#34d399', textTransform: 'uppercase' }}>
                AI GROWTH HYPOTHESIS
              </span>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {opportunity.ai_interpretation}
              </p>
            </div>
          </div>
        </div>

        {/* Interactive Campaign Customization Parameters */}
        <div
          style={{
            padding: '16px',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(16, 185, 129, 0.05) 100%)',
            border: '1px solid rgba(99, 102, 241, 0.25)',
            borderRadius: '10px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} color="#818CF8" />
            <h5 style={{ fontSize: '0.925rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Configure Action Proposal Terms
            </h5>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '0.775rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                Discount Percentage (Max: 20%)
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={discountValue}
                  onChange={(e) => setDiscountValue(Math.min(20, Math.max(1, Number(e.target.value) || 10)))}
                  className="form-input"
                  style={{ width: '100px' }}
                />
                <span style={{ fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: 600 }}>% OFF</span>
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.775rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                Campaign Duration
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <select
                  value={durationDays}
                  onChange={(e) => setDurationDays(Number(e.target.value))}
                  className="form-input"
                  style={{ width: '140px' }}
                >
                  <option value={3}>3 Days (Flash)</option>
                  <option value={7}>7 Days (Standard)</option>
                  <option value={14}>14 Days (Bi-weekly)</option>
                  <option value={30}>30 Days (Monthly)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Safety Boundary Notice */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 16px',
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            borderRadius: '8px',
            fontSize: '0.825rem',
            color: '#6ee7b7',
          }}
        >
          <ShieldCheck size={20} color="#10B981" style={{ flexShrink: 0 }} />
          <span>
            <strong>Human-In-The-Loop Control:</strong> Submitting this action creates an Action Proposal in your <strong>Approvals Queue</strong>. No discounts or campaigns are published without your explicit review.
          </span>
        </div>
      </div>

      <div className="modal-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isProposing}>
          Close Review
        </button>

        {onProposeAction && (
          <button
            type="button"
            className="btn btn-primary"
            onClick={handlePropose}
            disabled={isProposing}
            style={{
              gap: '8px',
              background: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
              fontWeight: 800,
              padding: '10px 20px',
            }}
          >
            {isProposing ? (
              <>
                <RefreshCw size={16} className="spinning" /> Submitting Proposal...
              </>
            ) : (
              <>
                <Zap size={16} fill="#FCD34D" color="#FCD34D" /> Submit Action Proposal to Approvals
              </>
            )}
          </button>
        )}
      </div>
    </Modal>
  );
};
