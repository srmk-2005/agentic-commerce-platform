import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Bot,
  CheckCircle2,
  Cpu,
  CreditCard,
  Layers,
  Play,
  Shield,
  ShoppingBag,
  Sliders,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { agentCommerceService } from '../services/agentCommerceService';
import type { AgentCommerceStats, Merchant } from '../types';

interface AgentCommerceDashboardPageProps {
  currentMerchant: Merchant | null;
}

export const AgentCommerceDashboardPage: React.FC<AgentCommerceDashboardPageProps> = ({ currentMerchant }) => {
  const [stats, setStats] = useState<AgentCommerceStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadStats();
  }, [currentMerchant]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await agentCommerceService.getStats(currentMerchant?.id);
      setStats(data);
    } catch (err) {
      console.error('Failed to load agent commerce stats:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Banner */}
      <div
        className="glass-card"
        style={{
          padding: '24px',
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%)',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Cpu size={20} color="#ffffff" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-main)' }}>
                Agent-to-Agent Commerce Hub
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Standardized Agent Commerce Protocol Layer & Autonomous Buyer Gateway
              </p>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <Link
            to="/demo"
            className="btn btn-primary"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
              fontWeight: 700,
              textDecoration: 'none',
              padding: '8px 16px',
              borderRadius: '8px',
              color: '#ffffff',
            }}
          >
            <Play size={16} />
            3-Min Judge Demo Screen
          </Link>

          <Link
            to="/agent-commerce/inspector"
            className="btn btn-outline"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              textDecoration: 'none',
              padding: '8px 14px',
              borderRadius: '8px',
            }}
          >
            <Sliders size={16} />
            Protocol Inspector
          </Link>

          <Link
            to="/agent-commerce/readiness"
            className="btn btn-outline"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              textDecoration: 'none',
              padding: '8px 14px',
              borderRadius: '8px',
            }}
          >
            <Sparkles size={16} color="#fbbf24" />
            Readiness Score
          </Link>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div
          className="glass-card"
          style={{
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontWeight: 600 }}>ACTIVE AI BUYERS</span>
            <Bot size={18} color="#818CF8" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-main)' }}>
            {loading ? '-' : stats?.active_sessions || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#818CF8', marginTop: '4px' }}>
            Stateful sessions active
          </div>
        </div>

        <div
          className="glass-card"
          style={{
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontWeight: 600 }}>ORDERS VIA AI</span>
            <ShoppingBag size={18} color="#38BDF8" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-main)' }}>
            {loading ? '-' : stats?.orders_via_ai || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#38BDF8', marginTop: '4px' }}>
            Autonomous machine purchases
          </div>
        </div>

        <div
          className="glass-card"
          style={{
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontWeight: 600 }}>AI GMV REVENUE</span>
            <TrendingUp size={18} color="#34D399" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#34D399' }} className="mono">
            {loading ? '-' : `₹${(stats?.ai_revenue || 0).toLocaleString()}`}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#34D399', marginTop: '4px' }}>
            Gated & verified revenue
          </div>
        </div>

        <div
          className="glass-card"
          style={{
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontWeight: 600 }}>SAFE PAYMENTS</span>
            <CreditCard size={18} color="#10B981" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-main)' }}>
            {loading ? '-' : stats?.successful_payments || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#10B981', marginTop: '4px' }}>
            Captured in Razorpay test mode
          </div>
        </div>

        <div
          className="glass-card"
          style={{
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontWeight: 600 }}>BLOCKED ATTEMPTS</span>
            <Shield size={18} color="#EF4444" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#EF4444' }}>
            {loading ? '-' : stats?.blocked_transactions || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#f87171', marginTop: '4px' }}>
            Protected by policy limits
          </div>
        </div>
      </div>

      {/* Architecture & Security Invariant Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        {/* Core Architecture */}
        <div
          className="glass-card"
          style={{
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <Layers size={18} color="#818CF8" />
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Protocol Architecture (v1.0)
            </h3>
          </div>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', lineHeight: '1.5', marginBottom: '14px' }}>
            Mercora provides a <strong>Protocol-ready Agentic Commerce Interface</strong> that standardizes discovery, catalog querying, real-time inventory checking, order creation, and gated payment proposals.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.775rem', padding: '6px 10px', borderRadius: '6px', background: 'rgba(255, 255, 255, 0.02)' }}>
              <span style={{ color: 'var(--text-dim)' }}>Protocol Version:</span>
              <strong className="mono" style={{ color: '#818CF8' }}>1.0 (Standard Agent Commerce)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.775rem', padding: '6px 10px', borderRadius: '6px', background: 'rgba(255, 255, 255, 0.02)' }}>
              <span style={{ color: 'var(--text-dim)' }}>Session Isolation:</span>
              <span style={{ color: '#34D399' }}>✓ Trace ID + Merchant Boundary</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.775rem', padding: '6px 10px', borderRadius: '6px', background: 'rgba(255, 255, 255, 0.02)' }}>
              <span style={{ color: 'var(--text-dim)' }}>Payment Adapter:</span>
              <span style={{ color: '#38BDF8' }}>Razorpay Test Mode (Paise + HMAC-SHA256)</span>
            </div>
          </div>
        </div>

        {/* Security Inspector Checklist */}
        <div
          className="glass-card"
          style={{
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <Shield size={18} color="#10B981" />
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Security & Safety Invariants
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#6ee7b7' }}>
              <CheckCircle2 size={16} color="#10B981" />
              <span>AI cannot alter product prices (Server computes pricing)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#6ee7b7' }}>
              <CheckCircle2 size={16} color="#10B981" />
              <span>AI cannot bypass inventory or stock deduction rules</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#6ee7b7' }}>
              <CheckCircle2 size={16} color="#10B981" />
              <span>AI cannot self-authorize payment (Explicit [APPROVE & PAY] Gate)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#6ee7b7' }}>
              <CheckCircle2 size={16} color="#10B981" />
              <span>AI cannot exceed single transaction or daily spend caps</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#6ee7b7' }}>
              <CheckCircle2 size={16} color="#10B981" />
              <span>Secret keys strictly isolated from LLM prompts & client responses</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
