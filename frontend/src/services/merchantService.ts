import { request } from './api';
import { Merchant, MerchantCreateInput, MerchantUpdateInput } from '../types';

export const merchantService = {
  getMerchants: (skip = 0, limit = 100): Promise<Merchant[]> => {
    return request<Merchant[]>(`/merchants?skip=${skip}&limit=${limit}`);
  },

  getMerchant: (id: number): Promise<Merchant> => {
    return request<Merchant>(`/merchants/${id}`);
  },

  createMerchant: (data: MerchantCreateInput): Promise<Merchant> => {
    return request<Merchant>('/merchants', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  updateMerchant: (id: number, data: MerchantUpdateInput): Promise<Merchant> => {
    return request<Merchant>(`/merchants/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  deleteMerchant: (id: number): Promise<{ message: string }> => {
    return request<{ message: string }>(`/merchants/${id}`, {
      method: 'DELETE',
    });
  },
};
