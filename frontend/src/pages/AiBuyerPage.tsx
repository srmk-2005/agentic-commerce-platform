import React, { useEffect, useRef, useState } from 'react';
import { BuyerProductOption, Merchant, AIOrderResponse } from '../types';
import { buyerService } from '../services/buyerService';
import {
  Bot,
  Send,
  Sparkles,
  ShoppingBag,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Cpu,
  ArrowRight,
  PackageCheck,
  Clock,
  Layers,
} from 'lucide-react';

interface AiBuyerPageProps {
  currentMerchant: Merchant | null;
}

interface BuyerMessage {
  id: string;
  sender: 'user' | 'buyer_agent';
  text: string;
  candidates?: BuyerProductOption[];
  selectedProduct?: BuyerProductOption | null;
  orderCreated?: AIOrderResponse | null;
  executionSteps?: string[];
  timestamp: Date;
}

const QUICK_BUYER_PROMPTS = [
  'I need running shoes under ₹3000.',
  'Find me a sports t-shirt under ₹1000.',
  'Find high performance marathon shoes.',
  'Buy the Velocity Running Shoes.',
  'Find accessories under ₹800.',
];

export const AiBuyerPage: React.FC<AiBuyerPageProps> = ({ currentMerchant }) => {
  const [messages, setMessages] = useState<BuyerMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<BuyerProductOption | null>(null);
  const [orderQuantity, setOrderQuantity] = useState<number>(1);
  const [orderingLoading, setOrderingLoading] = useState(false);
  const [latestOrder, setLatestOrder] = useState<AIOrderResponse | null>(null);
  const [orderNotice, setOrderNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initial welcome message
    setMessages([
      {
        id: 'init-buyer',
        sender: 'buyer_agent',
        text: "👋 Hello! I am an **External AI Buyer Agent**.\n\nI can autonomously query the merchant's machine-readable catalog, rank products deterministically, verify real-time stock, and prepare orders without accessing the merchant's internal database.",
        timestamp: new Date(),
      },
    ]);
  }, [currentMerchant]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || !currentMerchant || loading) return;

    const userMsg: BuyerMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await buyerService.chat(currentMerchant.id, text);

      const agentMsg: BuyerMessage = {
        id: `buyer-${Date.now()}`,
        sender: 'buyer_agent',
        text: response.response,
        candidates: response.candidates,
        selectedProduct: response.selected_product,
        orderCreated: response.order_created,
        executionSteps: response.execution_steps,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, agentMsg]);

      if (response.selected_product) {
        setSelectedProduct(response.selected_product);
      }
      if (response.order_created) {
        setLatestOrder(response.order_created);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'buyer_agent',
          text: `⚠️ **AI Buyer Communication Error:** ${err.message || 'Failed to reach AI Commerce interface.'}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrder = async (product: BuyerProductOption) => {
    if (!currentMerchant) return;
    try {
      setOrderingLoading(true);
      setOrderNotice(null);

      const idempotencyKey = `buyer-sim-key-${Date.now()}`;
      const simRes = await buyerService.simulateOrder(
        currentMerchant.id,
        product.id,
        orderQuantity,
        idempotencyKey
      );

      if (simRes.success && simRes.order) {
        setLatestOrder(simRes.order);
        setOrderNotice({
          type: 'success',
          message: `Order #${simRes.order.order_id} created successfully for ₹${simRes.order.total_amount}.`,
        });

        // Add confirmation to chat
        setMessages((prev) => [
          ...prev,
          {
            id: `order-conf-${Date.now()}`,
            sender: 'buyer_agent',
            text: `🎉 **Order #${simRes.order!.order_id} Placed!**\n\n${simRes.explainability}`,
            orderCreated: simRes.order,
            timestamp: new Date(),
          },
        ]);
      } else {
        setOrderNotice({
          type: 'error',
          message: simRes.error_message || 'Order simulation failed.',
        });
      }
    } catch (err: any) {
      setOrderNotice({
        type: 'error',
        message: err.message || 'Failed to submit order.',
      });
    } finally {
      setOrderingLoading(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '20px', height: 'calc(100vh - 140px)' }}>
      {/* Left Pane: Conversational AI Buyer Chat */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', height: '100%' }}>
        {/* Header */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingBottom: '8px',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Bot size={20} color="#38BDF8" /> Simulated AI Buyer Agent
            </h2>
            <p style={{ fontSize: '0.775rem', color: 'var(--text-dim)' }}>
              Demonstrates an external client interacting with the merchant's machine-readable commerce interface.
            </p>
          </div>
          <span
            className="badge-tag"
            style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.3)' }}
          >
            <Cpu size={13} /> LangGraph Agent
          </span>
        </div>

        {/* Chat History */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '18px',
            paddingRight: '6px',
          }}
        >
          {messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                gap: '8px',
              }}
            >
              <div
                style={{
                  maxWidth: msg.sender === 'user' ? '75%' : '90%',
                  padding: '14px 18px',
                  borderRadius: '14px',
                  background:
                    msg.sender === 'user'
                      ? 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)'
                      : 'rgba(15, 23, 42, 0.85)',
                  border: msg.sender === 'user' ? 'none' : '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.875rem',
                  lineHeight: '1.5',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {msg.text}
              </div>

              {/* Execution Steps Trace */}
              {msg.executionSteps && msg.executionSteps.length > 0 && (
                <div
                  style={{
                    width: '90%',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid rgba(56, 189, 248, 0.15)',
                    fontSize: '0.75rem',
                    color: 'var(--text-dim)',
                  }}
                >
                  <div style={{ fontWeight: 700, color: '#38bdf8', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Layers size={12} /> Autonomous Execution Trace:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '16px' }}>
                    {msg.executionSteps.map((step, idx) => (
                      <li key={idx} style={{ marginTop: '2px' }}>{step}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Candidate Products Returned */}
              {msg.candidates && msg.candidates.length > 0 && (
                <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
                  {msg.candidates.map((cand) => (
                    <div
                      key={cand.id}
                      className="glass-card"
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '12px 14px',
                        background: 'rgba(30, 41, 59, 0.6)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '0.9rem' }}>
                          {cand.name}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                          Category: {cand.category} • Score: {cand.relevance_score}
                        </div>
                        {cand.reason && (
                          <div style={{ fontSize: '0.725rem', color: '#34d399', marginTop: '2px' }}>
                            {cand.reason}
                          </div>
                        )}
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div className="mono" style={{ fontWeight: 700, color: '#38bdf8', fontSize: '0.95rem' }}>
                          ₹{cand.price.toLocaleString()}
                        </div>
                        <button
                          type="button"
                          className="btn btn-primary btn-sm"
                          onClick={() => setSelectedProduct(cand)}
                          style={{ gap: '4px', fontSize: '0.75rem', padding: '4px 10px' }}
                        >
                          Select <ArrowRight size={12} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-dim)', fontSize: '0.8rem' }}>
              <RefreshCw size={14} className="spinning" />
              <span>AI Buyer is querying merchant manifest and catalog endpoints...</span>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Quick Suggestion Chips */}
        <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '2px' }}>
          {QUICK_BUYER_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => handleSendMessage(prompt)}
              disabled={loading}
              style={{ whiteSpace: 'nowrap', fontSize: '0.725rem', borderRadius: '16px', padding: '4px 10px' }}
            >
              <Sparkles size={11} color="#38bdf8" /> {prompt}
            </button>
          ))}
        </div>

        {/* Prompt Input Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          style={{
            display: 'flex',
            gap: '8px',
            background: 'rgba(13, 19, 33, 0.9)',
            padding: '8px 12px',
            borderRadius: '10px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <input
            type="text"
            className="form-input"
            style={{ border: 'none', background: 'transparent', boxShadow: 'none', fontSize: '0.875rem' }}
            placeholder="Ask AI Buyer (e.g. 'I need running shoes under ₹3000')..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !inputMessage.trim()}
            style={{ padding: '6px 14px' }}
          >
            <Send size={15} />
          </button>
        </form>
      </div>

      {/* Right Pane: Checkout Preparation & Order Receipt */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Selection & Checkout Drawer */}
        <div
          className="glass-card"
          style={{
            padding: '20px',
            background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%)',
            borderColor: selectedProduct ? 'rgba(56, 189, 248, 0.4)' : 'var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <ShoppingBag size={18} color="#38BDF8" />
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>
              AI Buyer Order Preparation
            </h3>
          </div>

          {selectedProduct ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div
                style={{
                  padding: '12px',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                  Target Product
                </div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
                  {selectedProduct.name}
                </div>
                <div style={{ fontSize: '0.8rem', color: '#34d399', marginTop: '2px' }}>
                  ✓ Real-time status: {selectedProduct.availability} ({selectedProduct.stock_quantity} units available)
                </div>
              </div>

              {/* Pricing & Quantity */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <div style={{ fontSize: '0.725rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                    Unit Price
                  </div>
                  <div className="mono" style={{ fontSize: '1rem', fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>
                    ₹{selectedProduct.price.toLocaleString()}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.725rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                    Quantity
                  </div>
                  <select
                    className="form-input"
                    value={orderQuantity}
                    onChange={(e) => setOrderQuantity(Number(e.target.value))}
                    style={{ marginTop: '2px', padding: '4px 8px', fontSize: '0.85rem' }}
                    disabled={orderingLoading}
                  >
                    {[1, 2, 3, 4, 5].map((q) => (
                      <option key={q} value={q}>
                        {q} unit(s)
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  background: 'rgba(56, 189, 248, 0.08)',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                }}
              >
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)' }}>
                  Total Order Amount:
                </span>
                <span className="mono" style={{ fontSize: '1.1rem', fontWeight: 800, color: '#38bdf8' }}>
                  ₹{(selectedProduct.price * orderQuantity).toLocaleString()}
                </span>
              </div>

              {/* Order Submission Button */}
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => handleCreateOrder(selectedProduct)}
                disabled={orderingLoading}
                style={{
                  gap: '6px',
                  padding: '10px',
                  background: 'linear-gradient(135deg, #0284C7 0%, #2563EB 100%)',
                  fontWeight: 700,
                }}
              >
                {orderingLoading ? <RefreshCw size={16} className="spinning" /> : <PackageCheck size={16} />}
                Create Order as AI Buyer
              </button>

              <div style={{ fontSize: '0.725rem', color: 'var(--text-dim)', textAlign: 'center' }}>
                Protected with automated Idempotency-Key & server-side pricing.
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '36px 12px', color: 'var(--text-dim)' }}>
              <Bot size={32} color="#6366F1" style={{ margin: '0 auto 10px', opacity: 0.6 }} />
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                No product selected yet.
              </div>
              <div style={{ fontSize: '0.75rem', marginTop: '4px' }}>
                Search for products in the chat on the left and click <strong>Select</strong>.
              </div>
            </div>
          )}
        </div>

        {/* Order Notification / Receipt Card */}
        {orderNotice && (
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '8px',
              fontSize: '0.8rem',
              background: orderNotice.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              border: `1px solid ${orderNotice.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
              color: orderNotice.type === 'success' ? '#6ee7b7' : '#fca5a5',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            {orderNotice.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            <span>{orderNotice.message}</span>
          </div>
        )}

        {latestOrder && (
          <div
            className="glass-card"
            style={{
              padding: '18px',
              background: 'rgba(16, 185, 129, 0.04)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#34d399', textTransform: 'uppercase' }}>
                AI Order Receipt
              </span>
              <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                Order #{latestOrder.order_id}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span style={{ color: 'var(--text-dim)' }}>Status:</span>
              <strong style={{ color: '#fbbf24' }}>{latestOrder.status}</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span style={{ color: 'var(--text-dim)' }}>Total Amount:</span>
              <strong className="mono" style={{ color: 'var(--text-main)' }}>
                ₹{latestOrder.total_amount.toLocaleString()} {latestOrder.currency}
              </strong>
            </div>

            {/* Payment Phase 4 Disclaimer */}
            <div
              style={{
                marginTop: '6px',
                padding: '10px 12px',
                borderRadius: '6px',
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.25)',
                fontSize: '0.775rem',
                color: '#fbbf24',
              }}
            >
              <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={12} /> Payment: NOT_AVAILABLE
              </div>
              <div style={{ marginTop: '2px', color: 'var(--text-muted)' }}>
                Payment simulation with Razorpay test mode will be added in Phase 5.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
