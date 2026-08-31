export type OrderStatus = 'PENDING' | 'CONFIRMED' | 'CANCELLED' | 'FAILED';

export type OpportunityType = 'UPSELL' | 'CROSS_SELL' | 'BUNDLE' | 'SLOW_MOVING_PRODUCT';

export type CampaignStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'ACTIVE'
  | 'REJECTED'
  | 'PAUSED'
  | 'COMPLETED'
  | 'FAILED';

export type CampaignType =
  | 'CROSS_SELL'
  | 'UPSELL'
  | 'BUNDLE'
  | 'SLOW_MOVING_PRODUCT'
  | 'GENERAL_PROMOTION';

export type ProductCampaignRole = 'PRIMARY' | 'RECOMMENDED' | 'BUNDLE_ITEM' | 'TARGET';

export type OfferType = 'UPSELL' | 'CROSS_SELL' | 'BUNDLE' | 'PRODUCT_DISCOUNT';

export type DiscountType = 'PERCENTAGE' | 'FIXED_AMOUNT';

export type ApprovalStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED';

export type ApprovalActionType =
  | 'CREATE_CAMPAIGN'
  | 'CREATE_OFFER'
  | 'ACTIVATE_CAMPAIGN'
  | 'UPDATE_OFFER';

export type AgentActionStatus =
  | 'PROPOSED'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'EXECUTED'
  | 'FAILED';

export type ActorType = 'MERCHANT' | 'AI_AGENT' | 'AI_BUYER' | 'SYSTEM';

export type ProductAvailability = 'IN_STOCK' | 'LOW_STOCK' | 'OUT_OF_STOCK' | 'INACTIVE';

export interface AIProduct {
  id: number;
  merchant_id: number;
  name: string;
  description?: string | null;
  category: string;
  price: number;
  currency: string;
  availability: ProductAvailability;
  stock_quantity: number;
  sku: string;
  attributes: Record<string, any>;
  purchase_constraints: Record<string, any>;
}

export interface AIMerchantProfile {
  merchant_id: number;
  merchant_name: string;
  description?: string | null;
  currency: string;
  categories: string[];
  commerce_capabilities: Record<string, boolean>;
}

export interface AIMerchantManifest {
  merchant_id: number;
  name: string;
  version: string;
  capabilities: {
    catalog: boolean;
    search: boolean;
    product_details: boolean;
    inventory: boolean;
    order_creation: boolean;
    payment: boolean;
  };
  endpoints: Record<string, string>;
}

export interface AICatalogResponse {
  merchant_id?: number | null;
  total_count: number;
  products: AIProduct[];
}

export interface AISearchResult {
  product: AIProduct;
  relevance_score: number;
  match_reasons: string[];
}

export interface AISearchResponse {
  query?: string | null;
  total_matches: number;
  results: AISearchResult[];
}

export interface AIOrderItemResponse {
  product_id: number;
  name: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface AIOrderResponse {
  order_id: number;
  merchant_id: number;
  status: string;
  items: AIOrderItemResponse[];
  total_amount: number;
  currency: string;
  payment_status: string;
  idempotency_key?: string | null;
  created_at: string;
}

export interface BuyerProductOption {
  id: number;
  name: string;
  category: string;
  price: number;
  availability: string;
  stock_quantity: number;
  relevance_score: number;
  reason?: string | null;
}

export interface BuyerChatResponse {
  response: string;
  candidates: BuyerProductOption[];
  selected_product?: BuyerProductOption | null;
  order_created?: AIOrderResponse | null;
  payment_intent?: PaymentIntent | null;
  execution_steps: string[];
  provider_used?: string;
  is_fallback_mode?: boolean;
}

export interface BuyerSimulationResponse {
  success: boolean;
  order?: AIOrderResponse | null;
  payment_intent?: PaymentIntent | null;
  error_message?: string | null;
  explainability: string;
  payment_note: string;
}

export interface SafetyCheckItem {
  check_name: string;
  passed: boolean;
  details: string;
}

export interface SafetyCheckResult {
  is_safe: boolean;
  checks: SafetyCheckItem[];
  rejection_reasons: string[];
}

export interface ActionProposal {
  id: string;
  merchant_id: number;
  action_type: string;
  opportunity_id?: string | null;
  title: string;
  description: string;
  campaign_type: string;
  target_product_ids: number[];
  target_product_names: string[];
  primary_product_id?: number | null;
  primary_product_name?: string | null;
  recommended_product_ids: number[];
  recommended_product_names: string[];
  discount_type: string;
  discount_value: number;
  original_bundle_price?: number | null;
  discounted_bundle_price?: number | null;
  campaign_duration_days: number;
  expected_benefit: string;
  reasoning: string;
  risk_level: string;
  requires_approval: boolean;
  safety_check: SafetyCheckResult;
  approval_id?: number | null;
  agent_action_id?: number | null;
}

export interface Opportunity {
  id: string;
  type: OpportunityType;
  title: string;
  description: string;
  primary_product_id: number;
  primary_product_name: string;
  recommended_product_ids: number[];
  recommended_product_names: string[];
  reasoning: string;
  fact_statement: string;
  ai_interpretation: string;
  supporting_metrics: Record<string, any>;
  estimated_revenue_impact: number;
  confidence: number;
  requires_merchant_approval: boolean;
}

export interface AgentAnalysisResponse {
  merchant_id: number;
  summary: string;
  opportunities: Opportunity[];
  proposals: ActionProposal[];
  provider_used: string;
  is_fallback_mode: boolean;
}

export interface AgentChatRequest {
  merchant_id: number;
  message: string;
}

export interface AgentChatResponse {
  response: string;
  opportunities: Opportunity[];
  proposals: ActionProposal[];
  provider_used: string;
  is_fallback_mode: boolean;
}

export interface AgentSummaryMetrics {
  total_opportunities: number;
  high_confidence_count: number;
  potential_revenue_impact: number;
  pending_approvals_count: number;
  active_campaigns_count: number;
  provider_used: string;
  is_fallback_mode: boolean;
}

export interface CampaignProduct {
  id: number;
  product_id: number;
  product_name?: string | null;
  role: ProductCampaignRole;
}

export interface Campaign {
  id: number;
  merchant_id: number;
  name: string;
  description?: string | null;
  campaign_type: CampaignType;
  status: CampaignStatus;
  start_date?: string | null;
  end_date?: string | null;
  created_by: ActorType;
  created_at: string;
  updated_at: string;
  products: CampaignProduct[];
}

export interface Offer {
  id: number;
  merchant_id: number;
  campaign_id: number;
  product_id?: number | null;
  product_name?: string | null;
  offer_type: OfferType;
  discount_type: DiscountType;
  discount_value: number;
  maximum_discount_amount?: number | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Approval {
  id: number;
  merchant_id: number;
  action_type: ApprovalActionType;
  action_id?: number | null;
  status: ApprovalStatus;
  requested_at: string;
  reviewed_at?: string | null;
  reviewed_by?: string | null;
  reason?: string | null;
  metadata_json?: string | null;
  metadata_parsed?: Record<string, any> | null;
}

export interface AuditLog {
  id: number;
  merchant_id: number;
  actor_type: ActorType;
  actor_id?: string | null;
  action: string;
  entity_type?: string | null;
  entity_id?: number | null;
  status: string;
  reason?: string | null;
  metadata_json?: string | null;
  created_at: string;
}

export interface MerchantAiPolicy {
  id: number;
  merchant_id: number;
  max_discount_percentage: number;
  max_discount_amount: number;
  auto_approve_non_financial: boolean;
  require_approval_for_campaigns: boolean;
  require_approval_for_discounts: boolean;
  max_campaign_duration_days: number;
  is_enabled: boolean;
}

export interface Merchant {
  id: number;
  name: string;
  email: string;
  description?: string | null;
  currency: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MerchantCreateInput {
  name: string;
  email: string;
  description?: string;
  currency?: string;
}

export interface MerchantUpdateInput {
  name?: string;
  email?: string;
  description?: string;
  currency?: string;
  is_active?: boolean;
}

export interface Product {
  id: number;
  merchant_id: number;
  name: string;
  description?: string | null;
  category: string;
  price: number;
  currency: string;
  stock_quantity: number;
  sku: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCreateInput {
  merchant_id: number;
  name: string;
  description?: string;
  category: string;
  price: number;
  currency?: string;
  stock_quantity: number;
  sku: string;
  is_active?: boolean;
}

export interface ProductUpdateInput {
  name?: string;
  description?: string;
  category?: string;
  price?: number;
  currency?: string;
  stock_quantity?: number;
  sku?: string;
  is_active?: boolean;
}

export interface Customer {
  id: number;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreateInput {
  name: string;
  email: string;
}

export interface OrderItemInput {
  product_id: number;
  quantity: number;
}

export interface OrderCreateInput {
  merchant_id: number;
  customer_id: number;
  items: OrderItemInput[];
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
  subtotal: number;
  product?: Product;
}

export interface Order {
  id: number;
  merchant_id: number;
  customer_id: number;
  status: OrderStatus;
  total_amount: number;
  currency: string;
  idempotency_key?: string | null;
  payment_status: string;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
  customer?: Customer;
  merchant?: Merchant;
}

// --- Phase 5: Razorpay Test Mode & Bounded Money Actions Types ---

export type PaymentStatus =
  | 'CREATED'
  | 'PENDING'
  | 'AUTHORIZED'
  | 'CAPTURED'
  | 'FAILED'
  | 'CANCELLED'
  | 'REFUNDED';

export type PaymentIntentStatus =
  | 'PROPOSED'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'EXECUTING'
  | 'COMPLETED'
  | 'FAILED';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'BLOCKED';

export type MoneyActionType = 'CREATE_PAYMENT' | 'CAPTURE_PAYMENT' | 'REFUND_PAYMENT';

export interface PaymentPolicyCheck {
  is_allowed: boolean;
  amount: number;
  currency: string;
  max_transaction_limit: number;
  daily_limit: number;
  today_spent: number;
  remaining_daily_limit: number;
  risk_level: string;
  requires_approval: boolean;
  reasons: string[];
  explainability: string;
}

export interface PaymentIntent {
  id: number;
  order_id: number;
  merchant_id: number;
  amount: number;
  currency: string;
  status: PaymentIntentStatus;
  risk_level: RiskLevel;
  reason: string;
  requires_approval: boolean;
  approved_by?: string | null;
  approved_at?: string | null;
  expires_at?: string | null;
  idempotency_key?: string | null;
  created_at: string;
  explainability?: string | null;
  policy_check?: PaymentPolicyCheck | null;
}

export interface RazorpayOrder {
  razorpay_order_id: string;
  razorpay_key_id: string;
  amount: number; // in paise
  currency: string;
  payment_intent_id: number;
  order_id: number;
  status: string;
  is_test_mode: boolean;
}

export interface PaymentVerificationRequest {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
  payment_intent_id: number;
}

export interface PaymentVerificationResponse {
  success: boolean;
  payment_id: number;
  order_id: number;
  status: string;
  amount: number;
  currency: string;
  message: string;
  verified_at: string;
}

export interface Payment {
  id: number;
  order_id: number;
  merchant_id: number;
  payment_intent_id?: number | null;
  razorpay_order_id?: string | null;
  razorpay_payment_id?: string | null;
  amount: number;
  currency: string;
  status: PaymentStatus;
  payment_method: string;
  failure_reason?: string | null;
  created_at: string;
  verified_at?: string | null;
}

export interface TransactionDetail {
  payment: Payment;
  order: Record<string, any>;
  payment_intent?: PaymentIntent | null;
  decision_chain: string[];
  audit_events: Array<Record<string, any>>;
}

// --- Phase 6: Agent Commerce Protocol & Session Types ---

export type ProtocolAction =
  | 'DISCOVER'
  | 'SEARCH'
  | 'GET_PRODUCT'
  | 'CHECK_INVENTORY'
  | 'CREATE_ORDER'
  | 'PROPOSE_PAYMENT'
  | 'GET_PAYMENT_STATUS';

export interface AgentSenderRecipient {
  type: 'AI_BUYER' | 'MERCHANT' | 'SYSTEM';
  id: string;
}

export interface AgentMessage {
  protocol_version?: string;
  message_id: string;
  session_id: string;
  trace_id?: string | null;
  sender: AgentSenderRecipient;
  recipient: AgentSenderRecipient;
  action: ProtocolAction;
  payload?: Record<string, any>;
}

export interface AgentError {
  code: string;
  message: string;
  details?: Record<string, any> | null;
}

export interface AgentResponse {
  success: boolean;
  protocol_version: string;
  message_id: string;
  session_id: string;
  trace_id: string;
  action: string;
  data?: Record<string, any> | null;
  error?: AgentError | null;
}

export interface AgentCommerceContract {
  protocol_version: string;
  merchant_id: number;
  merchant_name: string;
  currency: string;
  capabilities: Record<string, boolean>;
  endpoints: Record<string, string>;
  payment_policy: Record<string, any>;
  supported_actions: string[];
}

export interface SessionResponse {
  session_id: string;
  trace_id: string;
  merchant_id: number;
  buyer_id: string;
  status: string;
  created_at: string;
  expires_at?: string | null;
}

export interface SessionTimelineEvent {
  timestamp: string;
  action: string;
  actor: string;
  status: string;
  details: Record<string, any>;
}

export interface SessionTimelineResponse {
  session_id: string;
  trace_id: string;
  status: string;
  merchant_id: number;
  buyer_id: string;
  timeline: SessionTimelineEvent[];
}

export interface CommerceReadinessScoreItem {
  category: string;
  name: string;
  weight: number;
  passed: boolean;
  details: string;
}

export interface CommerceReadinessResponse {
  merchant_id: number;
  merchant_name: string;
  readiness_score: number;
  is_ready: boolean;
  checklist: CommerceReadinessScoreItem[];
  recommendations: string[];
}

export interface AgentCommerceStats {
  active_sessions: number;
  orders_via_ai: number;
  ai_revenue: number;
  successful_payments: number;
  blocked_transactions: number;
  currency: string;
}

