# Support AI MVP - Complete Backend Implementation

## Overview

This is a complete AI-powered customer support system with the following key components:

- **InsightsBuddy**: AI agent that analyzes tickets and suggests resolutions based on historical data
- **CommCoach**: AI agent that drafts professional email responses
- **FastAPI Backend**: RESTful API for ticket management and AI interactions
- **MCP Server**: Model Context Protocol server for external AI clients
- **pgvector Database**: PostgreSQL with vector embeddings for similarity search

## 🚀 Features Implemented

✅ **Core Functionality**
- Ticket creation, assignment, and status management
- User authentication and authorization
- AI-powered ticket analysis with confidence scores
- Professional email response generation
- Historical incident storage and similarity search
- Comprehensive audit logging

✅ **AI Agents**
- **InsightsBuddy**: Analyzes tickets using embeddings and LLM
- **CommCoach**: Generates empathetic, professional email responses

✅ **Database Schema**
- Users (REQUESTER/SUPPORT roles)
- Tickets with full lifecycle management
- Historical incidents with vector embeddings
- Email drafts and approved emails
- AI audit logs for compliance

✅ **MCP Integration**
- Full MCP server with 11 available tools
- External AI client integration capabilities
- Tool-based interaction model

## 📋 Prerequisites

1. **Docker & Docker Compose** - For PostgreSQL/pgvector
2. **Python 3.11+** - For backend services
3. **Azure OpenAI Access** - Already configured in `.env`

## 🛠️ Setup Instructions

### 1. Start Database
```bash
# Start pgvector database
cd support-ai-mvp
docker compose up -d

# Verify database is running
docker ps
```

### 2. Setup Backend Environment
```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Initialization
```bash
# Connect to database and run schema setup
docker exec -it pgvector psql -U postgres -d support_ai

# In psql, run the schema creation commands:
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

# Copy and paste the full schema from the original instructions
# (Users, Tickets, Historical Incidents, Emails, AI Audit Log tables)

# Insert test users and tickets
# (Copy the INSERT statements from original instructions)
```

### 4. Start Services

#### Option A: FastAPI Server (REST API)
```bash
cd backend
python start_api_server.py
```
- API available at: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

#### Option B: MCP Server (Model Context Protocol)
```bash
cd backend
python start_mcp_server.py
```
- MCP server available at: ws://localhost:8001
- Provides 11 MCP tools for AI clients

#### Option C: Both (Recommended)
Run both servers in separate terminals for full functionality.

## 🔧 API Endpoints

### Ticket Management
- `GET /tickets` - List tickets (filtered by user role)
- `POST /tickets` - Create new ticket
- `GET /tickets/{ticket_id}` - Get ticket details
- `POST /tickets/{ticket_id}/assign` - Assign ticket to user
- `POST /tickets/{ticket_id}/status` - Update ticket status

### AI-Powered Features
- `POST /tickets/{ticket_id}/analyze` - **Analyze ticket with InsightsBuddy**
- `POST /tickets/{ticket_id}/draft-email` - **Draft email with CommCoach**
- `GET /tickets/{ticket_id}/emails` - Get all ticket emails
- `POST /emails/{email_id}/approve` - Approve and send email
- `GET /tickets/{ticket_id}/audit-logs` - Get AI audit logs

### AI Management
- `POST /ai/historical-incidents` - Create historical incident
- `GET /ai/historical-incidents` - List historical incidents
- `POST /ai/similar-incidents` - Find similar incidents
- `GET /ai/audit-logs` - List all AI audit logs
- `GET /ai/statistics` - Get AI usage statistics

### Authentication
- `POST /auth/login` - User authentication
- Uses JWT tokens for API access

## 🤖 MCP Tools Available

1. **analyze_ticket** - Run AI analysis on tickets
2. **draft_email** - Generate professional email responses
3. **approve_email** - Approve and send emails
4. **get_ticket_info** - Retrieve ticket details
5. **get_ticket_emails** - Get all emails for a ticket
6. **create_historical_incident** - Add training data
7. **find_similar_incidents** - Search similar cases
8. **mark_resolution_used** - Track resolution success
9. **get_audit_logs** - Retrieve AI audit logs
10. **create_user** - User management
11. **create_ticket** - Ticket creation

## 💡 Usage Examples

### 1. Analyze a Ticket (API)
```bash
curl -X POST "http://localhost:8000/tickets/{ticket_id}/analyze" \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json"
```

### 2. Draft Email Response (API)
```bash
curl -X POST "http://localhost:8000/tickets/{ticket_id}/draft-email" \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "resolution_option": {
      "title": "Outlook Sync Fix",
      "description": "Rebuild Outlook profile",
      "confidence_score": 0.85,
      "reasoning": "Common fix for sync issues",
      "estimated_time": "10 minutes",
      "risk_level": "low"
    },
    "recipient_email": "saakshi@supportai.com"
  }'
```

### 3. MCP Client Integration
Connect your AI client to `ws://localhost:8001` and use the available tools.

## 🔍 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Client     │    │  FastAPI App    │    │   pgvector DB   │
│   (MCP Client)  │◄──►│   (REST API)    │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Server    │    │  AI Agents      │    │  Vector Search  │
│   (WebSocket)   │    │  - InsightsBuddy│    │  - Embeddings   │
│                 │    │  - CommCoach    │    │  - Similarity   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Key Components

### InsightsBuddy Agent
- Analyzes ticket content using embeddings
- Finds similar historical incidents
- Generates resolution suggestions with confidence scores
- Provides reasoning and risk assessment

### CommCoach Agent
- Creates professional email responses
- Ensures empathy, clarity, and action steps
- Maintains consistent tone and formatting
- Adaptive based on resolution context

### Audit System
- Logs all AI interactions
- Tracks resolution success rates
- Enables compliance reporting
- Supports continuous improvement

## 🔒 Security Features

- JWT-based authentication
- Role-based access control (REQUESTER/SUPPORT)
- Input validation and sanitization
- Comprehensive audit logging
- Secure database connections

## 📈 Monitoring & Analytics

The system provides comprehensive analytics through:
- AI usage statistics
- Resolution success rates
- Average confidence scores
- Audit trail for all AI decisions

## 🧪 Testing

### Test Users Available
- **saakshi@supportai.com** - REQUESTER role
- **anjali@supportai.com** - SUPPORT role

### Test Tickets
5 realistic Microsoft support tickets are pre-loaded for testing.

## 🚀 Next Steps

1. **Add Historical Incidents**: Populate more training data for better AI suggestions
2. **Email Integration**: Connect to actual email service (Azure Graph API)
3. **Embedding Generation**: Set up background jobs for embedding creation
4. **Frontend**: Build React/Vue.js frontend for complete user experience
5. **Monitoring**: Add application monitoring and logging

## 🐛 Troubleshooting

### Common Issues
1. **Database Connection**: Ensure pgvector container is running
2. **OpenAI API**: Verify Azure OpenAI credentials in `.env`
3. **Dependencies**: Run `pip install -r requirements.txt`
4. **Port Conflicts**: Check ports 5432 (DB), 8000 (API), 8001 (MCP)

### Logs Location
- FastAPI logs: Console output
- MCP server logs: Console output
- Database logs: `docker logs pgvector`

---

**🎉 Your Support AI MVP is now ready for use!**

The system provides a complete AI-powered support workflow from ticket analysis to professional email responses, all with comprehensive audit trails and both REST API and MCP interfaces for maximum flexibility.