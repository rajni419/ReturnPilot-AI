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

