import { request } from './api';
import { Approval, ApprovalStatus } from '../types';

export const approvalService = {
  getApprovals: (params?: { merchant_id?: number; status?: ApprovalStatus }): Promise<Approval[]> => {
    const query = new URLSearchParams();
    if (params?.merchant_id) query.append('merchant_id', params.merchant_id.toString());
    if (params?.status) query.append('status', params.status);
    const queryString = query.toString() ? `?${query.toString()}` : '';
    return request<Approval[]>(`/approvals${queryString}`);
  },

  getApproval: (approvalId: number): Promise<Approval> => {
    return request<Approval>(`/approvals/${approvalId}`);
  },

  approve: (approvalId: number, reviewedBy: string = 'Merchant Owner'): Promise<any> => {
    return request<any>(`/approvals/${approvalId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ reviewed_by: reviewedBy }),
    });
  },

  reject: (approvalId: number, reason?: string, reviewedBy: string = 'Merchant Owner'): Promise<any> => {
    return request<any>(`/approvals/${approvalId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason, reviewed_by: reviewedBy }),
    });
  },

  simulateFailure: (approvalId: number, reviewedBy: string = 'Merchant Owner'): Promise<any> => {
    return request<any>(`/approvals/${approvalId}/simulate-failure`, {
      method: 'POST',
      body: JSON.stringify({ reviewed_by: reviewedBy }),
    });
  },
};
