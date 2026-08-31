import { request } from './api';
import type {
  AgentCommerceContract,
  AgentCommerceStats,
  AgentMessage,
  AgentResponse,
  CommerceReadinessResponse,
  SessionResponse,
  SessionTimelineResponse,
} from '../types';

export const agentCommerceService = {
  /**
   * Start a new stateful Agent Commerce Session with a trace ID.
   */
  async createSession(merchantId: number = 1, buyerId: string = 'demo_ai_buyer'): Promise<SessionResponse> {
    return request<SessionResponse>('/agent-commerce/sessions', {
      method: 'POST',
      body: JSON.stringify({ merchant_id: merchantId, buyer_id: buyerId }),
    });
  },

  /**
   * Get session status.
   */
  async getSession(sessionId: string): Promise<SessionResponse> {
    return request<SessionResponse>(`/agent-commerce/sessions/${sessionId}`);
  },

  /**
   * Get transaction timeline with complete chronological trace events.
   */
  async getSessionTimeline(sessionId: string): Promise<SessionTimelineResponse> {
    return request<SessionTimelineResponse>(`/agent-commerce/sessions/${sessionId}/timeline`);
  },

  /**
   * Get merchant discovery contract and capabilities.
   */
  async getMerchantContract(merchantId: number = 1): Promise<AgentCommerceContract> {
    return request<AgentCommerceContract>(`/agent-commerce/merchants/${merchantId}`);
  },

  /**
   * Dispatch standardized agent-to-agent protocol message.
   */
  async dispatchMessage(msg: AgentMessage): Promise<AgentResponse> {
    return request<AgentResponse>('/agent-commerce/message', {
      method: 'POST',
      body: JSON.stringify(msg),
    });
  },

  /**
   * Get deterministic AI Commerce Readiness score and weighted checklist.
   */
  async getReadiness(merchantId: number = 1): Promise<CommerceReadinessResponse> {
    return request<CommerceReadinessResponse>(`/agent-commerce/readiness/${merchantId}`);
  },

  /**
   * Get aggregate metrics for AI commerce platform overview.
   */
  async getStats(merchantId?: number): Promise<AgentCommerceStats> {
    const query = merchantId ? `?merchant_id=${merchantId}` : '';
    return request<AgentCommerceStats>(`/agent-commerce/stats${query}`);
  },
};
