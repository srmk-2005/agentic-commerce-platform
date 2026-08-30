import { request } from './api';
import {
  AgentAnalysisResponse,
  AgentChatRequest,
  AgentChatResponse,
  AgentSummaryMetrics,
} from '../types';

export const agentService = {
  analyzeStore: (merchantId: number, userRequest?: string): Promise<AgentAnalysisResponse> => {
    return request<AgentAnalysisResponse>('/agent/analyze', {
      method: 'POST',
      body: JSON.stringify({
        merchant_id: merchantId,
        request: userRequest || 'Analyze store product catalog and sales for revenue opportunities',
      }),
    });
  },

  chatWithAgent: (data: AgentChatRequest): Promise<AgentChatResponse> => {
    return request<AgentChatResponse>('/agent/chat', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getMetrics: (merchantId: number): Promise<AgentSummaryMetrics> => {
    return request<AgentSummaryMetrics>(`/agent/metrics/${merchantId}`);
  },
};
