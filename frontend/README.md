# Support AI Frontend

A modern React TypeScript frontend for the Support AI MVP system, featuring role-based dashboards, AI-powered ticket analysis, and real-time communication workflows.

## Features

### 🔐 Authentication & Authorization
- Secure JWT-based authentication
- Role-based access control (REQUESTER vs SUPPORT)
- Protected routes and conditional UI elements

### 🎯 Role-Specific Dashboards
- **Customer Dashboard**: Personal ticket overview, creation, and tracking
- **Support Dashboard**: Team metrics, AI analytics, and ticket management
- Real-time statistics and performance indicators

### 🎫 Advanced Ticket Management
- Create, view, and track support tickets
- Priority-based categorization (LOW/MEDIUM/HIGH/CRITICAL)
- Status tracking (NEW/ASSIGNED/RESOLVED)
- Advanced filtering and search capabilities

### 🤖 AI-Powered Features
- **InsightsBuddy**: Intelligent ticket analysis and resolution suggestions
- **CommCoach**: Professional email drafting with tone adaptation
- Confidence scoring and reasoning for AI recommendations
- Pattern-based fallback system

### 💬 Enhanced Communication Flow
- Bidirectional email communication
- Customer reply capabilities
- Resolution approval workflow
- Communication history tracking
- Real-time status updates

## Technology Stack

- **Frontend**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **Routing**: React Router v6
- **State Management**: TanStack Query (React Query)
- **Forms**: React Hook Form with Zod validation
- **HTTP Client**: Axios with interceptors
- **UI Components**: Headless UI + Hero Icons
- **Build Tool**: Vite
- **Development**: Hot reload, TypeScript checking

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Start development server**
   ```bash
   npm run dev
   ```

3. **Open browser**
   Navigate to http://localhost:3000

### Demo Accounts

The system works with hardcoded demo accounts:

**Customer Account:**
- Email: `saakshi@support.ai`
- Password: `password123`
- Role: REQUESTER

**Support Agent Account:**
- Email: `anjali@support.ai` 
- Password: `password123`
- Role: SUPPORT

## User Workflows

### Customer (REQUESTER) Flow

1. **Login** with customer credentials
2. **Dashboard** - View ticket statistics and recent activity
3. **Create Ticket** - Submit new support requests with priority levels
4. **Track Progress** - Monitor ticket status and communications
5. **Communicate** - Reply to support team messages
6. **Approve Resolution** - Accept/reject proposed solutions

### Support Agent (SUPPORT) Flow

1. **Login** with support credentials  
2. **Dashboard** - View team metrics and AI performance
3. **Manage Tickets** - Review and assign tickets from queue
4. **AI Analysis** - Use InsightsBuddy for intelligent ticket analysis
5. **Draft Communications** - Use CommCoach for professional emails
6. **Send Updates** - Communicate resolution progress to customers
7. **Monitor Performance** - Track AI confidence scores and success rates

## Key Components

### Authentication System
```typescript
// Protected route wrapper
<ProtectedRoute requiredRole="SUPPORT">
  <SupportOnlyComponent />
</ProtectedRoute>
```

### API Integration
```typescript
// Type-safe API calls with automatic error handling
const { data: tickets } = useQuery({
  queryKey: ['tickets'],
  queryFn: () => api.get<Ticket[]>('/tickets')
});
```

### AI Feature Integration
```typescript
// AI analysis with loading states
const analysisMutation = useMutation({
  mutationFn: () => api.post(`/tickets/${id}/analyze`),
  onSuccess: (result) => setAnalysisResult(result)
});
```

## Development Commands

```bash
# Development server
npm run dev

# Type checking
npm run type-check

# Build for production  
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

## API Configuration

The frontend is configured to proxy API requests to the backend:

```typescript
// vite.config.ts - API proxy configuration
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## Styling & Design

### Custom Design System
- Primary color scheme with blue/indigo tones
- Status-specific styling (success, warning, danger)
- Consistent spacing and typography
- Responsive grid layouts

### Component Classes
```css
/* Utility classes for consistent styling */
.btn-primary { /* Primary action buttons */ }
.btn-secondary { /* Secondary actions */ }
.status-badge { /* Status indicators */ }
.card { /* Content containers */ }
```

## Error Handling & UX

- **Loading States**: Skeleton screens and spinners during API calls
- **Error Boundaries**: Graceful error handling with user feedback
- **Toast Notifications**: Success/error messages for user actions
- **Form Validation**: Real-time validation with helpful messages
- **Offline Support**: Graceful degradation when backend unavailable

## Security Features

- **JWT Token Management**: Automatic token refresh and logout
- **Role-Based Access**: UI elements shown/hidden based on permissions  
- **Input Validation**: Client and server-side validation
- **CSRF Protection**: Secure API communication
- **Session Management**: Persistent authentication across browser sessions

## Performance Optimizations

- **Code Splitting**: Lazy loading of route components
- **Query Caching**: TanStack Query for efficient data fetching
- **Bundle Optimization**: Vite's optimized production builds
- **Image Optimization**: Responsive images and lazy loading
- **Network Efficiency**: Request deduplication and background updates

## Accessibility

- **Keyboard Navigation**: Full keyboard support for all interactions
- **Screen Reader Support**: Proper ARIA labels and semantic HTML
- **Color Contrast**: WCAG AA compliant color schemes
- **Focus Management**: Clear focus indicators and logical tab order
- **Responsive Design**: Works across all device sizes and orientations

## Future Enhancements

- **Real-time Updates**: WebSocket integration for live notifications
- **File Upload**: Attachment support for tickets and communications  
- **Advanced Analytics**: Detailed reporting and metrics dashboard
- **Multi-language**: Internationalization support
- **Dark Mode**: Theme switching capabilities
- **PWA Features**: Offline support and push notifications

## Troubleshooting

### Common Issues

1. **Build Errors**: Ensure TypeScript types match API responses
2. **Network Issues**: Check backend API is running on port 8000
3. **Authentication**: Clear localStorage if login issues persist
4. **Styling**: Run `npm run build` to ensure CSS is properly processed

### Development Tips

- Use browser dev tools React extension for component debugging
- Enable network tab to monitor API calls and responses
- Check console for TypeScript errors and warnings
- Use the React Query dev tools for query state inspection

This frontend provides a complete, production-ready interface for the Support AI MVP system with modern UX patterns and robust error handling.