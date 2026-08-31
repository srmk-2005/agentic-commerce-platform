import { request } from './api';
import {
  AICatalogResponse,
  AIMerchantManifest,
  AIMerchantProfile,
  AIOrderResponse,
  AIProduct,
  AISearchResponse,
} from '../types';

export const commerceService = {
  getManifest: (merchantId: number): Promise<AIMerchantManifest> => {
    return request<AIMerchantManifest>(`/ai/merchant/${merchantId}/manifest`);
  },

  getProfile: (merchantId: number): Promise<AIMerchantProfile> => {
    return request<AIMerchantProfile>(`/ai/merchant/${merchantId}/profile`);
  },

  getCatalog: (params?: {
    merchant_id?: number;
    category?: string;
    search?: string;
    min_price?: number;
    max_price?: number;
    in_stock?: boolean;
  }): Promise<AICatalogResponse> => {
    const query = new URLSearchParams();
    if (params?.merchant_id) query.append('merchant_id', params.merchant_id.toString());
    if (params?.category) query.append('category', params.category);
    if (params?.search) query.append('search', params.search);
    if (params?.min_price !== undefined) query.append('min_price', params.min_price.toString());
    if (params?.max_price !== undefined) query.append('max_price', params.max_price.toString());
    if (params?.in_stock !== undefined) query.append('in_stock', params.in_stock.toString());

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return request<AICatalogResponse>(`/ai/catalog${queryString}`);
  },

  getProduct: (productId: number): Promise<AIProduct> => {
    return request<AIProduct>(`/ai/products/${productId}`);
  },

  searchProducts: (params?: {
    query?: string;
    merchant_id?: number;
    category?: string;
    min_price?: number;
    max_price?: number;
  }): Promise<AISearchResponse> => {
    const query = new URLSearchParams();
    if (params?.query) query.append('query', params.query);
    if (params?.merchant_id) query.append('merchant_id', params.merchant_id.toString());
    if (params?.category) query.append('category', params.category);
    if (params?.min_price !== undefined) query.append('min_price', params.min_price.toString());
    if (params?.max_price !== undefined) query.append('max_price', params.max_price.toString());

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return request<AISearchResponse>(`/ai/search${queryString}`);
  },

  createOrder: (
    orderData: { merchant_id: number; items: { product_id: number; quantity: number }[]; idempotency_key?: string },
    idempotencyKey?: string
  ): Promise<AIOrderResponse> => {
    const headers: Record<string, string> = {};
    if (idempotencyKey || orderData.idempotency_key) {
      headers['Idempotency-Key'] = idempotencyKey || orderData.idempotency_key!;
    }
    return request<AIOrderResponse>('/ai/orders', {
      method: 'POST',
      headers,
      body: JSON.stringify(orderData),
    });
  },
};
