import React from 'react';
import { Modal } from './Modal';
import { Opportunity } from '../types';
import { ShieldCheck } from 'lucide-react';

interface OpportunityDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  opportunity: Opportunity | null;
}

export const OpportunityDetailsModal: React.FC<OpportunityDetailsModalProps> = ({
  isOpen,
  onClose,
  opportunity,
}) => {
  if (!opportunity) return null;

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

        {/* Supporting Metrics Table */}
        {Object.keys(opportunity.supporting_metrics).length > 0 && (
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px' }}>
              Supporting Metrics
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>Observed Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(opportunity.supporting_metrics).map(([key, val]) => (
                    <tr key={key}>
                      <td style={{ textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</td>
                      <td className="mono cell-highlight">
                        {typeof val === 'number'
                          ? val % 1 !== 0
                            ? val.toFixed(2)
                            : val.toString()
                          : String(val)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Safety Boundary Notice */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 16px',
            background: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            borderRadius: '8px',
            fontSize: '0.825rem',
            color: '#fcd34d',
          }}
        >
          <ShieldCheck size={20} color="#F59E0B" style={{ flexShrink: 0 }} />
          <span>
            <strong>Phase 2 Review Only:</strong> This recommendation requires merchant approval. Campaign execution workflows and automated buyer discounts will be activated in Phase 3.
          </span>
        </div>
      </div>

      <div className="modal-footer">
        <button type="button" className="btn btn-secondary" onClick={onClose}>
          Close Review
        </button>
      </div>
    </Modal>
  );
};
