import React, { useEffect, useState } from 'react';
import { Plus, Eye, RefreshCw, Filter } from 'lucide-react';
import { Customer, Merchant, Order, OrderCreateInput, OrderStatus, Product } from '../types';
import { orderService } from '../services/orderService';
import { productService } from '../services/productService';
import { customerService } from '../services/customerService';
import { OrderStatusBadge } from '../components/Badge';
import { OrderCreateModal } from '../components/OrderCreateModal';
import { OrderDetailsModal } from '../components/OrderDetailsModal';

interface OrdersPageProps {
  currentMerchant: Merchant | null;
}

export const OrdersPage: React.FC<OrdersPageProps> = ({ currentMerchant }) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [viewingOrder, setViewingOrder] = useState<Order | null>(null);

  const fetchOrders = async () => {
    if (!currentMerchant) return;
    try {
      setLoading(true);
      const filters: any = { merchant_id: currentMerchant.id };
      if (selectedStatus) filters.status = selectedStatus as OrderStatus;

      const [ordData, prodData, custData] = await Promise.all([
        orderService.getOrders(filters),
        productService.getProducts({ merchant_id: currentMerchant.id, is_active: true }),
        customerService.getCustomers(),
      ]);

      setOrders(ordData);
      setProducts(prodData);
      setCustomers(custData);
    } catch (err) {
      console.error('Failed to load orders:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [currentMerchant, selectedStatus]);

  const handleCreateOrder = async (orderData: OrderCreateInput) => {
    await orderService.createOrder(orderData);
    await fetchOrders();
  };

  const handleStatusChange = async (orderId: number, newStatus: OrderStatus) => {
    try {
      const updated = await orderService.updateOrderStatus(orderId, newStatus);
      setViewingOrder(updated);
      await fetchOrders();
    } catch (err: any) {
      alert(err.message || 'Failed to update status.');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Action and Filter Bar */}
      <div className="filter-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-dim)', fontSize: '0.875rem' }}>
            <Filter size={16} /> Filter Status:
          </div>
          <div style={{ display: 'flex', gap: '6px' }}>
            {['', 'PENDING', 'CONFIRMED', 'CANCELLED', 'FAILED'].map((st) => (
              <button
                key={st}
                type="button"
                className={`btn btn-sm ${selectedStatus === st ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSelectedStatus(st)}
              >
                {st === '' ? 'All Orders' : st}
              </button>
            ))}
          </div>
        </div>

        <div className="filter-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={fetchOrders}
            title="Refresh orders"
          >
            <RefreshCw size={16} />
          </button>

          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setIsCreateOpen(true)}
            disabled={!currentMerchant}
          >
            <Plus size={18} /> Create Order
          </button>
        </div>
      </div>

      {/* Orders Table */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Customer</th>
                <th>Items Summary</th>
                <th>Order Total</th>
                <th>Status</th>
                <th>Created At</th>
                <th style={{ textAlign: 'right' }}>Details</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '40px' }}>
                    Loading store orders...
                  </td>
                </tr>
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '40px' }}>
                    No orders matching the selected filter.
                  </td>
                </tr>
              ) : (
                orders.map((ord) => {
                  const itemCount = ord.items.reduce((sum, i) => sum + i.quantity, 0);
                  const itemsPreview = ord.items
                    .map((i) => `${i.product?.name || 'Item'} (${i.quantity})`)
                    .join(', ');

                  return (
                    <tr
                      key={ord.id}
                      onClick={() => setViewingOrder(ord)}
                      style={{ cursor: 'pointer' }}
                    >
                      <td>
                        <span className="mono cell-highlight" style={{ color: '#818cf8' }}>
                          #{ord.id}
                        </span>
                      </td>
                      <td>
                        <div className="cell-highlight">
                          {ord.customer?.name || `Customer #${ord.customer_id}`}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                          {ord.customer?.email}
                        </div>
                      </td>
                      <td>
                        <div
                          style={{
                            fontSize: '0.825rem',
                            color: 'var(--text-muted)',
                            maxWidth: '260px',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                          title={itemsPreview}
                        >
                          <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                            {itemCount} {itemCount === 1 ? 'item' : 'items'}:
                          </span>{' '}
                          {itemsPreview}
                        </div>
                      </td>
                      <td className="mono" style={{ fontWeight: 700, color: 'var(--text-main)' }}>
                        ₹{ord.total_amount.toLocaleString()}
                      </td>
                      <td>
                        <OrderStatusBadge status={ord.status} />
                      </td>
                      <td style={{ fontSize: '0.8rem' }}>
                        {new Date(ord.created_at).toLocaleString('en-IN', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setViewingOrder(ord);
                          }}
                          title="View order breakdown"
                        >
                          <Eye size={14} /> View
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Order Modal */}
      {currentMerchant && (
        <OrderCreateModal
          isOpen={isCreateOpen}
          onClose={() => setIsCreateOpen(false)}
          onSubmit={handleCreateOrder}
          merchantId={currentMerchant.id}
          customers={customers}
          products={products}
        />
      )}

      {/* Order Details Modal */}
      <OrderDetailsModal
        isOpen={!!viewingOrder}
        onClose={() => setViewingOrder(null)}
        order={viewingOrder}
        onStatusChange={handleStatusChange}
      />
    </div>
  );
};
