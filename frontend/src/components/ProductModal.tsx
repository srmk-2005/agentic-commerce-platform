import React, { useEffect, useState } from 'react';
import { Modal } from './Modal';
import { Product, ProductCreateInput, ProductUpdateInput } from '../types';

interface ProductModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ProductCreateInput | ProductUpdateInput) => Promise<void>;
  product?: Product | null;
  merchantId: number;
}

export const ProductModal: React.FC<ProductModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  product,
  merchantId,
}) => {
  const [name, setName] = useState('');
  const [sku, setSku] = useState('');
  const [category, setCategory] = useState('Footwear');
  const [price, setPrice] = useState<number | ''>('');
  const [stockQuantity, setStockQuantity] = useState<number | ''>('');
  const [description, setDescription] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (product) {
      setName(product.name);
      setSku(product.sku);
      setCategory(product.category);
      setPrice(product.price);
      setStockQuantity(product.stock_quantity);
      setDescription(product.description || '');
      setIsActive(product.is_active);
    } else {
      setName('');
      setSku('');
      setCategory('Footwear');
      setPrice('');
      setStockQuantity('');
      setDescription('');
      setIsActive(true);
    }
    setError(null);
  }, [product, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Product title is required.');
      return;
    }
    if (!sku.trim()) {
      setError('SKU identifier is required.');
      return;
    }
    if (price === '' || Number(price) < 0) {
      setError('Valid non-negative price is required.');
      return;
    }
    if (stockQuantity === '' || Number(stockQuantity) < 0) {
      setError('Valid non-negative stock quantity is required.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      if (product) {
        await onSubmit({
          name: name.trim(),
          sku: sku.trim(),
          category: category.trim(),
          price: Number(price),
          stock_quantity: Number(stockQuantity),
          description: description.trim() || undefined,
          is_active: isActive,
        });
      } else {
        await onSubmit({
          merchant_id: merchantId,
          name: name.trim(),
          sku: sku.trim(),
          category: category.trim(),
          price: Number(price),
          stock_quantity: Number(stockQuantity),
          description: description.trim() || undefined,
          is_active: isActive,
        });
      }
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save product');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={product ? 'Edit Product' : 'Add New Product'}
    >
      <form onSubmit={handleSubmit}>
        <div className="modal-content">
          {error && (
            <div className="alert-box alert-error" style={{ marginBottom: '16px' }}>
              {error}
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Product Title *</label>
            <input
              type="text"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Carbon-Pro Running Shoes"
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">SKU *</label>
              <input
                type="text"
                className="form-input"
                value={sku}
                onChange={(e) => setSku(e.target.value)}
                placeholder="e.g. CSS-RUN-003"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Category *</label>
              <select
                className="form-select"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                <option value="Footwear">Footwear</option>
                <option value="Apparel">Apparel</option>
                <option value="Accessories">Accessories</option>
                <option value="Bags & Gear">Bags & Gear</option>
                <option value="Equipment">Equipment</option>
                <option value="Nutrition">Nutrition</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Price (INR ₹) *</label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="form-input"
                value={price}
                onChange={(e) => setPrice(e.target.value === '' ? '' : parseFloat(e.target.value))}
                placeholder="2499.00"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Stock Quantity *</label>
              <input
                type="number"
                min="0"
                className="form-input"
                value={stockQuantity}
                onChange={(e) =>
                  setStockQuantity(e.target.value === '' ? '' : parseInt(e.target.value, 10))
                }
                placeholder="50"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              className="form-textarea"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detailed product specifications and materials..."
            />
          </div>

          <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '10px' }}>
            <input
              type="checkbox"
              id="isActive"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              style={{ width: '16px', height: '16px', accentColor: 'var(--accent-primary)' }}
            />
            <label htmlFor="isActive" className="form-label" style={{ marginBottom: 0, cursor: 'pointer' }}>
              List product as Active in catalog
            </label>
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : product ? 'Save Changes' : 'Create Product'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
