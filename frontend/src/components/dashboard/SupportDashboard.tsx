import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  TicketIcon,
  ClockIcon,
  CheckCircleIcon,
  SparklesIcon,
  ChartBarIcon,
  UsersIcon
} from '@heroicons/react/24/outline';
import { api } from '@/lib/api';
import { Ticket } from '@/types';
import { formatTimeAgo, getStatusColor, getPriorityColor } from '@/lib/utils';

export default function SupportDashboard() {
  const { data: tickets, isLoading: ticketsLoading } = useQuery({
    queryKey: ['tickets'],
    queryFn: async () => {
      const response = await api.get<Ticket[]>('/tickets');
      return response.data;
    },
  });

  const { data: aiStats, isLoading: aiStatsLoading } = useQuery({
    queryKey: ['ai-statistics'],
    queryFn: async () => {
      const response = await api.get('/ai/statistics');
      return response.data;
    },
  });

  const stats = tickets ? {
    total: tickets.length,
    new: tickets.filter(t => t.status === 'NEW').length,
    assigned: tickets.filter(t => t.status === 'ASSIGNED').length,
    resolved: tickets.filter(t => t.status === 'RESOLVED').length,
    highPriority: tickets.filter(t => t.priority === 'HIGH' || t.priority === 'CRITICAL').length
  } : null;

  const recentTickets = tickets?.slice(0, 5) || [];
  const unassignedTickets = tickets?.filter(t => t.status === 'NEW') || [];

  if (ticketsLoading || aiStatsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Support Dashboard</h1>
          <p className="mt-2 text-sm text-gray-700">
            Monitor tickets, AI performance, and team productivity.
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TicketIcon className="h-6 w-6 text-gray-400" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Total Tickets</dt>
                <dd className="text-lg font-medium text-gray-900">{stats?.total || 0}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ClockIcon className="h-6 w-6 text-yellow-400" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Unassigned</dt>
                <dd className="text-lg font-medium text-gray-900">{stats?.new || 0}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircleIcon className="h-6 w-6 text-green-400" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Resolved</dt>
                <dd className="text-lg font-medium text-gray-900">{stats?.resolved || 0}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <SparklesIcon className="h-6 w-6 text-primary-400" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">AI Analyses</dt>
                <dd className="text-lg font-medium text-gray-900">{aiStats?.total_ai_analyses || 0}</dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* AI Performance Stats */}
      {aiStats && (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
          <div className="card p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ChartBarIcon className="h-6 w-6 text-blue-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Avg AI Confidence
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {(aiStats.average_confidence_score * 100).toFixed(1)}%
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="card p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <SparklesIcon className="h-6 w-6 text-green-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Success Rate
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {aiStats.success_rate}%
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="card p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <UsersIcon className="h-6 w-6 text-purple-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Email Drafts
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {aiStats.total_email_drafts || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Unassigned Tickets */}
        <div className="card">
          <div className="px-4 py-5 sm:p-6">
            <div className="sm:flex sm:items-center sm:justify-between">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Unassigned Tickets
              </h3>
              <div className="mt-3 sm:mt-0 sm:ml-4">
                <Link to="/tickets?status=NEW" className="btn-secondary text-sm">
                  View all
                </Link>
              </div>
            </div>
            <div className="mt-6">
              {unassignedTickets.length === 0 ? (
                <div className="text-center py-6">
                  <CheckCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">All caught up!</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    No unassigned tickets at the moment.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {unassignedTickets.slice(0, 3).map((ticket) => (
                    <div key={ticket.ticket_id} className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <Link
                          to={`/tickets/${ticket.ticket_id}`}
                          className="text-sm font-medium text-gray-900 hover:text-primary-600 truncate"
                        >
                          {ticket.title}
                        </Link>
                        <p className="text-sm text-gray-500">
                          <span className={getPriorityColor(ticket.priority)}>
                            {ticket.priority}
                          </span>
                          {' • '}
                          {formatTimeAgo(ticket.created_at)}
                        </p>
                      </div>
                      <div className="ml-4">
                        <span className={getStatusColor(ticket.status)}>
                          {ticket.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="px-4 py-5 sm:p-6">
            <div className="sm:flex sm:items-center sm:justify-between">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Recent Activity
              </h3>
              <div className="mt-3 sm:mt-0 sm:ml-4">
                <Link to="/tickets" className="btn-secondary text-sm">
                  View all
                </Link>
              </div>
            </div>
            <div className="mt-6">
              {recentTickets.length === 0 ? (
                <div className="text-center py-6">
                  <TicketIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No recent activity</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Recent ticket updates will appear here.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {recentTickets.slice(0, 3).map((ticket) => (
                    <div key={ticket.ticket_id} className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <Link
                          to={`/tickets/${ticket.ticket_id}`}
                          className="text-sm font-medium text-gray-900 hover:text-primary-600 truncate"
                        >
                          {ticket.title}
                        </Link>
                        <p className="text-sm text-gray-500">
                          <span className={getPriorityColor(ticket.priority)}>
                            {ticket.priority}
                          </span>
                          {' • '}
                          {formatTimeAgo(ticket.updated_at)}
                        </p>
                      </div>
                      <div className="ml-4">
                        <span className={getStatusColor(ticket.status)}>
                          {ticket.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}