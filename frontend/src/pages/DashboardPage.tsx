import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  DollarSign,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  Bot,
  Sparkles,
  ShieldCheck,
  Megaphone,
  Clock,
} from 'lucide-react';
import { AgentSummaryMetrics, Merchant, Order, Product } from '../types';
import { productService } from '../services/productService';
import { orderService } from '../services/orderService';
import { agentService } from '../services/agentService';
import { StatCard } from '../components/StatCard';
import { OrderStatusBadge, StockBadge } from '../components/Badge';

interface DashboardPageProps {
  currentMerchant: Merchant | null;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ currentMerchant }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [aiMetrics, setAiMetrics] = useState<AgentSummaryMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!currentMerchant) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        const [prodData, ordData, agentData] = await Promise.all([
          productService.getProducts({ merchant_id: currentMerchant.id }),
          orderService.getOrders({ merchant_id: currentMerchant.id }),
          agentService.getMetrics(currentMerchant.id).catch(() => null),
        ]);
        setProducts(prodData);
        setOrders(ordData);
        setAiMetrics(agentData);
      } catch (err) {
        console.error('Failed to load dashboard metrics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [currentMerchant]);

  // Compute metrics
  const totalRevenue = orders
    .filter((o) => o.status !== 'CANCELLED' && o.status !== 'FAILED')
    .reduce((sum, o) => sum + o.total_amount, 0);

  const lowStockProducts = products.filter((p) => p.stock_quantity <= 15);
  const recentOrders = orders.slice(0, 5);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top AI Merchant Growth Callout Banner */}
      <div
        className="glass-card"
        style={{
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(16, 185, 129, 0.08) 100%)',
          borderColor: 'rgba(99, 102, 241, 0.3)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          padding: '20px 24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: 'var(--accent-gradient)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4)',
            }}
          >
            <Bot size={26} color="white" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>
                Merchant AI Growth Intelligence & Action Hub
              </h3>
              <span
                className="badge-tag"
                style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#6ee7b7', border: '1px solid rgba(16, 185, 129, 0.3)' }}
              >
                <Sparkles size={12} /> Active
              </span>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              {aiMetrics
                ? `Identified ${aiMetrics.total_opportunities} opportunities. ${aiMetrics.pending_approvals_count} action proposal(s) awaiting your review.`
                : 'Analyzing catalog and historical order co-purchase affinities...'}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <Link to="/approvals" className="btn btn-secondary btn-sm" style={{ gap: '6px' }}>
            <ShieldCheck size={14} color="#818CF8" /> Approvals ({aiMetrics?.pending_approvals_count || 0})
          </Link>
          <Link to="/ai-assistant" className="btn btn-primary btn-sm" style={{ gap: '6px' }}>
            AI Assistant <ArrowRight size={14} />
          </Link>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="stat-grid">
        <StatCard
          label="Total Revenue"
          value={loading ? '...' : `₹${totalRevenue.toLocaleString()}`}
          icon={<DollarSign size={20} color="#10B981" />}
          subtitle="Confirmed / Pending orders"
          trend="+18.4%"
        />

        <StatCard
          label="Pending Approvals"
          value={loading ? '...' : aiMetrics ? aiMetrics.pending_approvals_count : 0}
          icon={<Clock size={20} color="#F59E0B" />}
          subtitle="AI growth actions needing review"
          trend={aiMetrics && aiMetrics.pending_approvals_count > 0 ? 'Requires Action' : undefined}
        />

        <StatCard
          label="Active Campaigns"
          value={loading ? '...' : aiMetrics ? aiMetrics.active_campaigns_count : 0}
          icon={<Megaphone size={20} color="#38BDF8" />}
          subtitle="Live bundles & cross-sells"
        />

        <StatCard
          label="AI Revenue Potential"
          value={loading ? '...' : aiMetrics ? `₹${aiMetrics.potential_revenue_impact.toLocaleString()}` : '₹0'}
          icon={<Sparkles size={20} color="#818CF8" />}
          subtitle="*AI-estimated potential gain"
        />
      </div>

      {/* Main Grid: Recent Orders & Inventory Health */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '2fr 1fr',
          gap: '24px',
        }}
      >
        {/* Recent Orders Card */}
        <div className="glass-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Recent Transactions</h3>
              <p className="card-subtitle">Latest commerce orders placed on store</p>
            </div>
            <Link to="/orders" className="btn btn-secondary btn-sm">
              View All <ArrowRight size={14} />
            </Link>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Customer</th>
                  <th>Total</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {recentOrders.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '32px' }}>
                      {loading ? 'Loading orders...' : 'No orders recorded yet.'}
                    </td>
                  </tr>
                ) : (
                  recentOrders.map((ord) => (
                    <tr key={ord.id}>
                      <td className="mono cell-highlight">#{ord.id}</td>
                      <td>{ord.customer?.name || `Customer #${ord.customer_id}`}</td>
                      <td className="mono" style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                        ₹{ord.total_amount.toLocaleString()}
                      </td>
                      <td>
                        <OrderStatusBadge status={ord.status} />
                      </td>
                      <td style={{ fontSize: '0.8rem' }}>
                        {new Date(ord.created_at).toLocaleDateString('en-IN', {
                          month: 'short',
                          day: 'numeric',
                        })}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Low Stock Alerts & Fast Insights */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="glass-card">
            <div className="card-header">
              <div>
                <h3 className="card-title">Inventory Alerts</h3>
                <p className="card-subtitle">Items requiring replenishment</p>
              </div>
              <AlertTriangle size={18} color="#F59E0B" />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {lowStockProducts.length === 0 ? (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', padding: '12px 0' }}>
                  All catalog items have healthy stock levels.
                </div>
              ) : (
                lowStockProducts.map((p) => (
                  <div
                    key={p.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 12px',
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderRadius: '8px',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-main)' }}>
                        {p.name}
                      </div>
                      <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        SKU: {p.sku}
                      </div>
                    </div>
                    <StockBadge quantity={p.stock_quantity} />
                  </div>
                ))
              )}
            </div>
          </div>

          <div
            className="glass-card"
            style={{
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(168, 85, 247, 0.04) 100%)',
              borderColor: 'rgba(99, 102, 241, 0.2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <TrendingUp size={18} color="#818CF8" />
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#c7d2fe' }}>
                Governance & Safety Guardrails
              </h4>
            </div>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              All AI revenue proposals are capped at 20% discount, checked against live stock, and require explicit merchant consent before activation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
