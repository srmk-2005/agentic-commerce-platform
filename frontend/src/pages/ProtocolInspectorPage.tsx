import React, { useState } from 'react';
import {
  Cpu,
  RefreshCw,
  Send,
  Sliders,
} from 'lucide-react';
import { agentCommerceService } from '../services/agentCommerceService';
import type { AgentMessage, AgentResponse, ProtocolAction } from '../types';

export const ProtocolInspectorPage: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>('acs_demo_session');
  const [buyerId, setBuyerId] = useState<string>('inspector_ai_buyer');
  const [merchantId, setMerchantId] = useState<number>(1);
  const [selectedAction, setSelectedAction] = useState<ProtocolAction>('SEARCH');
  const [payloadInput, setPayloadInput] = useState<string>(
    JSON.stringify({ query: 'running', max_price: 3000, in_stock_only: true }, null, 2)
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<AgentResponse | null>(null);

  const handleActionChange = (action: ProtocolAction) => {
    setSelectedAction(action);
    switch (action) {
      case 'DISCOVER':
        setPayloadInput(JSON.stringify({}, null, 2));
        break;
      case 'SEARCH':
        setPayloadInput(JSON.stringify({ query: 'running', max_price: 3000, in_stock_only: true }, null, 2));
        break;
      case 'GET_PRODUCT':
        setPayloadInput(JSON.stringify({ product_id: 1 }, null, 2));
        break;
      case 'CHECK_INVENTORY':
        setPayloadInput(JSON.stringify({ product_id: 1, quantity: 1 }, null, 2));
        break;
      case 'CREATE_ORDER':
        setPayloadInput(
          JSON.stringify(
            {
              product_id: 1,
              quantity: 1,
              idempotency_key: `inspector-ord-${Date.now()}`,
            },
            null,
            2
          )
        );
        break;
      case 'PROPOSE_PAYMENT':
        setPayloadInput(JSON.stringify({ order_id: 1 }, null, 2));
        break;
      case 'GET_PAYMENT_STATUS':
        setPayloadInput(JSON.stringify({ payment_intent_id: 1 }, null, 2));
        break;
    }
  };

  const handleSendProtocolMessage = async () => {
    try {
      setLoading(true);
      let parsedPayload = {};
      try {
        parsedPayload = JSON.parse(payloadInput);
      } catch (err: any) {
        alert('Invalid JSON in payload: ' + err.message);
        setLoading(false);
        return;
      }

      // If session is demo, ensure it exists or create one
      let activeSessionId = sessionId;
      if (!activeSessionId || activeSessionId.includes('demo')) {
        try {
          const sess = await agentCommerceService.createSession(merchantId, buyerId);
          activeSessionId = sess.session_id;
          setSessionId(activeSessionId);
        } catch {
          // fallback
        }
      }

      const msg: AgentMessage = {
        protocol_version: '1.0',
        message_id: `msg_insp_${Date.now()}`,
        session_id: activeSessionId,
        trace_id: `trace_insp_${Date.now()}`,
        sender: { type: 'AI_BUYER', id: buyerId },
        recipient: { type: 'MERCHANT', id: String(merchantId) },
        action: selectedAction,
        payload: parsedPayload,
      };

      const res = await agentCommerceService.dispatchMessage(msg);
      setResponse(res);
    } catch (err: any) {
      console.error('Failed to dispatch message:', err);
      setResponse({
        success: false,
        protocol_version: '1.0',
        message_id: `err_${Date.now()}`,
        session_id: sessionId,
        trace_id: 'error_trace',
        action: selectedAction,
        error: { code: 'NETWORK_ERROR', message: err.message || 'Request failed' },
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div
        className="glass-card"
        style={{
          padding: '20px 24px',
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sliders size={22} color="#38BDF8" />
          <div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Protocol Inspector & Message Debugger
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Inspect raw canonical JSON protocol messages exchanged between External AI Buyers and the Mercora Commerce Agent.
            </p>
          </div>
        </div>
      </div>

      {/* Main Two-Column Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(350px, 1fr) minmax(350px, 1fr)', gap: '20px' }}>
        {/* Left Column: Message Dispatcher Form */}
        <div
          className="glass-card"
          style={{
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Agent Message Builder
            </span>
            <span className="mono" style={{ fontSize: '0.725rem', color: '#818CF8', background: 'rgba(99, 102, 241, 0.1)', padding: '2px 8px', borderRadius: '6px' }}>
              protocol: 1.0
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div>
              <label style={{ fontSize: '0.725rem', color: 'var(--text-dim)', marginBottom: '4px', display: 'block' }}>
                Buyer Agent ID
              </label>
              <input
                type="text"
                className="form-input"
                value={buyerId}
                onChange={(e) => setBuyerId(e.target.value)}
                style={{ fontSize: '0.8rem', padding: '6px 10px' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.725rem', color: 'var(--text-dim)', marginBottom: '4px', display: 'block' }}>
                Target Merchant ID
              </label>
              <input
                type="number"
                className="form-input"
                value={merchantId}
                onChange={(e) => setMerchantId(Number(e.target.value))}
                style={{ fontSize: '0.8rem', padding: '6px 10px' }}
              />
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.725rem', color: 'var(--text-dim)', marginBottom: '4px', display: 'block' }}>
              Action Preset
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {(['DISCOVER', 'SEARCH', 'GET_PRODUCT', 'CHECK_INVENTORY', 'CREATE_ORDER', 'PROPOSE_PAYMENT', 'GET_PAYMENT_STATUS'] as ProtocolAction[]).map(
                (act) => (
                  <button
                    key={act}
                    type="button"
                    onClick={() => handleActionChange(act)}
                    className={`btn ${selectedAction === act ? 'btn-primary' : 'btn-outline'}`}
                    style={{ fontSize: '0.7rem', padding: '4px 8px', borderRadius: '6px' }}
                  >
                    {act}
                  </button>
                )
              )}
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.725rem', color: 'var(--text-dim)', marginBottom: '4px', display: 'block' }}>
              Payload (JSON)
            </label>
            <textarea
              className="form-input mono"
              value={payloadInput}
              onChange={(e) => setPayloadInput(e.target.value)}
              rows={8}
              style={{
                fontSize: '0.775rem',
                fontFamily: 'monospace',
                background: 'rgba(15, 23, 42, 0.9)',
                color: '#38bdf8',
                resize: 'vertical',
              }}
            />
          </div>

          <button
            type="button"
            className="btn btn-primary"
            onClick={handleSendProtocolMessage}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              fontWeight: 700,
              padding: '10px',
            }}
          >
            {loading ? <RefreshCw size={16} className="spinning" /> : <Send size={16} />}
            Dispatch Protocol Message
          </button>
        </div>

        {/* Right Column: Protocol Response Viewer */}
        <div
          className="glass-card"
          style={{
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Mercora Response Envelope
            </span>
            {response && (
              <span
                style={{
                  fontSize: '0.725rem',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '6px',
                  background: response.success ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                  color: response.success ? '#34d399' : '#f87171',
                  border: `1px solid ${response.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                }}
              >
                {response.success ? 'SUCCESS (200)' : `ERROR (${response.error?.code || '400'})`}
              </span>
            )}
          </div>

          <div
            style={{
              flex: 1,
              minHeight: '260px',
              padding: '12px',
              borderRadius: '8px',
              background: 'rgba(10, 15, 28, 0.95)',
              border: '1px solid var(--border-subtle)',
              overflow: 'auto',
            }}
          >
            {response ? (
              <pre
                className="mono"
                style={{
                  fontSize: '0.775rem',
                  color: response.success ? '#6ee7b7' : '#fca5a5',
                  margin: 0,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {JSON.stringify(response, null, 2)}
              </pre>
            ) : (
              <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-dim)' }}>
                <Cpu size={28} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                <p style={{ fontSize: '0.85rem' }}>Select an action and click <strong>Dispatch</strong> to inspect response.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
