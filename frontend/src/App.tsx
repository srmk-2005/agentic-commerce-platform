import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { AiAssistantPage } from './pages/AiAssistantPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { CampaignsPage } from './pages/CampaignsPage';
import { AuditPage } from './pages/AuditPage';
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
            path="/ai-assistant"
            element={<AiAssistantPage currentMerchant={currentMerchant} />}
          />
          <Route
            path="/approvals"
            element={<ApprovalsPage currentMerchant={currentMerchant} />}
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
