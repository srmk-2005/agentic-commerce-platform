import { request } from './api';
import { Customer, CustomerCreateInput } from '../types';

export const customerService = {
  getCustomers: (skip = 0, limit = 100): Promise<Customer[]> => {
    return request<Customer[]>(`/customers?skip=${skip}&limit=${limit}`);
  },

  getCustomer: (id: number): Promise<Customer> => {
    return request<Customer>(`/customers/${id}`);
  },

  createCustomer: (data: CustomerCreateInput): Promise<Customer> => {
    return request<Customer>('/customers', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};
