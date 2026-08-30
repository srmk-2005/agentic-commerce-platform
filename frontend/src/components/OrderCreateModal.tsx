import React, { useState } from 'react';
import { Modal } from './Modal';
import { Customer, OrderCreateInput, Product } from '../types';
import { Plus, Trash2 } from 'lucide-react';

interface OrderCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: OrderCreateInput) => Promise<void>;
  merchantId: number;
  customers: Customer[];
  products: Product[];
}

interface DraftItem {
  productId: number;
  quantity: number;
}

export const OrderCreateModal: React.FC<OrderCreateModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  merchantId,
  customers,
  products,
}) => {
  const [customerId, setCustomerId] = useState<number | ''>(
    customers.length > 0 ? customers[0].id : ''
  );
  const [items, setItems] = useState<DraftItem[]>([
    { productId: products.length > 0 ? products[0].id : 0, quantity: 1 },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addItemRow = () => {
    if (products.length === 0) return;
    setItems([...items, { productId: products[0].id, quantity: 1 }]);
  };

  const removeItemRow = (index: number) => {
    if (items.length <= 1) return;
    setItems(items.filter((_, i) => i !== index));
  };

  const updateItemRow = (index: number, field: 'productId' | 'quantity', val: number) => {
    const updated = [...items];
    updated[index] = { ...updated[index], [field]: val };
    setItems(updated);
  };

  // Preview estimated calculation for user clarity
  const previewTotal = items.reduce((sum, item) => {
    const prod = products.find((p) => p.id === item.productId);
    return sum + (prod ? prod.price * item.quantity : 0);
  }, 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerId) {
      setError('Please select a customer.');
      return;
    }
    if (items.length === 0) {
      setError('Order must contain at least one item.');
      return;
    }

    for (const item of items) {
      if (!item.productId || item.quantity <= 0) {
        setError('All items must have a valid product and quantity greater than 0.');
        return;
      }
      const prod = products.find((p) => p.id === item.productId);
      if (prod && item.quantity > prod.stock_quantity) {
        setError(
          `Requested quantity (${item.quantity}) for "${prod.name}" exceeds available stock (${prod.stock_quantity}).`
        );
        return;
      }
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onSubmit({
        merchant_id: merchantId,
        customer_id: Number(customerId),
        items: items.map((i) => ({
          product_id: i.productId,
          quantity: i.quantity,
        })),
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to place order.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create New Order" maxWidth="640px">
      <form onSubmit={handleSubmit}>
        <div className="modal-content">
          {error && (
            <div className="alert-box alert-error" style={{ marginBottom: '16px' }}>
              {error}
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Select Customer *</label>
            <select
              className="form-select"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value === '' ? '' : Number(e.target.value))}
              required
            >
              {customers.length === 0 ? (
                <option value="">No customers found</option>
              ) : (
                customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.email})
                  </option>
                ))
              )}
            </select>
          </div>

          <div style={{ marginTop: '20px', marginBottom: '12px' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '10px',
              }}
            >
              <label className="form-label" style={{ marginBottom: 0 }}>
                Order Line Items
              </label>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={addItemRow}
                disabled={products.length === 0}
              >
                <Plus size={14} /> Add Line Item
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {items.map((item, index) => {
                const selectedProd = products.find((p) => p.id === item.productId);
                return (
                  <div
                    key={index}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '3fr 1.2fr 1fr auto',
                      gap: '10px',
                      alignItems: 'center',
                      background: 'rgba(255, 255, 255, 0.02)',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <select
                      className="form-select"
                      value={item.productId}
                      onChange={(e) =>
                        updateItemRow(index, 'productId', Number(e.target.value))
                      }
                    >
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} - ₹{p.price} (Stock: {p.stock_quantity})
                        </option>
                      ))}
                    </select>

                    <input
                      type="number"
                      min="1"
                      className="form-input"
                      value={item.quantity}
                      onChange={(e) =>
                        updateItemRow(
                          index,
                          'quantity',
                          Math.max(1, parseInt(e.target.value, 10) || 1)
                        )
                      }
                    />

                    <span
                      className="mono"
                      style={{
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        color: 'var(--text-main)',
                      }}
                    >
                      ₹
                      {selectedProd
                        ? (selectedProd.price * item.quantity).toLocaleString()
                        : '0'}
                    </span>

                    <button
                      type="button"
                      className="btn btn-danger btn-sm"
                      onClick={() => removeItemRow(index)}
                      disabled={items.length <= 1}
                      style={{ padding: '6px' }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          <div
            style={{
              marginTop: '16px',
              padding: '12px 16px',
              background: 'rgba(99, 102, 241, 0.08)',
              border: '1px solid rgba(99, 102, 241, 0.2)',
              borderRadius: '8px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Estimated Total (computed server-side):
              </span>
            </div>
            <div className="mono" style={{ fontSize: '1.2rem', fontWeight: 700, color: '#818cf8' }}>
              ₹{previewTotal.toLocaleString()}
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
            {isSubmitting ? 'Creating Order...' : 'Submit Order'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
