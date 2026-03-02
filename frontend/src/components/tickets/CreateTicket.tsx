import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';
import { Ticket, TicketCreate } from '@/types';

const ticketSchema = z.object({
  title: z.string().min(5, 'Title must be at least 5 characters').max(100, 'Title must be less than 100 characters'),
  description: z.string().min(10, 'Description must be at least 10 characters').max(1000, 'Description must be less than 1000 characters'),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']).default('MEDIUM'),
});

type TicketFormData = z.infer<typeof ticketSchema>;

export default function CreateTicket() {
  const navigate = useNavigate();
  
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<TicketFormData>({
    resolver: zodResolver(ticketSchema),
    defaultValues: {
      priority: 'MEDIUM',
    },
  });

  const createTicketMutation = useMutation({
    mutationFn: async (data: TicketCreate) => {
      const response = await api.post<Ticket>('/tickets', data);
      return response.data;
    },
    onSuccess: (ticket) => {
      toast.success('Ticket created successfully!');
      navigate('/tickets'); // Redirect to tickets list instead of ticket detail
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create ticket');
    },
  });

  const onSubmit = (data: TicketFormData) => {
    createTicketMutation.mutate(data);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Create Support Ticket</h1>
          <p className="mt-2 text-sm text-gray-700">
            Describe your issue and we'll help you resolve it as quickly as possible.
          </p>
        </div>

        {/* Form */}
        <div className="card p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                Issue Title <span className="text-red-500">*</span>
              </label>
              <input
                {...register('title')}
                type="text"
                className="input"
                placeholder="Brief description of your issue"
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Provide a clear, concise title that summarizes your issue
              </p>
            </div>

            {/* Priority */}
            <div>
              <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-2">
                Priority Level
              </label>
              <select {...register('priority')} className="input">
                <option value="LOW">Low - General questions or minor issues</option>
                <option value="MEDIUM">Medium - Moderate impact on work</option>
                <option value="HIGH">High - Significant impact on productivity</option>
                <option value="CRITICAL">Critical - System down or blocking work</option>
              </select>
              {errors.priority && (
                <p className="mt-1 text-sm text-red-600">{errors.priority.message}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                Detailed Description <span className="text-red-500">*</span>
              </label>
              <textarea
                {...register('description')}
                rows={6}
                className="input resize-none"
                placeholder="Please provide detailed information about your issue, including:&#10;• What you were trying to do&#10;• What happened instead&#10;• Any error messages you received&#10;• Steps you've already tried to resolve it"
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                The more details you provide, the faster we can help resolve your issue
              </p>
            </div>

            {/* Tips */}
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <h3 className="text-sm font-medium text-blue-800 mb-2">💡 Tips for faster resolution:</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Include specific error messages if any</li>
                <li>• Mention which browser/device you're using</li>
                <li>• Describe what you expected to happen vs. what actually happened</li>
                <li>• List any troubleshooting steps you've already tried</li>
                <li>• Add screenshots if they would be helpful</li>
              </ul>
            </div>

            {/* Submit Buttons */}
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => navigate('/tickets')}
                className="btn-secondary"
                disabled={isSubmitting || createTicketMutation.isPending}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={isSubmitting || createTicketMutation.isPending}
              >
                {isSubmitting || createTicketMutation.isPending ? 'Creating Ticket...' : 'Create Ticket'}
              </button>
            </div>
          </form>
        </div>

        {/* Support Information */}
        <div className="card p-6 bg-gray-50">
          <h3 className="text-lg font-medium text-gray-900 mb-3">Need immediate help?</h3>
          <div className="space-y-2 text-sm text-gray-600">
            <p><strong>• Critical issues:</strong> Mark as "Critical" priority and we'll respond within 2 hours</p>
            <p><strong>• General questions:</strong> Check our knowledge base or FAQ before creating a ticket</p>
            <p><strong>• Follow-up:</strong> You'll receive email updates on your ticket progress</p>
            <p><strong>• Response time:</strong> We typically respond within 4-8 business hours</p>
          </div>
        </div>
      </div>
    </div>
  );
}