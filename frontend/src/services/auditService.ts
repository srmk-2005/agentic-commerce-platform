import { request } from './api';
import { AuditLog } from '../types';

export const auditService = {
  getLogs: (params?: { merchant_id?: number; limit?: number }): Promise<AuditLog[]> => {
    const query = new URLSearchParams();
    if (params?.merchant_id) query.append('merchant_id', params.merchant_id.toString());
    if (params?.limit) query.append('limit', params.limit.toString());
    const queryString = query.toString() ? `?${query.toString()}` : '';
    return request<AuditLog[]>(`/audit/logs${queryString}`);
  },
};
