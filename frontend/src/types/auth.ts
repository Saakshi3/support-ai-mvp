export interface User {
  user_id: string;
  email: string;
  display_name: string;
  role: 'REQUESTER' | 'SUPPORT';
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}