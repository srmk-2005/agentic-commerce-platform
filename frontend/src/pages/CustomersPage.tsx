import React, { useEffect, useState } from 'react';
import { Plus, Mail, Calendar, RefreshCw } from 'lucide-react';
import { Customer, CustomerCreateInput, Order } from '../types';
import { customerService } from '../services/customerService';
import { orderService } from '../services/orderService';
import { CustomerModal } from '../components/CustomerModal';

export const CustomersPage: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchCustomersAndOrders = async () => {
    try {
      setLoading(true);
      const [custList, ordList] = await Promise.all([
        customerService.getCustomers(),
        orderService.getOrders(),
      ]);
      setCustomers(custList);
      setOrders(ordList);
    } catch (err) {
      console.error('Failed to load customers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomersAndOrders();
  }, []);

  const handleCreateCustomer = async (data: CustomerCreateInput) => {
    await customerService.createCustomer(data);
    await fetchCustomersAndOrders();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="filter-bar">
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)' }}>
            Customer Base
          </h3>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-dim)' }}>
            Registered purchasers and buyer profiles
          </p>
        </div>

        <div className="filter-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={fetchCustomersAndOrders}
            title="Refresh list"
          >
            <RefreshCw size={16} />
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setIsModalOpen(true)}
          >
            <Plus size={18} /> Add Customer
          </button>
        </div>
      </div>

      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Customer</th>
                <th>Email Address</th>
                <th>Total Orders</th>
                <th>Lifetime Spend</th>
                <th>Registered Date</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '40px' }}>
                    Loading customer profiles...
                  </td>
                </tr>
              ) : customers.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '40px' }}>
                    No customer records found.
                  </td>
                </tr>
              ) : (
                customers.map((c) => {
                  const custOrders = orders.filter((o) => o.customer_id === c.id);
                  const totalSpent = custOrders
                    .filter((o) => o.status !== 'CANCELLED' && o.status !== 'FAILED')
                    .reduce((sum, o) => sum + o.total_amount, 0);

                  return (
                    <tr key={c.id}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div
                            style={{
                              width: '34px',
                              height: '34px',
                              borderRadius: '50%',
                              background: 'rgba(99, 102, 241, 0.15)',
                              color: '#818cf8',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontWeight: 700,
                              fontSize: '0.85rem',
                            }}
                          >
                            {c.name.charAt(0)}
                          </div>
                          <div>
                            <div className="cell-highlight">{c.name}</div>
                            <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                              ID: #{c.id}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)' }}>
                          <Mail size={14} color="var(--text-dim)" />
                          {c.email}
                        </span>
                      </td>
                      <td>
                        <span className="badge-tag" style={{ background: 'rgba(255,255,255,0.05)' }}>
                          {custOrders.length} {custOrders.length === 1 ? 'order' : 'orders'}
                        </span>
                      </td>
                      <td>
                        <span className="mono" style={{ fontWeight: 600, color: '#34d399' }}>
                          ₹{totalSpent.toLocaleString()}
                        </span>
                      </td>
                      <td>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem' }}>
                          <Calendar size={14} color="var(--text-dim)" />
                          {new Date(c.created_at).toLocaleDateString('en-IN', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                          })}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <CustomerModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreateCustomer}
      />
    </div>
  );
};
