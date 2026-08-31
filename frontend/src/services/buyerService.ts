import { request } from './api';
import { BuyerChatResponse, BuyerSimulationResponse } from '../types';

export const buyerService = {
  chat: (merchantId: number, message: string): Promise<BuyerChatResponse> => {
    return request<BuyerChatResponse>('/buyer/chat', {
      method: 'POST',
      body: JSON.stringify({ merchant_id: merchantId, message }),
    });
  },

  simulateOrder: (
    merchantId: number,
    productId: number,
    quantity: number = 1,
    idempotencyKey?: string
  ): Promise<BuyerSimulationResponse> => {
    return request<BuyerSimulationResponse>('/buyer/simulate-order', {
      method: 'POST',
      body: JSON.stringify({
        merchant_id: merchantId,
        product_id: productId,
        quantity,
        idempotency_key: idempotencyKey,
      }),
    });
  },
};
