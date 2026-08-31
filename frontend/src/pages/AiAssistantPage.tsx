import React, { useEffect, useRef, useState } from 'react';
import { Bot, Send, Sparkles, RefreshCw, Cpu } from 'lucide-react';
import { ActionProposal, Merchant, Opportunity } from '../types';
import { agentService } from '../services/agentService';
import { growthService } from '../services/growthService';
import { OpportunityCard } from '../components/OpportunityCard';
import { OpportunityDetailsModal } from '../components/OpportunityDetailsModal';
import { ActionProposalCard } from '../components/ActionProposalCard';

interface AiAssistantPageProps {
  currentMerchant: Merchant | null;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  opportunities?: Opportunity[];
  proposals?: ActionProposal[];
  provider?: string;
  isFallback?: boolean;
  timestamp: Date;
}

const QUICK_PROMPTS = [
  'Create a bundle for Running Shoes and Running Socks with 10% discount.',
  'Create a campaign for my slow-moving inventory.',
  'What products are commonly bought together?',
  'Find me an upsell opportunity for running shoes.',
  'How can I increase my store revenue this week?',
];

export const AiAssistantPage: React.FC<AiAssistantPageProps> = ({ currentMerchant }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeProvider, setActiveProvider] = useState<string>('Initializing Agent...');
  const [isFallback, setIsFallback] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);
  const [isProposingOpportunity, setIsProposingOpportunity] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  const loadAnalysis = async (userPrompt?: string) => {
    if (!currentMerchant) return;
    try {
      setLoading(true);
      const analysis = await agentService.analyzeStore(
        currentMerchant.id,
        userPrompt || 'Analyze catalog data and order patterns for revenue growth opportunities'
      );

      setActiveProvider(analysis.provider_used);
      setIsFallback(analysis.is_fallback_mode);

      setMessages((prev) => [
        ...prev,
        {
          id: `init-${Date.now()}`,
          sender: 'assistant',
          text: analysis.summary,
          opportunities: analysis.opportunities,
          proposals: analysis.proposals || [],
          provider: analysis.provider_used,
          isFallback: analysis.is_fallback_mode,
          timestamp: new Date(),
        },
      ]);
    } catch (err: any) {
      console.error('Analysis failed:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: `init-err-${Date.now()}`,
          sender: 'assistant',
          text: 'AI Agent is ready. Ask me any question about your store revenue, product affinities, or click "Propose Campaign" on any suggestion card below!',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!currentMerchant) return;
    setMessages([]);
    loadAnalysis();
  }, [currentMerchant]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleProposeOpportunity = async (
    opportunity: Opportunity,
    discountValue: number = 10,
    durationDays: number = 7
  ) => {
    if (!currentMerchant) return;
    try {
      setIsProposingOpportunity(opportunity.id);
      const targetIds = [
        opportunity.primary_product_id,
        ...(opportunity.recommended_product_ids || []),
      ].filter(Boolean) as number[];

      const actionType =
        opportunity.type === 'BUNDLE'
          ? 'CREATE_BUNDLE'
          : opportunity.type === 'SLOW_MOVING_PRODUCT'
          ? 'SLOW_MOVING_PROMOTION'
          : 'CREATE_CAMPAIGN';

      const newProposal = await growthService.proposeAction({
        merchant_id: currentMerchant.id,
        action_type: actionType,
        opportunity_id: opportunity.id,
        title: opportunity.title,
        description:
          opportunity.description ||
          `AI-generated growth action based on recommendation: ${opportunity.title}`,
        campaign_type: opportunity.type,
        target_product_ids:
          targetIds.length > 0 ? targetIds : [opportunity.primary_product_id],
        primary_product_id: opportunity.primary_product_id,
        recommended_product_ids: opportunity.recommended_product_ids,
        discount_type: 'PERCENTAGE',
        discount_value: discountValue,
        campaign_duration_days: durationDays,
        expected_benefit: `Estimated gross revenue upside of ₹${opportunity.estimated_revenue_impact.toLocaleString()}`,
        reasoning: `${opportunity.fact_statement} ${opportunity.ai_interpretation}`,
      });

      // Append confirmation message with proposal card to chat
      const proposalMsg: ChatMessage = {
        id: `prop-${Date.now()}`,
        sender: 'assistant',
        text: `⚡ I have created a structured **Action Proposal** for **${opportunity.title}** (${discountValue}% discount for ${durationDays} days) and submitted it to your **Merchant Approvals Queue**.\n\n🛡️ **Governance Status**: Placed in **PENDING APPROVAL** status. Click below to review and authorize it in Approvals.`,
        proposals: [newProposal],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, proposalMsg]);
      setSelectedOpportunity(null);
    } catch (err: any) {
      console.error('Failed to propose action:', err);
      alert(`Could not create action proposal: ${err?.message || 'Policy violation'}`);
    } finally {
      setIsProposingOpportunity(null);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || !currentMerchant || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await agentService.chatWithAgent({
        merchant_id: currentMerchant.id,
        message: text,
      });

      setActiveProvider(response.provider_used);
      setIsFallback(response.is_fallback_mode);

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: 'assistant',
        text: response.response,
        opportunities: response.opportunities,
        proposals: response.proposals || [],
        provider: response.provider_used,
        isFallback: response.is_fallback_mode,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: 'AI service is temporarily unavailable. Your merchant data is safe. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: 'calc(100vh - 140px)' }}>
      {/* Header Info & Provider Status */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          paddingBottom: '12px',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Bot size={22} color="#818CF8" /> Merchant AI Growth Agent
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
            LangGraph reasoning engine: Analyze catalog data, identify opportunities, and generate structured growth proposals.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => loadAnalysis('Fresh store re-analysis')}
            disabled={loading}
            style={{ gap: '6px', fontSize: '0.8rem' }}
          >
            <RefreshCw size={13} className={loading ? 'spinning' : ''} />
            Re-Analyze Catalog
          </button>

          <span
            className="badge-tag"
            style={
              isFallback
                ? { background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.3)' }
                : { background: 'rgba(99, 102, 241, 0.15)', color: '#a5b4fc', border: '1px solid rgba(99, 102, 241, 0.3)' }
            }
          >
            <Cpu size={14} />
            {isFallback ? 'AI Mode: Fallback Engine' : `Engine: ${activeProvider}`}
          </span>
        </div>
      </div>

      {/* Chat Log View */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
          paddingRight: '8px',
        }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              gap: '12px',
            }}
          >
            <div
              style={{
                maxWidth: msg.sender === 'user' ? '70%' : '88%',
                padding: '16px 20px',
                borderRadius: '16px',
                background:
                  msg.sender === 'user'
                    ? 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)'
                    : 'rgba(15, 23, 42, 0.85)',
                border: msg.sender === 'user' ? 'none' : '1px solid var(--border-subtle)',
                boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                color: 'var(--text-main)',
                fontSize: '0.925rem',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap',
              }}
            >
              {msg.text}
            </div>

            {/* Render Attached Action Proposals (Phase 3) */}
            {msg.proposals && msg.proposals.length > 0 && (
              <div
                style={{
                  width: '100%',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
                  gap: '16px',
                  marginTop: '6px',
                }}
              >
                {msg.proposals.map((prop) => (
                  <ActionProposalCard key={prop.id} proposal={prop} />
                ))}
              </div>
            )}

            {/* Render Attached Opportunities with Direct Action Triggers */}
            {msg.opportunities && msg.opportunities.length > 0 && (
              <div
                style={{
                  width: '100%',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                  gap: '16px',
                  marginTop: '6px',
                }}
              >
                {msg.opportunities.map((opp) => (
                  <OpportunityCard
                    key={opp.id}
                    opportunity={opp}
                    onReview={(o) => setSelectedOpportunity(o)}
                    onProposeAction={(o) => handleProposeOpportunity(o, 10, 7)}
                    isProposing={isProposingOpportunity === opp.id}
                  />
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
            <RefreshCw size={16} className="spinning" />
            <span>Agent is analyzing order history and validating safety policies...</span>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Suggested Quick Prompt Chips */}
      <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
        {QUICK_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => handleSendMessage(prompt)}
            disabled={loading}
            style={{
              whiteSpace: 'nowrap',
              fontSize: '0.775rem',
              borderRadius: '20px',
              padding: '6px 12px',
            }}
          >
            <Sparkles size={12} color="#818cf8" />
            {prompt}
          </button>
        ))}
      </div>

      {/* Message Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        style={{
          display: 'flex',
          gap: '12px',
          background: 'rgba(13, 19, 33, 0.9)',
          padding: '8px 12px',
          borderRadius: '12px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <input
          type="text"
          className="form-input"
          style={{ border: 'none', background: 'transparent', boxShadow: 'none' }}
          placeholder="Ask AI Growth Agent (e.g. 'Create a bundle for shoes and socks with 10% discount')..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !inputMessage.trim()}
          style={{ padding: '8px 18px' }}
        >
          <Send size={16} /> Send
        </button>
      </form>

      {/* Opportunity Details Review Modal with Direct Proposal Action */}
      <OpportunityDetailsModal
        isOpen={!!selectedOpportunity}
        onClose={() => setSelectedOpportunity(null)}
        opportunity={selectedOpportunity}
        onProposeAction={handleProposeOpportunity}
        isProposing={!!isProposingOpportunity}
      />
    </div>
  );
};
