import React from 'react';
import { Modal } from './Modal';
import { Order, OrderStatus } from '../types';
import { OrderStatusBadge } from './Badge';

interface OrderDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  order: Order | null;
  onStatusChange?: (orderId: number, newStatus: OrderStatus) => Promise<void>;
}

export const OrderDetailsModal: React.FC<OrderDetailsModalProps> = ({
  isOpen,
  onClose,
  order,
  onStatusChange,
}) => {
  if (!order) return null;

  const formattedDate = new Date(order.created_at).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Order Details #${order.id}`}
      maxWidth="700px"
    >
      <div className="modal-content">
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
            marginBottom: '24px',
            padding: '16px',
            background: 'rgba(255, 255, 255, 0.02)',
            borderRadius: '10px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Customer
            </div>
            <div style={{ fontWeight: 600, color: 'var(--text-main)', marginTop: '4px' }}>
              {order.customer?.name || `Customer #${order.customer_id}`}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {order.customer?.email}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Order Status
            </div>
            <div style={{ marginTop: '4px' }}>
              <OrderStatusBadge status={order.status} />
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Placed On
            </div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-main)', marginTop: '4px' }}>
              {formattedDate}
            </div>
          </div>
        </div>

        <div style={{ marginBottom: '12px' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '8px' }}>
            Purchased Line Items
          </div>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Quantity</th>
                  <th>Unit Price</th>
                  <th style={{ textAlign: 'right' }}>Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {order.items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <div className="cell-highlight">
                        {item.product?.name || `Product #${item.product_id}`}
                      </div>
                      {item.product?.sku && (
                        <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                          SKU: {item.product.sku}
                        </span>
                      )}
                    </td>
                    <td>{item.quantity}</td>
                    <td className="mono">₹{item.unit_price.toLocaleString()}</td>
                    <td className="mono" style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-main)' }}>
                      ₹{item.subtotal.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            gap: '16px',
            marginTop: '16px',
            paddingTop: '16px',
            borderTop: '1px solid var(--border-subtle)',
          }}
        >
          <span style={{ fontSize: '0.95rem', color: 'var(--text-muted)' }}>Order Total:</span>
          <span className="mono" style={{ fontSize: '1.4rem', fontWeight: 700, color: '#818cf8' }}>
            ₹{order.total_amount.toLocaleString()} {order.currency}
          </span>
        </div>

        {onStatusChange && (
          <div
            style={{
              marginTop: '20px',
              padding: '12px 16px',
              background: 'rgba(255, 255, 255, 0.02)',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Update Order Status:
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              {(['PENDING', 'CONFIRMED', 'CANCELLED'] as OrderStatus[]).map((st) => (
                <button
                  key={st}
                  type="button"
                  className={`btn btn-sm ${order.status === st ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => onStatusChange(order.id, st)}
                  disabled={order.status === st}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="modal-footer">
        <button type="button" className="btn btn-secondary" onClick={onClose}>
          Close
        </button>
      </div>
    </Modal>
  );
};
