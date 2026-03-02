import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  PlusIcon, 
  TicketIcon,
  ClockIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { api } from '@/lib/api';
import { Ticket } from '@/types';
import { formatTimeAgo, getStatusColor } from '@/lib/utils';

export default function RequesterDashboard() {
  const { data: tickets, isLoading } = useQuery({
    queryKey: ['tickets'],
    queryFn: async () => {
      const response = await api.get<Ticket[]>('/tickets');
      return response.data;
    },
  });

  const stats = tickets ? {
    total: tickets.length,
    new: tickets.filter(t => t.status === 'NEW').length,
    assigned: tickets.filter(t => t.status === 'ASSIGNED').length,
    resolved: tickets.filter(t => t.status === 'RESOLVED').length
  } : null;

  const recentTickets = tickets?.slice(0, 5) || [];

  if (isLoading) {
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
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-sm text-gray-700">
            Welcome back! Here's what's happening with your support tickets.
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Link
            to="/tickets/new"
            className="btn-primary"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create Ticket
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TicketIcon className="h-6 w-6 text-gray-400" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Tickets
                </dt>
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
                <dt className="text-sm font-medium text-gray-500 truncate">
                  In Progress
                </dt>
                <dd className="text-lg font-medium text-gray-900">{(stats?.new || 0) + (stats?.assigned || 0)}</dd>
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
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Resolved
                </dt>
                <dd className="text-lg font-medium text-gray-900">{stats?.resolved || 0}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-6 w-6 bg-primary-100 rounded-full flex items-center justify-center">
                <span className="text-xs font-bold text-primary-600">%</span>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Resolution Rate
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {stats?.total ? Math.round((stats.resolved / stats.total) * 100) : 0}%
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Tickets */}
      <div className="card">
        <div className="px-4 py-5 sm:p-6">
          <div className="sm:flex sm:items-center sm:justify-between">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Recent Tickets
            </h3>
            <div className="mt-3 sm:mt-0 sm:ml-4">
              <Link
                to="/tickets"
                className="btn-secondary text-sm"
              >
                View all
              </Link>
            </div>
          </div>
          <div className="mt-6 flow-root">
            {recentTickets.length === 0 ? (
              <div className="text-center py-6">
                <TicketIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No tickets yet</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by creating your first support ticket.
                </p>
                <div className="mt-6">
                  <Link
                    to="/tickets/new"
                    className="btn-primary"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Create Ticket
                  </Link>
                </div>
              </div>
            ) : (
              <ul className="-mb-8">
                {recentTickets.map((ticket, ticketIndex) => (
                  <li key={ticket.ticket_id}>
                    <div className="relative pb-8">
                      {ticketIndex !== recentTickets.length - 1 ? (
                        <span
                          className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                          aria-hidden="true"
                        />
                      ) : null}
                      <div className="relative flex space-x-3">
                        <div>
                          <span className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center ring-8 ring-white">
                            <TicketIcon className="h-4 w-4 text-gray-500" />
                          </span>
                        </div>
                        <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                          <div>
                            <Link
                              to={`/tickets/${ticket.ticket_id}`}
                              className="text-sm font-medium text-gray-900 hover:text-primary-600"
                            >
                              {ticket.title}
                            </Link>
                            <p className="text-sm text-gray-500">
                              Priority: <span className="font-medium">{ticket.priority}</span>
                            </p>
                          </div>
                          <div className="text-right text-sm whitespace-nowrap text-gray-500">
                            <div>
                              <span className={getStatusColor(ticket.status)}>
                                {ticket.status}
                              </span>
                            </div>
                            <div className="mt-1">
                              {formatTimeAgo(ticket.created_at)}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}