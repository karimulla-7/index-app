"""
Seed script for Index archival catalog.
Ingests realistic sample files for instant viva and demo presentation.
Usage:
    python seed_catalog.py
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import httpx

BASE_URL = "http://127.0.0.1:8000"
PROJECT_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = PROJECT_DIR / "sample_files"

def seed():
    print("[*] Seeding sample documents into Index...")
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    # Get folders
    folders = client.get("/api/folders").json()
    folder_map = {f["name"]: f["id"] for f in folders}

    samples = [
        ("annual_budget_2024.csv", "text/csv", folder_map.get("Financial & Receipts")),
        ("system_architecture_spec.md", "text/markdown", folder_map.get("Project Specifications")),
        ("employee_handbook_policies.txt", "text/plain", folder_map.get("Academic & Coursework")),
        ("database_optimizer.py", "text/x-python", folder_map.get("Project Specifications")),
        ("student_enrollment_data.json", "application/json", folder_map.get("Academic & Coursework"))
    ]

    for filename, mime, folder_id in samples:
        filepath = SAMPLE_DIR / filename
        if not filepath.exists():
            continue

        with open(filepath, "rb") as f:
            files = [("files", (filename, f, mime))]
            data = {"folder_id": str(folder_id)} if folder_id else {}
            r = client.post("/api/files/upload", files=files, data=data)
            if r.status_code == 200:
                item = r.json()["uploaded"][0]
                print(f"  [OK] Ingested '{filename}' -> Collection: {folder_id or 'Unassigned'}")
            else:
                print(f"  [WARN] Failed '{filename}': {r.text}")

    print("[OK] Seeding complete! Open http://127.0.0.1:8000 in your browser.")

if __name__ == "__main__":
    seed()
