"""
Convenience entry point for starting the Index server.
Usage:
    python run.py
"""

import sys
import uvicorn
from app import config

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    print("=" * 65)
    print("  * INDEX -- AI-POWERED ARCHIVAL FILE MANAGEMENT SYSTEM *")
    print("  College Project for Computer Science & Business Systems (CSBS)")
    print("=" * 65)
    print(f"  -> Web Interface:      http://{config.HOST}:{config.PORT}")
    print(f"  -> API Documentation:  http://{config.HOST}:{config.PORT}/docs")
    print(f"  -> Active AI Engine:   {config.get_active_ai_provider().upper()}")
    print("=" * 65)

    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True
    )

if __name__ == "__main__":
    main()
