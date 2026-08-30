import { request } from './api';
import { Campaign, CampaignStatus } from '../types';

export const campaignService = {
  getCampaigns: (params?: { merchant_id?: number; status?: CampaignStatus }): Promise<Campaign[]> => {
    const query = new URLSearchParams();
    if (params?.merchant_id) query.append('merchant_id', params.merchant_id.toString());
    if (params?.status) query.append('status', params.status);
    const queryString = query.toString() ? `?${query.toString()}` : '';
    return request<Campaign[]>(`/campaigns${queryString}`);
  },

  getCampaign: (campaignId: number): Promise<Campaign> => {
    return request<Campaign>(`/campaigns/${campaignId}`);
  },

  pauseCampaign: (campaignId: number): Promise<Campaign> => {
    return request<Campaign>(`/campaigns/${campaignId}/pause`, {
      method: 'POST',
    });
  },

  activateCampaign: (campaignId: number): Promise<Campaign> => {
    return request<Campaign>(`/campaigns/${campaignId}/activate`, {
      method: 'POST',
    });
  },
};
