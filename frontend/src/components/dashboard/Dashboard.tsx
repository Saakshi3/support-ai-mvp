import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import RequesterDashboard from './RequesterDashboard';
import SupportDashboard from './SupportDashboard';

export default function Dashboard() {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return user.role === 'SUPPORT' ? <SupportDashboard /> : <RequesterDashboard />;
}