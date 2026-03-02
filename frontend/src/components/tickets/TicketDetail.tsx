import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  SparklesIcon,
  PaperAirplaneIcon,
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  XCircleIcon,
  UserIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { api } from '@/lib/api';
import { Ticket, AnalysisResult, EmailDraft, Email } from '@/types';
import { useAuth } from '@/contexts/AuthContext';
import { formatDateTime, getStatusColor, formatTimeAgo } from '@/lib/utils';
import toast from 'react-hot-toast';

export default function TicketDetail() {
  const { ticketId } = useParams<{ ticketId: string }>();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [showEmailDraft, setShowEmailDraft] = useState(false);
  const [customerReply, setCustomerReply] = useState('');
  const [approvalFeedback, setApprovalFeedback] = useState('');

  // Fetch ticket details
  const { data: ticket, isLoading: ticketLoading } = useQuery({
    queryKey: ['ticket', ticketId],
    queryFn: async () => {
      const response = await api.get<Ticket>(`/tickets/${ticketId}`);
      return response.data;
    },
    enabled: !!ticketId,
  });

  // Fetch ticket emails/communications  
  const { data: emails, isLoading: emailsLoading, refetch: refetchEmails } = useQuery({
    queryKey: ['ticket-emails', ticketId],
    queryFn: async () => {
      console.log('[DEBUG] Fetching emails for ticket:', ticketId);
      const response = await api.get<{emails: Email[]}>(`/tickets/${ticketId}/emails`);
      console.log('[DEBUG] Fetched emails:', response.data.emails);
      return response.data.emails;
    },
    enabled: !!ticketId,
    refetchInterval: 5000, // Auto-refresh every 5 seconds to catch new messages
  });

  // AI Analysis mutation
  const analysisMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<AnalysisResult>(`/tickets/${ticketId}/analyze`);
      return response.data;
    },
    onSuccess: () => {
      setShowAnalysis(true);
      toast.success('AI analysis completed!');
    },
    onError: (error: any) => {
      console.error('AI analysis error:', error);
      const errorMessage = error?.response?.data?.detail || error?.message || 'AI analysis failed';
      toast.error(errorMessage);
    },
  });

  // Email Draft mutation
  const emailDraftMutation = useMutation({
    mutationFn: async (params: { email_type: string; tone: string; recipient_context: string }) => {
      const response = await api.post<EmailDraft>(`/tickets/${ticketId}/draft-email`, params);
      return response.data;
    },
    onSuccess: () => {
      setShowEmailDraft(true);
      toast.success('Email draft created!');
    },
    onError: (error: any) => {
      console.error('Email draft error:', error);
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to create email draft';
      toast.error(errorMessage);
    },
  });

  // Send Email mutation
  const sendEmailMutation = useMutation({
    mutationFn: async (emailId: string) => {
      console.log('[DEBUG] Sending email with ID:', emailId);
      if (!emailId) {
        throw new Error('Email ID is required');
      }
      const response = await api.post(`/tickets/${ticketId}/send-email/${emailId}`);
      console.log('[DEBUG] Send email response:', response.data);
      return response.data;
    },
    onSuccess: (data) => {
      console.log('[SUCCESS] Email sent successfully:', data);
      
      // Wait a bit before refetching to ensure backend changes are committed
      setTimeout(() => {
        console.log('[DEBUG] Invalidating queries and refetching...');
        // Refresh both ticket and emails to show updated conversation
        queryClient.invalidateQueries({ queryKey: ['ticket', ticketId] });
        queryClient.invalidateQueries({ queryKey: ['ticket-emails', ticketId] });
        // Force immediate refetch
        refetchEmails();
      }, 500);
      
      toast.success('Email sent successfully!');
      setShowEmailDraft(false); // Close email draft panel
    },
    onError: (error: any) => {
      console.error('[ERROR] Send email error:', error);
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to send email';
      toast.error(errorMessage);
    },
  });

  // Ticket Assignment mutation
  const assignmentMutation = useMutation({
    mutationFn: async (assigneeEmail: string) => {
      const response = await api.post(`/tickets/${ticketId}/assign`, {
        assigned_to_email: assigneeEmail
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ticket', ticketId] });
      queryClient.invalidateQueries({ queryKey: ['tickets'] }); // Refresh dashboard
      toast.success('Ticket assigned successfully!');
    },
    onError: (error: any) => {
      const errorMessage = error?.response?.data?.detail || 'Failed to assign ticket';
      toast.error(errorMessage);
    },
  });

  // Customer Reply mutation
  const customerReplyMutation = useMutation({
    mutationFn: async (replyText: string) => {
      const response = await api.post(`/tickets/${ticketId}/customer-reply`, {
        reply_text: replyText
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ticket-emails', ticketId] });
      queryClient.invalidateQueries({ queryKey: ['ticket', ticketId] });
      setCustomerReply('');
      toast.success('Reply sent!');
    },
    onError: (error: any) => {
      console.error('Customer reply error:', error);
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to send reply';
      toast.error(errorMessage);
    },
  });

  // Resolution Approval mutation
  const approvalMutation = useMutation({
    mutationFn: async (params: { approved: boolean; feedback?: string }) => {
      const response = await api.post(`/tickets/${ticketId}/customer-approve-resolution`, params);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ticket', ticketId] });
      setApprovalFeedback('');
      toast.success('Response submitted!');
    },    onError: (error: any) => {
      console.error('Approval error:', error);
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to submit feedback';
      toast.error(errorMessage);
    },  });

  const handleAnalyze = () => {
    analysisMutation.mutate();
  };

  const handleDraftEmail = () => {
    emailDraftMutation.mutate({
      email_type: 'UPDATE',
      tone: 'professional',
      recipient_context: 'customer'
    });
  };

  const handleSendEmail = (emailId: string | undefined) => {
    console.log('[DEBUG] handleSendEmail called with emailId:', emailId);
    if (!emailId) {
      console.log('[ERROR] No email ID provided');
      toast.error('Email ID not available. Please draft an email first.');
      return;
    }
    console.log('[DEBUG] Calling sendEmailMutation with:', emailId);
    sendEmailMutation.mutate(emailId);
  };

  const handleCustomerReply = () => {
    if (customerReply.trim()) {
      customerReplyMutation.mutate(customerReply);
    }
  };

  const handleApproval = (approved: boolean) => {
    approvalMutation.mutate({
      approved,
      feedback: approvalFeedback || undefined
    });
  };

  // Status progression logic
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'NEW':
        return {
          icon: InformationCircleIcon,
          color: 'text-blue-600 bg-blue-50 border-blue-200',
          message: 'Your ticket has been submitted and is waiting to be assigned to a support agent.',
          nextStep: 'A support agent will review and assign your ticket soon.'
        };
      case 'ASSIGNED':
        return {
          icon: ArrowPathIcon,
          color: 'text-yellow-600 bg-yellow-50 border-yellow-200',
          message: 'Your ticket is actively being worked on by our support team.',
          nextStep: 'You will receive updates as we investigate and resolve your issue.'
        };
      case 'RESOLVED':
        return {
          icon: CheckCircleIcon,
          color: 'text-green-600 bg-green-50 border-green-200',
          message: 'Your issue has been resolved! Please review the solution provided.',
          nextStep: 'If you\'re satisfied with the resolution, please approve it below.'
        };
      default:
        return {
          icon: ClockIcon,
          color: 'text-gray-600 bg-gray-50 border-gray-200',
          message: 'Ticket status is being updated.',
          nextStep: 'Please wait for further updates.'
        };
    }
  };

  const getPriorityInfo = (priority: string) => {
    switch (priority) {
      case 'CRITICAL':
        return { icon: ExclamationTriangleIcon, color: 'text-red-800', description: 'Urgent - System down or blocking work' };
      case 'HIGH':
        return { icon: ExclamationTriangleIcon, color: 'text-red-600', description: 'High - Significant impact on productivity' };
      case 'MEDIUM':
        return { icon: InformationCircleIcon, color: 'text-yellow-600', description: 'Medium - Moderate impact on work' };
      case 'LOW':
        return { icon: InformationCircleIcon, color: 'text-gray-600', description: 'Low - General questions or minor issues' };
      default:
        return { icon: InformationCircleIcon, color: 'text-gray-600', description: 'Priority not set' };
    }
  };

  if (ticketLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">Ticket not found</h3>
        <p className="mt-1 text-sm text-gray-500">The ticket you're looking for doesn't exist.</p>
      </div>
    );
  }

  const statusInfo = getStatusInfo(ticket.status);
  const priorityInfo = getPriorityInfo(ticket.priority);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Ticket Header with Status Timeline */}
      <div className="card p-6">
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-gray-900">{ticket.title}</h1>
              <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                #{ticket.ticket_id.slice(0, 8)}
              </span>
            </div>
            
            {/* Status Timeline */}
            <div className={`flex items-center p-4 rounded-lg border-2 ${statusInfo.color} mb-4`}>
              <statusInfo.icon className="h-6 w-6 mr-3 flex-shrink-0" />
              <div>
                <p className="font-medium">{statusInfo.message}</p>
                <p className="text-sm mt-1 opacity-75">{statusInfo.nextStep}</p>
              </div>
            </div>

            {/* Priority and Basic Info */}
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center">
                <priorityInfo.icon className={`h-4 w-4 mr-2 ${priorityInfo.color}`} />
                <span className={`font-medium ${priorityInfo.color}`}>{ticket.priority}</span>
                <span className="text-gray-500 ml-2">Priority</span>
              </div>
              <div className="flex items-center">
                <ClockIcon className="h-4 w-4 mr-2 text-gray-400" />
                <span>Created {formatTimeAgo(ticket.created_at)}</span>
              </div>
              <div className="flex items-center">
                <span className={getStatusColor(ticket.status)}>{ticket.status}</span>
              </div>
            </div>
          </div>
          
          {user?.role === 'SUPPORT' && (
            <div className="flex gap-2">
              {ticket.status === 'NEW' && (
                <button
                  onClick={() => assignmentMutation.mutate(user.email)}
                  disabled={assignmentMutation.isPending}
                  className="btn-secondary"
                >
                  <UserIcon className="h-4 w-4 mr-2" />
                  {assignmentMutation.isPending ? 'Assigning...' : 'Assign to Me'}
                </button>
              )}
              <button
                onClick={handleAnalyze}
                disabled={analysisMutation.isPending}
                className="btn-primary"
              >
                <SparklesIcon className="h-4 w-4 mr-2" />
                {analysisMutation.isPending ? 'Analyzing...' : 'AI Analyze'}
              </button>
              <button
                onClick={handleDraftEmail}
                disabled={emailDraftMutation.isPending}
                className="btn-secondary"
              >
                <PaperAirplaneIcon className="h-4 w-4 mr-2" />
                {emailDraftMutation.isPending ? 'Drafting...' : 'Draft Email'}
              </button>
            </div>
          )}
        </div>

        {/* Ticket Description */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-900 mb-2">Issue Description</h3>
          <p className="text-gray-700 leading-relaxed">{ticket.description}</p>
        </div>

        {/* Additional Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-200">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-sm font-medium text-gray-500">Category</div>
            <div className="text-lg font-semibold text-gray-900 mt-1">
              {ticket.category?.replace('_', ' ') || 'General'}
            </div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-sm font-medium text-gray-500">
              {ticket.assigned_to ? 'Assigned Agent' : 'Status'} 
            </div>
            <div className="text-lg font-semibold text-gray-900 mt-1">
              {ticket.assigned_to ? (
                <span className="text-green-600">Agent Assigned</span> 
              ) : (
                <span className="text-yellow-600">Awaiting Assignment</span>
              )}
            </div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-sm font-medium text-gray-500">Last Updated</div>
            <div className="text-lg font-semibold text-gray-900 mt-1">
              {formatTimeAgo(ticket.updated_at)}
            </div>
          </div>
        </div>
      </div>

      {/* AI Analysis Results */}
      {showAnalysis && analysisMutation.data && (
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <div className="p-2 bg-primary-100 rounded-lg mr-3">
              <SparklesIcon className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <h2 className="text-lg font-medium text-gray-900">AI Analysis Results</h2>
              <p className="text-sm text-gray-500">Intelligent suggestions based on similar cases</p>
            </div>
          </div>
          
          <div className="space-y-6">
            {/* Category Analysis */}
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-blue-900">Issue Classification</h3>
                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                  {Math.round((analysisMutation.data.confidence_score || 0) * 100)}% Confidence
                </span>
              </div>
              <p className="text-blue-800 font-medium">
                {analysisMutation.data.category ? analysisMutation.data.category.replace('_', ' ') : 'General Support'}
              </p>
              <p className="text-blue-700 text-sm mt-1">{analysisMutation.data.reasoning || 'Analysis in progress...'}</p>
            </div>

            {/* Resolution Suggestions */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Suggested Resolutions</h3>
              <div className="space-y-4">
                {(analysisMutation.data.resolution_options || []).map((option, index) => (
                  <div key={index} className="bg-gradient-to-r from-green-50 to-blue-50 border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm font-bold mr-3">
                          {index + 1}
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-900">Resolution Option {index + 1}</h4>
                          <div className="flex items-center mt-1">
                            <div className="w-full bg-gray-200 rounded-full h-1.5 mr-2 w-16">
                              <div 
                                className="bg-primary-600 h-1.5 rounded-full" 
                                style={{ width: `${(option.confidence_score || 0) * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-xs text-gray-600 font-medium">
                              {Math.round((option.confidence_score || 0) * 100)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="bg-white rounded-md p-3 border border-gray-100">
                      <p className="text-gray-700 leading-relaxed">
                        {option.resolution_text || 'Resolution suggestion unavailable'}
                      </p>
                    </div>
                    <div className="mt-2 text-xs text-gray-600 bg-gray-100 rounded p-2">
                      <strong>AI Reasoning:</strong> {option.reasoning || 'Analysis in progress...'}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {analysisMutation.data.escalation_recommended && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-600 mr-2" />
                  <span className="font-medium text-red-800">Escalation Recommended</span>
                </div>
                <p className="text-red-700 text-sm mt-1">
                  This issue may require specialized attention or additional resources for optimal resolution.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Email Draft */}
      {showEmailDraft && emailDraftMutation.data && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg mr-3">
                <PaperAirplaneIcon className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <h2 className="text-lg font-medium text-gray-900">AI-Generated Email</h2>
                <p className="text-sm text-gray-500">Professional communication draft</p>
              </div>
            </div>
            {user?.role === 'SUPPORT' && emailDraftMutation.data?.email_id && (
              <button
                onClick={() => handleSendEmail(emailDraftMutation.data?.email_id)}
                disabled={sendEmailMutation.isPending || !emailDraftMutation.data?.email_id}
                className="btn-success"
              >
                <PaperAirplaneIcon className="h-4 w-4 mr-2" />
                {sendEmailMutation.isPending ? 'Sending...' : 'Send to Customer'}
              </button>
            )}
          </div>
          
          <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
            <div className="bg-white border-b border-gray-200 px-4 py-3">
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-700 mr-2">Subject:</span>
                <span className="text-sm text-gray-900">{emailDraftMutation.data.subject}</span>
              </div>
            </div>
            <div className="p-4">
              <div className="bg-white border border-gray-200 rounded-md p-4">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                  {emailDraftMutation.data.body}
                </pre>
              </div>
            </div>
            <div className="bg-blue-50 px-4 py-2 border-t border-gray-200">
              <div className="flex items-center justify-between text-xs">
                <span className="text-blue-700">
                  AI Confidence: {Math.round(emailDraftMutation.data.confidence_score * 100)}%
                </span>
                <span className="text-blue-600">
                  {emailDraftMutation.data.draft_reasoning}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Communications Timeline */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg mr-3">
              <ChatBubbleLeftRightIcon className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <h2 className="text-lg font-medium text-gray-900">Communication Timeline</h2>
              <p className="text-sm text-gray-500">All messages and updates for this ticket</p>
            </div>
          </div>
          <button
            onClick={() => refetchEmails()}
            disabled={emailsLoading}
            className="text-xs text-gray-500 hover:text-gray-700 flex items-center px-2 py-1 rounded"
          >
            <ArrowPathIcon className={`h-4 w-4 mr-1 ${emailsLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
        
        {emailsLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
            <p className="text-sm text-gray-500 mt-2">Loading communications...</p>
          </div>
        ) : emails && emails.length > 0 ? (
          <div className="space-y-6">
            {(() => {
              console.log('[DEBUG] Rendering emails:', emails);
              return emails.map((email, index) => {
                console.log(`[DEBUG] Rendering email ${index}:`, email);
                return (
                  <div key={email.email_id} className="relative">
                    {/* Timeline connector */}
                    {index !== emails.length - 1 && (
                      <div className="absolute left-6 top-12 w-0.5 h-12 bg-gray-200"></div>
                    )}
                
                <div className="flex items-start">
                  <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center ${
                    email.type === 'DRAFT' && email.is_approved && email.subject.includes('Assigned') 
                      ? 'bg-yellow-100' 
                      : email.type === 'CUSTOMER_REPLY' || email.is_from_customer
                      ? 'bg-blue-100' 
                      : email.type === 'SUPPORT_RESPONSE' || email.type === 'APPROVED'
                      ? 'bg-green-100'
                      : email.type === 'DRAFT' && !email.is_approved
                      ? 'bg-gray-100'
                      : 'bg-green-100'
                  }`}>
                    {email.type === 'DRAFT' && email.is_approved && email.subject.includes('Assigned') ? (
                      <UserIcon className="h-6 w-6 text-yellow-600" />
                    ) : email.type === 'CUSTOMER_REPLY' || email.is_from_customer ? (
                      <UserIcon className="h-6 w-6 text-blue-600" />
                    ) : (
                      <UserIcon className={`h-6 w-6 ${
                        email.type === 'SUPPORT_RESPONSE' || email.type === 'APPROVED' ? 'text-green-600' : 'text-gray-600'
                      }`} />
                    )}
                  </div>
                  
                  <div className="ml-4 flex-1">
                    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
                      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <span className="text-sm font-medium text-gray-900">
                              {email.type === 'DRAFT' && email.is_approved && email.subject.includes('Assigned') 
                                ? 'System Update' 
                                : email.type === 'CUSTOMER_REPLY' || email.is_from_customer
                                ? 'You' 
                                : email.type === 'SUPPORT_RESPONSE' || email.type === 'APPROVED'
                                ? 'Support Team'
                                : email.type === 'DRAFT' && !email.is_approved
                                ? 'Draft Message'
                                : 'Support Team'}
                            </span>
                            {(email.type === 'SUPPORT_RESPONSE' || email.type === 'APPROVED') && (
                              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                <CheckCircleIcon className="h-3 w-3 mr-1" />
                                Sent to Customer
                              </span>
                            )}
                            {email.type === 'DRAFT' && email.is_approved && (
                              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                <CheckCircleIcon className="h-3 w-3 mr-1" />
                                {email.subject.includes('Assigned') ? 'Auto-sent' : 'Sent'}
                              </span>
                            )}
                            {email.type === 'DRAFT' && !email.is_approved && (
                              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                                <ClockIcon className="h-3 w-3 mr-1" />
                                Draft
                              </span>
                            )}
                            {email.type === 'CUSTOMER_REPLY' && (
                              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                <ChatBubbleLeftRightIcon className="h-3 w-3 mr-1" />
                                Customer Reply
                              </span>
                            )}
                          </div>
                          <span className="text-xs text-gray-500">
                            {formatDateTime(email.created_at)}
                          </span>
                        </div>
                        <h4 className="text-sm font-medium text-gray-700 mt-1">{email.subject}</h4>
                      </div>
                      <div className="p-4">
                        <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                          {email.body}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
                );
              });
            })()} 
          </div>
        ) : (
          <div className="text-center py-8 bg-gray-50 rounded-lg">
            <ChatBubbleLeftRightIcon className="mx-auto h-8 w-8 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No communications yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              {user?.role === 'SUPPORT' 
                ? 'Start the conversation by drafting an email to the customer.'
                : 'Our support team will reach out to you soon with updates.'
              }
            </p>
          </div>
        )}

        {/* Customer Reply Section */}
        {user?.role === 'REQUESTER' && (
          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="bg-blue-50 rounded-lg p-4 mb-4">
              <h3 className="text-sm font-medium text-blue-900 mb-2">💬 Send a Reply</h3>
              <p className="text-sm text-blue-700">
                Have additional information or questions? Send a message to our support team.
              </p>
            </div>
            <div className="space-y-4">
              <textarea
                value={customerReply}
                onChange={(e) => setCustomerReply(e.target.value)}
                rows={4}
                className="input resize-none"
                placeholder="Type your message to the support team..."
              />
              <button
                onClick={handleCustomerReply}
                disabled={!customerReply.trim() || customerReplyMutation.isPending}
                className="btn-primary"
              >
                <ChatBubbleLeftRightIcon className="h-4 w-4 mr-2" />
                {customerReplyMutation.isPending ? 'Sending...' : 'Send Message'}
              </button>
            </div>
          </div>
        )}

        {/* Resolution Approval for Customers */}
        {user?.role === 'REQUESTER' && ticket.status === 'ASSIGNED' && (
          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="bg-green-50 rounded-lg p-4 mb-4 border border-green-200">
              <h3 className="text-sm font-medium text-green-900 mb-2">✅ Resolution Approval</h3>
              <p className="text-sm text-green-700">
                Has your issue been resolved? Let us know if the solution worked for you.
              </p>
            </div>
            <div className="space-y-4">
              <textarea
                value={approvalFeedback}
                onChange={(e) => setApprovalFeedback(e.target.value)}
                rows={3}
                className="input resize-none"
                placeholder="Optional: Share your feedback about the resolution..."
              />
              <div className="flex gap-3">
                <button
                  onClick={() => handleApproval(true)}
                  disabled={approvalMutation.isPending}
                  className="btn-success flex-1"
                >
                  <CheckCircleIcon className="h-4 w-4 mr-2" />
                  {approvalMutation.isPending ? 'Submitting...' : '✅ Issue Resolved'}
                </button>
                <button
                  onClick={() => handleApproval(false)}
                  disabled={approvalMutation.isPending}
                  className="btn-danger flex-1"
                >
                  <XCircleIcon className="h-4 w-4 mr-2" />
                  {approvalMutation.isPending ? 'Submitting...' : '❌ Still Need Help'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}