#!/usr/bin/env python3
"""
Support AI MVP - MCP Server Startup Script
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app.mcp.server import run_server
import asyncio

if __name__ == "__main__":
    print("🚀 Starting Support AI MCP Server...")
    print("📊 Available tools: analyze_ticket, draft_email, approve_email, get_ticket_info, etc.")
    print("🔌 Server running on stdio (standard input/output)")
    print("🤖 InsightsBuddy & CommCoach AI agents ready")
    print("")
    print("ℹ️  To connect an MCP client, pipe to this process or use JSON-RPC over stdio")
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\n🛑 MCP Server stopped by user")
    except Exception as e:
        print(f"❌ MCP Server error: {e}")
        sys.exit(1)