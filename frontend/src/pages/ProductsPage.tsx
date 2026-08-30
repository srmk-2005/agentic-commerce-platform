import React, { useEffect, useState } from 'react';
import { Plus, Search, Edit2, Trash2, Tag, RefreshCw } from 'lucide-react';
import { Merchant, Product, ProductCreateInput, ProductUpdateInput } from '../types';
import { productService } from '../services/productService';
import { ProductModal } from '../components/ProductModal';
import { StockBadge } from '../components/Badge';

interface ProductsPageProps {
  currentMerchant: Merchant | null;
}

export const ProductsPage: React.FC<ProductsPageProps> = ({ currentMerchant }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  // Modals state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);

  const fetchProducts = async () => {
    if (!currentMerchant) return;
    try {
      setLoading(true);
      const filters: any = {
        merchant_id: currentMerchant.id,
      };
      if (searchTerm.trim()) filters.search = searchTerm.trim();
      if (selectedCategory) filters.category = selectedCategory;
      if (selectedStatus === 'active') filters.is_active = true;
      if (selectedStatus === 'inactive') filters.is_active = false;

      const data = await productService.getProducts(filters);
      setProducts(data);
    } catch (err) {
      console.error('Failed to load products:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [currentMerchant, searchTerm, selectedCategory, selectedStatus]);

  const handleCreateOrUpdate = async (data: ProductCreateInput | ProductUpdateInput) => {
    if (editingProduct) {
      await productService.updateProduct(editingProduct.id, data as ProductUpdateInput);
    } else {
      await productService.createProduct(data as ProductCreateInput);
    }
    await fetchProducts();
  };

  const handleDelete = async (productId: number, productName: string) => {
    if (window.confirm(`Are you sure you want to delete "${productName}"?`)) {
      try {
        await productService.deleteProduct(productId);
        await fetchProducts();
      } catch (err: any) {
        alert(err.message || 'Failed to delete product.');
      }
    }
  };

  const openAddModal = () => {
    setEditingProduct(null);
    setIsModalOpen(true);
  };

  const openEditModal = (product: Product) => {
    setEditingProduct(product);
    setIsModalOpen(true);
  };

  const categories = Array.from(new Set(products.map((p) => p.category))).filter(Boolean);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header & Quick Action Bar */}
      <div className="filter-bar">
        <div className="search-box">
          <Search size={18} color="var(--text-dim)" />
          <input
            type="text"
            placeholder="Search products by name, SKU, or category..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-actions">
          <select
            className="form-select"
            style={{ width: 'auto', minWidth: '150px' }}
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            <option value="Footwear">Footwear</option>
            <option value="Apparel">Apparel</option>
            <option value="Accessories">Accessories</option>
            <option value="Bags & Gear">Bags & Gear</option>
            {categories.map(
              (cat) =>
                !['Footwear', 'Apparel', 'Accessories', 'Bags & Gear'].includes(cat) && (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                )
            )}
          </select>

          <select
            className="form-select"
            style={{ width: 'auto', minWidth: '130px' }}
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
          >
            <option value="">All Status</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive</option>
          </select>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={fetchProducts}
            title="Refresh list"
          >
            <RefreshCw size={16} />
          </button>

          <button type="button" className="btn btn-primary" onClick={openAddModal}>
            <Plus size={18} /> Add Product
          </button>
        </div>
      </div>

      {/* Catalog Table */}
      <div className="glass-card" style={{ padding: '0', overflow: 'hidden' }}>
        <div className="table-container" style={{ border: 'none', borderRadius: '0' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>SKU</th>
                <th>Category</th>
                <th>Price</th>
                <th>Stock</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '40px' }}>
                    Loading catalog products...
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '40px' }}>
                    No products found matching the criteria.
                  </td>
                </tr>
              ) : (
                products.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <div className="cell-highlight">{p.name}</div>
                      {p.description && (
                        <div
                          style={{
                            fontSize: '0.775rem',
                            color: 'var(--text-dim)',
                            maxWidth: '300px',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                        >
                          {p.description}
                        </div>
                      )}
                    </td>
                    <td>
                      <span className="mono" style={{ fontSize: '0.8rem', color: '#a5b4fc' }}>
                        {p.sku}
                      </span>
                    </td>
                    <td>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          background: 'rgba(255, 255, 255, 0.04)',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '0.8rem',
                        }}
                      >
                        <Tag size={12} color="var(--text-dim)" />
                        {p.category}
                      </span>
                    </td>
                    <td className="mono" style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                      ₹{p.price.toLocaleString()}
                    </td>
                    <td>
                      <StockBadge quantity={p.stock_quantity} />
                    </td>
                    <td>
                      <span
                        className="status-pill"
                        style={
                          p.is_active
                            ? { background: 'rgba(16, 185, 129, 0.12)', color: '#34d399' }
                            : { background: 'rgba(148, 163, 184, 0.12)', color: '#94a3b8' }
                        }
                      >
                        {p.is_active ? 'Active' : 'Archived'}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '8px' }}>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => openEditModal(p)}
                          title="Edit product"
                        >
                          <Edit2 size={14} />
                        </button>
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDelete(p.id, p.name)}
                          title="Delete product"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Product Modal */}
      {currentMerchant && (
        <ProductModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSubmit={handleCreateOrUpdate}
          product={editingProduct}
          merchantId={currentMerchant.id}
        />
      )}
    </div>
  );
};
