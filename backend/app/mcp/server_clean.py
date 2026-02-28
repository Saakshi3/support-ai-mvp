#!/usr/bin/env python3
"""
Support AI MVP - MCP Server
Model Context Protocol server for AI-powered ticket analysis and email drafting
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from sqlalchemy.orm import Session

from app.config import MCP_SERVER_PORT, MCP_SERVER_HOST
from app.db.session import get_db
from app.mcp.tools import (
    analyze_ticket_with_ai,
    draft_email_response,
    approve_and_send_email,
    get_ticket_emails,
    get_ai_audit_logs,
    create_historical_incident,
    get_similar_incidents,
    mark_resolution_used,
    get_ticket,
    list_tickets,
    create_ticket,
    ensure_user
)
from app.schemas.ticket import ResolutionOption

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server instance
server = Server("support-ai-mcp")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all MCP tools available"""
    return [
        Tool(
            name="analyze_ticket",
            description="Analyze a support ticket using InsightsBuddy AI agent to generate resolution suggestions",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "UUID of the ticket to analyze"}
                },
                "required": ["ticket_id"]
            }
        ),
        Tool(
            name="draft_email",
            description="Draft a professional email response using CommCoach AI agent",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "UUID of the ticket"},
                    "resolution_option": {
                        "type": "object",
                        "description": "Selected resolution option",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "confidence_score": {"type": "number"},
                            "reasoning": {"type": "string"},
                            "estimated_time": {"type": "string"},
                            "risk_level": {"type": "string"}
                        },
                        "required": ["title", "description", "confidence_score", "reasoning", "estimated_time", "risk_level"]
                    },
                    "recipient_email": {"type": "string", "description": "Email address of the recipient"},
                    "created_by_user_id": {"type": "string", "description": "UUID of the user creating the email"}
                },
                "required": ["ticket_id", "resolution_option", "recipient_email", "created_by_user_id"]
            }
        ),
        Tool(
            name="get_ticket_info",
            description="Get detailed information about a ticket",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "UUID of the ticket"}
                },
                "required": ["ticket_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle MCP tool calls"""
    try:
        # Get database session
        db_session = next(get_db())
        
        if name == "analyze_ticket":
            ticket_id = UUID(arguments["ticket_id"])
            result = await analyze_ticket_with_ai(db_session, ticket_id=ticket_id)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "ticket_id": str(result.ticket_id),
                    "resolution_options": [
                        {
                            "title": option.title,
                            "description": option.description,
                            "confidence_score": option.confidence_score,
                            "reasoning": option.reasoning,
                            "estimated_time": option.estimated_time,
                            "risk_level": option.risk_level
                        } for option in result.resolution_options
                    ],
                    "similar_incidents_count": result.similar_incidents_count,
                    "analysis_timestamp": result.analysis_timestamp.isoformat(),
                    "audit_log_id": str(result.audit_log_id)
                }, indent=2)
            )]
            
        elif name == "draft_email":
            ticket_id = UUID(arguments["ticket_id"])
            resolution_data = arguments["resolution_option"]
            recipient_email = arguments["recipient_email"]
            created_by_user_id = UUID(arguments["created_by_user_id"])
            
            # Create ResolutionOption object
            resolution_option = ResolutionOption(
                title=resolution_data["title"],
                description=resolution_data["description"],
                confidence_score=resolution_data["confidence_score"],
                reasoning=resolution_data["reasoning"],
                estimated_time=resolution_data["estimated_time"],
                risk_level=resolution_data["risk_level"]
            )
            
            email_draft = await draft_email_response(
                db_session,
                ticket_id=ticket_id,
                resolution_option=resolution_option,
                recipient_email=recipient_email,
                created_by_user_id=created_by_user_id
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "subject": email_draft.subject,
                    "body": email_draft.body,
                    "confidence_score": email_draft.confidence_score,
                    "draft_reasoning": email_draft.draft_reasoning
                }, indent=2)
            )]
            
        elif name == "get_ticket_info":
            ticket_id = UUID(arguments["ticket_id"])
            ticket = get_ticket(db_session, ticket_id)
            
            if not ticket:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Ticket not found"}, indent=2)
                )]
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "ticket_id": str(ticket.ticket_id),
                    "title": ticket.title,
                    "description": ticket.description,
                    "status": ticket.status,
                    "created_by": str(ticket.created_by) if ticket.created_by else None,
                    "assigned_to": str(ticket.assigned_to) if ticket.assigned_to else None,
                    "created_at": ticket.created_at.isoformat(),
                    "updated_at": ticket.updated_at.isoformat()
                }, indent=2)
            )]
            
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
            )]
            
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]
    finally:
        # Close database session
        db_session.close()

async def run_server():
    """Run the MCP server"""
    logger.info(f"🚀 Starting Support AI MCP Server on stdio")
    logger.info(f"📊 Available tools: 3 core AI-powered tools")
    logger.info(f"🤖 InsightsBuddy & CommCoach agents ready")
    
    # Run MCP server using stdio
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    # Run the MCP server
    asyncio.run(run_server())