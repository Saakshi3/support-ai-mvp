import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistanceToNow } from 'date-fns';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date) {
  const parsedDate = typeof date === 'string' ? new Date(date) : date;
  return format(parsedDate, 'MMM dd, yyyy');
}

export function formatDateTime(date: string | Date) {
  const parsedDate = typeof date === 'string' ? new Date(date) : date;
  return format(parsedDate, 'MMM dd, yyyy h:mm a');
}

export function formatTimeAgo(date: string | Date) {
  const parsedDate = typeof date === 'string' ? new Date(date) : date;
  return formatDistanceToNow(parsedDate, { addSuffix: true });
}

export function getStatusColor(status: string | undefined | null) {
  if (!status) return 'status-new';
  switch (status.toUpperCase()) {
    case 'NEW':
      return 'status-new';
    case 'ASSIGNED':
      return 'status-assigned';
    case 'RESOLVED':
      return 'status-resolved';
    default:
      return 'status-new';
  }
}

export function getPriorityColor(priority: string | undefined | null) {
  if (!priority) return 'priority-low';
  switch (priority.toUpperCase()) {
    case 'LOW':
      return 'priority-low';
    case 'MEDIUM':
      return 'priority-medium';
    case 'HIGH':
      return 'priority-high';
    case 'CRITICAL':
      return 'priority-critical';
    default:
      return 'priority-low';
  }
}

export function getInitials(name: string | undefined | null) {
  if (!name) return 'U';
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

export function truncateText(text: string, maxLength: number = 100) {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}