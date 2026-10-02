"""
Main entry point for Index application.
FastAPI application configuration, middleware, routers, and static file serving.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app import database, config
from app.routers import files, folders, search, chat, stats

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite tables and seed data on startup
    database.init_db()
    print("[OK] SQLite database initialized successfully.")
    print(f"[AI] AI Provider: {config.get_active_ai_provider().upper()}")
    yield

app = FastAPI(
    title="Index — AI-Powered Personal File Management System",
    description="An archival library catalog personal file manager with AI auto-tagging, natural language search, and per-file chat.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for open local API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(files.router)
app.include_router(folders.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(stats.router)

# Mount Static Files
static_dir = config.BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    def serve_frontend_root():
        """Serves the Single Page Application index.html."""
        return FileResponse(static_dir / "index.html")
