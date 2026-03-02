import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  TicketIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { api } from '@/lib/api';
import { Ticket } from '@/types';
import { useAuth } from '@/contexts/AuthContext';
import { formatTimeAgo, getStatusColor, getPriorityColor, truncateText } from '@/lib/utils';

export default function TicketsList() {
  const { user } = useAuth();
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  const { data: tickets, isLoading } = useQuery({
    queryKey: ['tickets', statusFilter],
    queryFn: async () => {
      const url = statusFilter ? `/tickets?status=${statusFilter}` : '/tickets';
      const response = await api.get<Ticket[]>(url);
      return response.data;
    },
  });

  const filteredTickets = tickets?.filter(ticket =>
    ticket.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ticket.description.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

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
          <h1 className="text-2xl font-bold text-gray-900">
            {user?.role === 'SUPPORT' ? 'All Tickets' : 'My Tickets'}
          </h1>
          <p className="mt-2 text-sm text-gray-700">
            {user?.role === 'SUPPORT' 
              ? 'Manage and resolve customer support tickets' 
              : 'Track your support requests and their status'
            }
          </p>
        </div>
        {user?.role === 'REQUESTER' && (
          <div className="mt-4 sm:mt-0">
            <Link to="/tickets/new" className="btn-primary">
              <PlusIcon className="h-4 w-4 mr-2" />
              Create Ticket
            </Link>
          </div>
        )}
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <MagnifyingGlassIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search tickets..."
              className="input pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        <div className="sm:flex sm:items-center sm:gap-4">
          <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 sm:mb-0 mb-1">
            Status:
          </label>
          <select
            id="status-filter"
            className="input w-full sm:w-auto"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Status</option>
            <option value="NEW">New</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>
      </div>

      {/* Tickets List */}
      {filteredTickets.length === 0 ? (
        <div className="text-center py-12">
          <TicketIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            {searchQuery || statusFilter ? 'No tickets match your search' : 'No tickets found'}
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {user?.role === 'REQUESTER' 
              ? 'Get started by creating your first support ticket.'
              : 'No tickets to display at the moment.'
            }
          </p>
          {user?.role === 'REQUESTER' && !searchQuery && !statusFilter && (
            <div className="mt-6">
              <Link to="/tickets/new" className="btn-primary">
                <PlusIcon className="h-4 w-4 mr-2" />
                Create Ticket
              </Link>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="space-y-4">
              {filteredTickets.map((ticket) => (
                <div
                  key={ticket.ticket_id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <Link
                          to={`/tickets/${ticket.ticket_id}`}
                          className="text-lg font-medium text-gray-900 hover:text-primary-600"
                        >
                          {ticket.title}
                        </Link>
                        <span className={getStatusColor(ticket.status)}>
                          {ticket.status}
                        </span>
                        <span className={`text-sm font-medium ${getPriorityColor(ticket.priority)}`}>
                          {ticket.priority}
                        </span>
                      </div>
                      
                      <p className="text-sm text-gray-600 mb-3">
                        {truncateText(ticket.description, 150)}
                      </p>
                      
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span>Created {formatTimeAgo(ticket.created_at)}</span>
                        <span>•</span>
                        <span>Category: {ticket.category?.replace('_', ' ') || 'Other'}</span>
                        {ticket.updated_at !== ticket.created_at && (
                          <>
                            <span>•</span>
                            <span>Updated {formatTimeAgo(ticket.updated_at)}</span>
                          </>
                        )}
                      </div>
                    </div>
                    
                    <div className="ml-4">
                      <Link
                        to={`/tickets/${ticket.ticket_id}`}
                        className="btn-secondary text-sm"
                      >
                        View Details
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Stats Footer */}
      {filteredTickets.length > 0 && (
        <div className="text-sm text-gray-500 text-center">
          Showing {filteredTickets.length} ticket{filteredTickets.length !== 1 ? 's' : ''} 
          {statusFilter && ` with status "${statusFilter}"`}
          {searchQuery && ` matching "${searchQuery}"`}
        </div>
      )}
    </div>
  );
}