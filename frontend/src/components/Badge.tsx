import React from 'react';
import { OrderStatus } from '../types';

interface OrderStatusBadgeProps {
  status: OrderStatus;
}

export const OrderStatusBadge: React.FC<OrderStatusBadgeProps> = ({ status }) => {
  switch (status) {
    case 'CONFIRMED':
      return <span className="status-pill status-confirmed">Confirmed</span>;
    case 'PENDING':
      return <span className="status-pill status-pending">Pending</span>;
    case 'CANCELLED':
      return <span className="status-pill status-cancelled">Cancelled</span>;
    case 'FAILED':
      return <span className="status-pill status-failed">Failed</span>;
    default:
      return <span className="status-pill">{status}</span>;
  }
};

interface StockBadgeProps {
  quantity: number;
}

export const StockBadge: React.FC<StockBadgeProps> = ({ quantity }) => {
  if (quantity === 0) {
    return <span className="stock-tag stock-out">Out of Stock</span>;
  }
  if (quantity <= 15) {
    return <span className="stock-tag stock-low">{quantity} in stock (Low)</span>;
  }
  return <span className="stock-tag stock-good">{quantity} in stock</span>;
};
