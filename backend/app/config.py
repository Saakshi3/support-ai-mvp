import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Check backend/.env")

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev_only_change_me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

# OpenAI Configuration
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.2")
LLM_API_VERSION = os.getenv("LLM_API_VERSION", "2024-12-01-preview")

if not OPENAI_ENDPOINT or not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_ENDPOINT and OPENAI_API_KEY must be set in .env")

# MCP Server Configuration
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8001"))
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")