import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { AiAssistantPage } from './pages/AiAssistantPage';
import { AiCommercePage } from './pages/AiCommercePage';
import { AiBuyerPage } from './pages/AiBuyerPage';
import { AgentCommerceDashboardPage } from './pages/AgentCommerceDashboardPage';
import { ProtocolInspectorPage } from './pages/ProtocolInspectorPage';
import { CommerceReadinessPage } from './pages/CommerceReadinessPage';
import { JudgeDemoPage } from './pages/JudgeDemoPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { CampaignsPage } from './pages/CampaignsPage';
import { AuditPage } from './pages/AuditPage';
import { PaymentApprovalPage } from './pages/PaymentApprovalPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { ProductsPage } from './pages/ProductsPage';
import { OrdersPage } from './pages/OrdersPage';
import { CustomersPage } from './pages/CustomersPage';
import { Merchant } from './types';

export const App: React.FC = () => {
  const [currentMerchant, setCurrentMerchant] = useState<Merchant | null>(null);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          element={
            <Layout
              currentMerchant={currentMerchant}
              onSelectMerchant={setCurrentMerchant}
            />
          }
        >
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route
            path="/dashboard"
            element={<DashboardPage currentMerchant={currentMerchant} />}
          />
          <Route
            path="/demo"
            element={<JudgeDemoPage />}
          />
          <Route
            path="/agent-commerce"
            element={<AgentCommerceDashboardPage currentMerchant={currentMerchant} />}
          />
          <Route
            path="/agent-commerce/inspector"
            element={<ProtocolInspectorPage />}
          />
          <Route
            path="/agent-commerce/readiness"
            element={<CommerceReadinessPage currentMerchant={currentMerchant} />}
          />
          <Route
            path="/ai-assistant"
            element={<AiAssistantPage currentMerchant={currentMerchant} />}
          />
          <Route
            path="/ai-commerce"
            element={<AiCommercePage currentMerchant={currentMerchant} />}
          />
          <Route
            path="/ai-buyer"
            element={<AiBuyerPage currentMerchant={currentMerchant} />}
          />
          <Route
            path="/approvals"
            element={<ApprovalsPage currentMerchant={currentMerchant} />}
          />
          <Route
            path="/payment-approval/:id"
            element={<PaymentApprovalPage />}
          />
          <Route
            path="/transactions"
            element={<TransactionsPage />}
          />
          <Route
            path="/campaigns"
            element={<CampaignsPage currentMerchant={currentMerchant} />}
          />
          <Route
            path="/audit"
            element={<AuditPage currentMerchant={currentMerchant} />}
          />
          <Route
            path="/products"
            element={<ProductsPage currentMerchant={currentMerchant} />}
          />
          <Route
            path="/orders"
            element={<OrdersPage currentMerchant={currentMerchant} />}
          />
          <Route path="/customers" element={<CustomersPage />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
