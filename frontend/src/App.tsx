import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import Login from '@/components/auth/Login';
import Layout from '@/components/layout/Layout';
import Dashboard from '@/components/dashboard/Dashboard';
import TicketsList from '@/components/tickets/TicketsList';
import TicketDetail from '@/components/tickets/TicketDetail';
import CreateTicket from '@/components/tickets/CreateTicket';
import RequesterDashboard from '@/components/dashboard/RequesterDashboard';
import SupportDashboard from '@/components/dashboard/SupportDashboard';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="tickets" element={<TicketsList />} />
            <Route path="tickets/new" element={<CreateTicket />} />
            <Route path="tickets/:ticketId" element={<TicketDetail />} />
            <Route path="dashboard/requester" element={<RequesterDashboard />} />
            <Route path="dashboard/support" element={<SupportDashboard />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;