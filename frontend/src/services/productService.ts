import { request } from './api';
import { Product, ProductCreateInput, ProductUpdateInput } from '../types';

export interface ProductFilters {
  merchant_id?: number;
  category?: string;
  is_active?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}

export const productService = {
  getProducts: (filters: ProductFilters = {}): Promise<Product[]> => {
    const params = new URLSearchParams();
    if (filters.merchant_id !== undefined) params.append('merchant_id', filters.merchant_id.toString());
    if (filters.category) params.append('category', filters.category);
    if (filters.is_active !== undefined) params.append('is_active', filters.is_active.toString());
    if (filters.search) params.append('search', filters.search);
    if (filters.skip !== undefined) params.append('skip', filters.skip.toString());
    if (filters.limit !== undefined) params.append('limit', filters.limit.toString());

    const queryString = params.toString() ? `?${params.toString()}` : '';
    return request<Product[]>(`/products${queryString}`);
  },

  getProduct: (id: number): Promise<Product> => {
    return request<Product>(`/products/${id}`);
  },

  createProduct: (data: ProductCreateInput): Promise<Product> => {
    return request<Product>('/products', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  updateProduct: (id: number, data: ProductUpdateInput): Promise<Product> => {
    return request<Product>(`/products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  deleteProduct: (id: number): Promise<{ message: string }> => {
    return request<{ message: string }>(`/products/${id}`, {
      method: 'DELETE',
    });
  },
};
