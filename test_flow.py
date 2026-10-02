"""
Integration test script for Index.
Validates the complete workflow:
Upload -> AI Auto-tag & Summary -> Folders & Tags -> Ask AI Search -> Per-file Chat -> Download -> Delete
"""

import os
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
import httpx

BASE_URL = "http://127.0.0.1:8000"
PROJECT_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = PROJECT_DIR / "sample_files"

def run_tests():
    print("=" * 60)
    print("BEGINNING END-TO-END INDEX INTEGRATION VERIFICATION")
    print("=" * 60)

    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    # 1. System Health Check
    print("\n[1] Testing System Status Endpoint...")
    r = client.get("/api/system/status")
    assert r.status_code == 200, f"Status check failed: {r.text}"
    status_data = r.json()
    print("  [OK] Status OK:", status_data["app_name"])
    print("  [OK] Active AI Provider:", status_data["ai"]["active_provider"])

    # 2. Check Seed Folders
    print("\n[2] Testing Folders Listing...")
    r = client.get("/api/folders")
    assert r.status_code == 200
    folders = r.json()
    print(f"  [OK] Found {len(folders)} default folders:")
    for f in folders:
        print(f"    - [{f['id']}] {f['name']} ({f['file_count']} files)")
    assert len(folders) >= 4, "Expected seeded folders"

    # Find the 'Financial & Receipts' folder for the budget file
    finance_folder_id = next((f["id"] for f in folders if "Financial" in f["name"]), folders[0]["id"])
    project_folder_id = next((f["id"] for f in folders if "Project" in f["name"]), folders[1]["id"])

    # 3. File Upload & AI Auto-tagging
    print("\n[3] Testing File Ingestion & AI Auto-tagging...")
    
    # Upload budget CSV into Finance folder
    budget_path = SAMPLE_DIR / "annual_budget_2024.csv"
    with open(budget_path, "rb") as bf:
        files = [("files", ("annual_budget_2024.csv", bf, "text/csv"))]
        data = {"folder_id": str(finance_folder_id)}
        r = client.post("/api/files/upload", files=files, data=data)
        assert r.status_code == 200, f"Budget upload failed: {r.text}"
        budget_upload = r.json()["uploaded"][0]
        budget_id = budget_upload["id"]
        print(f"  [OK] Uploaded '{budget_upload['original_name']}' (ID: {budget_id})")
        print(f"    - AI Summary: {budget_upload['summary']}")
        print(f"    - Extracted Text length: {len(budget_upload['extracted_text'])} chars")
        print(f"    - Auto-generated Tags: {[t['name'] for t in budget_upload['tags']]}")
        assert len(budget_upload["tags"]) >= 2, "Expected auto-generated tags"

    # Upload system architecture markdown into Project folder
    arch_path = SAMPLE_DIR / "system_architecture_spec.md"
    with open(arch_path, "rb") as af:
        files = [("files", ("system_architecture_spec.md", af, "text/markdown"))]
        data = {"folder_id": str(project_folder_id)}
        r = client.post("/api/files/upload", files=files, data=data)
        assert r.status_code == 200, f"Architecture upload failed: {r.text}"
        arch_upload = r.json()["uploaded"][0]
        arch_id = arch_upload["id"]
        print(f"  [OK] Uploaded '{arch_upload['original_name']}' (ID: {arch_id})")
        print(f"    - AI Summary: {arch_upload['summary']}")
        print(f"    - Auto-generated Tags: {[t['name'] for t in arch_upload['tags']]}")

    # Upload student enrollment JSON
    student_path = SAMPLE_DIR / "student_enrollment_data.json"
    with open(student_path, "rb") as sf:
        files = [("files", ("student_enrollment_data.json", sf, "application/json"))]
        r = client.post("/api/files/upload", files=files)
        assert r.status_code == 200
        student_upload = r.json()["uploaded"][0]
        student_id = student_upload["id"]
        print(f"  [OK] Uploaded '{student_upload['original_name']}' (ID: {student_id})")

    # 4. Check Tags Endpoint
    print("\n[4] Testing Tags Cloud Discovery...")
    r = client.get("/api/tags")
    assert r.status_code == 200
    tags = r.json()
    print(f"  [OK] Catalog now has {len(tags)} subject tags:")
    print("   ", ", ".join([f"#{t['name']} ({t['count']})" for t in tags[:8]]))

    # 5. Manual Tag Addition
    print("\n[5] Testing Manual Tag Management...")
    r = client.post(f"/api/files/{budget_id}/tags", json={"tag_name": "quarterly-report"})
    assert r.status_code == 200
    updated_tags = [t["name"] for t in r.json()["tags"]]
    print(f"  [OK] Added manual tag 'quarterly-report'. Current tags: {updated_tags}")
    assert "quarterly-report" in updated_tags

    # 6. Natural Language Search ("Ask" mode)
    print("\n[6] Testing Natural Language Search ('Ask' mode)...")
    query = "budget spreadsheets from last month"
    print(f"  Query: '{query}'")
    r = client.post("/api/search/ask", json={"query": query})
    assert r.status_code == 200, f"Ask search failed: {r.text}"
    search_data = r.json()
    print("  [OK] AI Explanation:", search_data["explanation"])
    print(f"  [OK] Matched Files ({len(search_data['files'])}):")
    for mf in search_data["files"]:
        print(f"    - [{mf['id']}] {mf['original_name']} | Summary: {mf['summary'][:70]}...")
    assert budget_id in search_data["matched_file_ids"], "Budget file should be matched by query!"

    # 7. Per-File AI Chat
    print("\n[7] Testing Per-File Interactive AI Chat...")
    chat_prompt = "Which department allocated funds for GPU compute clusters and how much was spent?"
    print(f"  User Prompt: '{chat_prompt}'")
    r = client.post(f"/api/chat/{budget_id}/message", json={"message": chat_prompt})
    assert r.status_code == 200, f"Chat message failed: {r.text}"
    chat_res = r.json()
    print("  [OK] Assistant Response:\n" + chat_res["message"]["content"])

    # Follow-up Chat Turn
    followup_prompt = "What was the total expenditure across all departments?"
    print(f"\n  Follow-up Prompt: '{followup_prompt}'")
    r = client.post(f"/api/chat/{budget_id}/message", json={"message": followup_prompt})
    assert r.status_code == 200
    print("  [OK] Follow-up Response:\n" + r.json()["message"]["content"])

    # Verify Chat History
    r = client.get(f"/api/chat/{budget_id}/history")
    assert r.status_code == 200
    history = r.json()["messages"]
    print(f"  [OK] Chat history preserved: {len(history)} turns stored in SQLite database.")
    assert len(history) == 4, f"Expected 4 turns (2 user, 2 assistant), got {len(history)}"

    # 8. File Download
    print("\n[8] Testing Physical File Download...")
    r = client.get(f"/api/files/{budget_id}/download")
    assert r.status_code == 200
    assert "Department,Quarter,Category" in r.text
    print(f"  [OK] Downloaded {len(r.content)} bytes of '{budget_upload['original_name']}' successfully.")

    # 9. Create New Folder & Move Document
    print("\n[9] Testing Folder Creation & Document Reassignment...")
    r = client.post("/api/folders", json={
        "name": "Executive Board Presentations",
        "description": "Board meeting decks and strategic forecasts",
        "color": "#3E6B89"
    })
    assert r.status_code == 200
    new_folder = r.json()
    print(f"  [OK] Created new folder: '{new_folder['name']}' (ID: {new_folder['id']})")

    r = client.put(f"/api/files/{arch_id}/folder", json={"folder_id": new_folder["id"]})
    assert r.status_code == 200
    assert r.json()["folder_id"] == new_folder["id"]
    print(f"  [OK] Moved '{arch_upload['original_name']}' into '{new_folder['name']}'.")

    # 10. File Deletion
    print("\n[10] Testing Document Deletion...")
    r = client.delete(f"/api/files/{student_id}")
    assert r.status_code == 200
    print(f"  [OK] File ID {student_id} successfully deleted from SQLite and disk.")

    # Verify 404 on deleted file
    r = client.get(f"/api/files/{student_id}")
    assert r.status_code == 404
    print("  [OK] Confirmed file record is completely expunged (404 Not Found).")

    print("\n" + "=" * 60)
    print("ALL 10 VERIFICATION STEPS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
