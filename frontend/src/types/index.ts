export interface OrderItem {
  id: number;
  order_id: number;
  product_name: string;
  sku: string | null;
  quantity: number;
  price: number;
  is_returnable: boolean;
}

export interface Order {
  id: number;
  order_number: string;
  customer_name: string;
  customer_email: string;
  order_date: string;
  delivery_date: string | null;
  shipping_status: string;
  total_amount: number;
  created_at: string;
  items: OrderItem[];
}

export interface ReturnCheckRequest {
  order_number: string;
  customer_email: string;
  sku: string;
}

export interface ReturnCheckResponse {
  eligible: boolean;
  reason: string;
  order_number: string;
  sku: string;
}

export interface ReturnCreateRequest {
  order_number: string;
  customer_email: string;
  sku: string;
  return_reason: string;
}

export interface ReturnRequest {
  id: number;
  return_number: string;
  order_id: number;
  order_item_id: number;
  order_number: string;
  customer_email: string;
  sku: string;
  return_reason: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'PROCESSING' | string;
  created_at: string;
  updated_at: string;
}

export interface HealthStatus {
  status: string;
}

export interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
  message: string;
}

export interface UserRegisterRequest {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface UserLoginRequest {
  email: string;
  password: string;
}

export interface VerifyEmailRequest {
  email: string;
  token: string;
}

export interface ResendVerificationRequest {
  email: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  email: string;
  token: string;
  new_password: string;
  confirm_password: string;
}

export interface MessageResponse {
  message: string;
  success: boolean;
  dev_token?: string | null;
}

// AI Assistant & Chat Types
export interface PolicyCitation {
  policy_id: string;
  section: string;
  title: string;
  category: string;
  snippet: string;
  similarity_score: number;
  allowed_actions: string[];
}

export interface ResolutionOption {
  id: string;
  title: string;
  description: string;
  timeline: string;
  pros: string[];
  cons: string[];
  badge?: string | null;
  is_recommended: boolean;
}

export interface EligibilityEvaluation {
  eligible: boolean;
  order_number: string;
  sku: string;
  product_name: string;
  customer_email: string;
  policy_reference: string;
  reason: string;
  detailed_explanation: string;
  return_window_days: number;
  days_since_delivery?: number | null;
  permitted_resolutions: ResolutionOption[];
  active_return_number?: string | null;
  requires_human_review: boolean;
  suggested_resolution?: string | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  language: string;
  citations?: PolicyCitation[];
  eligibility?: EligibilityEvaluation | null;
  orders?: any[];
  selected_order_number?: string | null;
  selected_sku?: string | null;
  suggested_resolutions?: ResolutionOption[];
  confirmation_required?: boolean;
  confirmation_payload?: {
    order_number: string;
    customer_email: string;
    sku: string;
    product_name: string;
    resolution: string;
    return_reason: string;
  } | null;
  action_result?: any;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  preferred_language?: string;
  order_number?: string;
  sku?: string;
}

export interface ActionConfirmRequest {
  session_id: string;
  order_number: string;
  sku: string;
  resolution: string;
  return_reason: string;
}

export interface ActionConfirmResponse {
  success: boolean;
  message: string;
  return_number: string;
  status: string;
  order_number: string;
  sku: string;
  resolution: string;
  created_at: string;
}

export interface PhotoAnalysisResult {
  is_valid_image: boolean;
  file_name: string;
  file_size_kb: number;
  detected_issue: string;
  confidence_score: number;
  is_ambiguous: boolean;
  requires_human_review: boolean;
  summary: string;
  visible_evidence: string[];
  disclaimer: string;
}


