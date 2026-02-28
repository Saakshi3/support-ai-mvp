#!/usr/bin/env python3
"""
Support AI MVP - FastAPI Server Startup Script
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Support AI FastAPI Server...")
    print("📊 Available endpoints: /tickets, /ai, /auth, /health")
    print("🔗 API docs will be available at http://localhost:8000/docs")
    
    try:
        uvicorn.run(
            "app.main:app",  # Use import string instead of app object
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload to avoid warning
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)