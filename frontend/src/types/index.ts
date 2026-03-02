export type TicketStatus = 'NEW' | 'ASSIGNED' | 'RESOLVED';
export type TicketPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type TicketCategory = 'EMAIL_ISSUE' | 'ACCESS_PROBLEM' | 'SERVER_ISSUE' | 'UI_PROBLEM' | 'OTHER';

export interface Ticket {
  ticket_id: string;
  title: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  category: TicketCategory;
  created_by: string;
  assigned_to?: string;
  created_at: string;
  updated_at: string;
  resolution_text?: string;
  customer_satisfaction?: number;
}

export interface TicketCreate {
  title: string;
  description: string;
  priority?: TicketPriority;
}

export interface TicketAssignRequest {
  assigned_to_email: string;
}

export interface TicketStatusRequest {
  status: TicketStatus;
}

export interface ResolutionOption {
  resolution_text: string;
  confidence_score: number;
  reasoning: string;
  supporting_incident_ids?: string[];
}

export interface AnalysisResult {
  ticket_id: string;
  category: TicketCategory;
  confidence_score: number;
  reasoning: string;
  resolution_options: ResolutionOption[];
  escalation_recommended: boolean;
  agent_name: string;
}

export interface EmailDraftRequest {
  email_type: 'UPDATE' | 'RESOLUTION' | 'ESCALATION';
  tone: 'professional' | 'friendly' | 'formal';
  recipient_context: 'customer' | 'internal' | 'executive';
}

export interface EmailDraft {
  email_id: string;
  subject: string;
  body: string;
  confidence_score: number;
  draft_reasoning: string;
}

export interface Email {
  email_id: string;
  ticket_id: string;
  type: string;
  subject: string;
  body: string;
  tone: string;
  audience: string;
  is_approved: boolean;
  created_at: string;
  created_by: string;
  approved_by?: string;
  approved_at?: string;
  is_from_customer?: boolean;
}

export interface CustomerReplyRequest {
  reply_text: string;
}

export interface CustomerApprovalRequest {
  approved: boolean;
  feedback?: string;
}

export interface AIAuditLog {
  ai_event_id: string;
  agent_name: string;
  model_name: string;
  confidence_json: any;
  was_used: boolean;
  created_at: string;
}