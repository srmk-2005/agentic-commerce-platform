import { request } from './api';
import { Order, OrderCreateInput, OrderStatus } from '../types';

export interface OrderFilters {
  merchant_id?: number;
  customer_id?: number;
  status?: OrderStatus;
  skip?: number;
  limit?: number;
}

export const orderService = {
  getOrders: (filters: OrderFilters = {}): Promise<Order[]> => {
    const params = new URLSearchParams();
    if (filters.merchant_id !== undefined) params.append('merchant_id', filters.merchant_id.toString());
    if (filters.customer_id !== undefined) params.append('customer_id', filters.customer_id.toString());
    if (filters.status) params.append('status', filters.status);
    if (filters.skip !== undefined) params.append('skip', filters.skip.toString());
    if (filters.limit !== undefined) params.append('limit', filters.limit.toString());

    const queryString = params.toString() ? `?${params.toString()}` : '';
    return request<Order[]>(`/orders${queryString}`);
  },

  getOrder: (id: number): Promise<Order> => {
    return request<Order>(`/orders/${id}`);
  },

  createOrder: (data: OrderCreateInput): Promise<Order> => {
    return request<Order>('/orders', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  updateOrderStatus: (id: number, status: OrderStatus): Promise<Order> => {
    return request<Order>(`/orders/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },
};
