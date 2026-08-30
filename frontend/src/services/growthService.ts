import { request } from './api';
import { ActionProposal, MerchantAiPolicy } from '../types';

export const growthService = {
  proposeAction: (data: {
    merchant_id: number;
    action_type: string;
    opportunity_id?: string;
    title: string;
    description?: string;
    campaign_type?: string;
    target_product_ids: number[];
    primary_product_id?: number;
    recommended_product_ids?: number[];
    discount_type?: string;
    discount_value: number;
    campaign_duration_days?: number;
    expected_benefit?: string;
    reasoning?: string;
    risk_level?: string;
  }): Promise<ActionProposal> => {
    return request<ActionProposal>('/growth/actions/propose', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getPolicy: (merchantId: number): Promise<MerchantAiPolicy> => {
    return request<MerchantAiPolicy>(`/growth/policies/${merchantId}`);
  },

  updatePolicy: (merchantId: number, data: Partial<MerchantAiPolicy>): Promise<MerchantAiPolicy> => {
    return request<MerchantAiPolicy>(`/growth/policies/${merchantId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
};
