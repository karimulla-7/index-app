"""
Configuration settings for Index File Management System.
Handles environment variables, storage paths, and AI provider choices.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory is the project root (where run.py and .env live)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from project root
load_dotenv(BASE_DIR / ".env")

# Storage & Database paths
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "index.db"

# Server Settings
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))

# AI Configuration
# Providers: "gemini", "openai", or "auto" (will auto-detect available keys)
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()

# Google Gemini Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

# OpenAI Compatible Settings (Optional alternative)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()

def get_active_ai_provider() -> str:
    """
    Returns the currently active AI provider.
    Falls back gracefully to 'local_heuristic' if no valid API key is present.
    """
    if GEMINI_API_KEY:
        return "gemini"
    elif OPENAI_API_KEY:
        return "openai"
    return "local_heuristic"
