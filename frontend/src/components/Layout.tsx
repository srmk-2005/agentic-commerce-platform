import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  ShoppingBag,
  Users,
  Store,
  CheckCircle2,
  AlertCircle,
  Bot,
  ShieldCheck,
  Megaphone,
  History,
} from 'lucide-react';
import { Merchant } from '../types';
import { merchantService } from '../services/merchantService';
import { approvalService } from '../services/approvalService';
import { request } from '../services/api';

interface LayoutProps {
  currentMerchant: Merchant | null;
  onSelectMerchant: (merchant: Merchant) => void;
}

export const Layout: React.FC<LayoutProps> = ({ currentMerchant, onSelectMerchant }) => {
  const location = useLocation();
  const [apiHealthy, setApiHealthy] = useState<boolean | null>(null);
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(0);

  useEffect(() => {
    // Check health endpoint
    request<{ status: string }>('/health')
      .then((res) => setApiHealthy(res.status === 'ok'))
      .catch(() => setApiHealthy(false));

    // If no merchant selected, load first available merchant
    if (!currentMerchant) {
      merchantService
        .getMerchants()
        .then((merchants) => {
          if (merchants.length > 0) {
            onSelectMerchant(merchants[0]);
          }
        })
        .catch(console.error);
    } else {
      // Poll pending approvals
      approvalService
        .getApprovals({ merchant_id: currentMerchant.id, status: 'PENDING' })
        .then((apprs) => setPendingApprovalsCount(apprs.length))
        .catch(() => setPendingApprovalsCount(0));
    }
  }, [currentMerchant, onSelectMerchant, location.pathname]);

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/dashboard':
        return 'Executive Overview';
      case '/ai-assistant':
        return 'Merchant AI Assistant';
      case '/approvals':
        return 'Approvals & Governance Queue';
      case '/campaigns':
        return 'Campaigns & Active Promotions';
      case '/audit':
        return 'Audit Trail & Execution Ledger';
      case '/products':
        return 'Product Catalog & Inventory';
      case '/orders':
        return 'Orders & Transactions';
      case '/customers':
        return 'Customer Directory';
      default:
        return 'Merchant Dashboard';
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-icon">
            <Store size={22} />
          </div>
          <div className="brand-info">
            <h1>Agentic Commerce</h1>
            <span>AI Merchant Hub</span>
          </div>
        </div>

        <nav className="nav-section">
          <div className="nav-heading">Platform</div>
          <NavLink
            to="/dashboard"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </NavLink>

          <NavLink
            to="/ai-assistant"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <Bot size={18} color="#818CF8" />
            <span>AI Assistant</span>
          </NavLink>

          <div className="nav-heading" style={{ marginTop: '14px' }}>
            Growth & Governance
          </div>

          <NavLink
            to="/approvals"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <ShieldCheck size={18} color="#F59E0B" />
            <span>Approvals</span>
            {pendingApprovalsCount > 0 && (
              <span
                style={{
                  marginLeft: 'auto',
                  fontSize: '0.7rem',
                  fontWeight: 800,
                  padding: '2px 7px',
                  borderRadius: '10px',
                  background: 'rgba(245, 158, 11, 0.25)',
                  color: '#fbbf24',
                  border: '1px solid rgba(245, 158, 11, 0.4)',
                }}
              >
                {pendingApprovalsCount}
              </span>
            )}
          </NavLink>

          <NavLink
            to="/campaigns"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <Megaphone size={18} color="#38BDF8" />
            <span>Campaigns</span>
          </NavLink>

          <NavLink
            to="/audit"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <History size={18} color="#C084FC" />
            <span>Audit Trail</span>
          </NavLink>

          <div className="nav-heading" style={{ marginTop: '14px' }}>
            Commerce Core
          </div>

          <NavLink
            to="/products"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <Package size={18} />
            <span>Products</span>
          </NavLink>

          <NavLink
            to="/orders"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <ShoppingBag size={18} />
            <span>Orders</span>
          </NavLink>

          <NavLink
            to="/customers"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <Users size={18} />
            <span>Customers</span>
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="merchant-badge-card">
            <div className="merchant-badge-header">
              <span className="merchant-badge-title">
                {currentMerchant ? currentMerchant.name : 'Loading Store...'}
              </span>
              <span className="status-dot" title="Active Merchant" />
            </div>
            <div className="merchant-badge-sub">
              {currentMerchant ? `${currentMerchant.currency} Store (ID: ${currentMerchant.id})` : 'Initializing...'}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        <header className="top-header">
          <div className="header-left">
            <h2 className="page-title">{getPageTitle()}</h2>
          </div>

          <div className="header-right">
            <span
              className="badge-tag"
              style={{
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(16, 185, 129, 0.2) 100%)',
                color: '#a5b4fc',
                border: '1px solid rgba(99, 102, 241, 0.4)',
                fontWeight: 700,
              }}
            >
              Phase 3: Revenue Actions & Approvals
            </span>
            {apiHealthy !== null && (
              <span
                className={`badge-tag ${apiHealthy ? 'badge-health' : 'badge-tag'}`}
                style={!apiHealthy ? { background: 'rgba(239, 68, 68, 0.15)', color: '#f87171' } : {}}
              >
                {apiHealthy ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
                {apiHealthy ? 'FastAPI Online' : 'API Offline'}
              </span>
            )}
          </div>
        </header>

        <main className="content-body">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
