# INDEX — AI-Powered Personal File Management System
> **Academic Capstone Project**  
> **Program:** Computer Science and Business Systems (CSBS)  
> **Course:** Enterprise Information Systems & Applied Artificial Intelligence  
> **Design Theme:** Archival Library Catalog & Document Chamber

---

## 1. Executive Summary & Business Rationale (CSBS Focus)

Modern knowledge organizations suffer from **"unstructured document dark data"** — thousands of invoices, contracts, technical specifications, and research memos are saved with arbitrary names across fragmented drives. Traditional file systems rely on rigid folder trees and exact keyword matching, making discovery tedious and prone to human error.

**Index** bridges Computer Science and Business Systems principles by merging:
1. **Relational Data Integrity (ACID compliance via SQLite)** for deterministic cataloging, metadata retention, and relational indexing.
2. **Generative & Semantic AI (Google Gemini LLM / Heuristic Engine)** for automated document classification, semantic intent search ("Ask" mode), and interactive per-document Q&A.
3. **Archival Library Aesthetic**: A distraction-free UI inspired by antique library catalog cards, parchment tones, and brass accents that prioritize legibility and metadata density over generic SaaS templates.

---

## 2. System Architecture

```
                                  +---------------------------------------+
                                  |            Client Browser             |
                                  | (Single Page App: HTML5 / CSS3 / ES6) |
                                  +---------------------------------------+
                                                      |
                                                      | HTTP / REST API
                                                      v
+---------------------------------------------------------------------------------------------------+
|                                      FastAPI Backend Engine                                       |
|                                                                                                   |
|  +--------------------+   +----------------------+   +-------------------+   +-----------------+  |
|  | /api/files         |   | /api/folders & tags  |   | /api/search/ask   |   | /api/chat       |  |
|  | Upload/Download/Del|   | Collections & Taxon. |   | Natural Lang Retr.|   | Grounded Q&A    |  |
|  +--------------------+   +----------------------+   +-------------------+   +-----------------+  |
|            |                         |                         |                      |           |
+------------|-------------------------|-------------------------|----------------------|-----------+
             |                         |                         |                      |
             v                         v                         v                      v
  +--------------------+   +---------------------------------------+   +----------------------------+
  |    Local Storage   |   |           SQLite Database             |   |         AI Service         |
  |    data/uploads/   |   |             data/index.db             |   |     (Google Gemini API     |
  | (UUID Hashed Disk) |   | (Files, Folders, Tags, Chat Messages) |   |  or Offline Viva Fallback) |
  +--------------------+   +---------------------------------------+   +----------------------------+
```

---

## 3. Core Features

### 1. Document Ingestion & Storage
- **Drag-and-Drop Dropzone**: Drag documents directly into the catalog dropzone or use the system file picker.
- **Disk Storage**: Files are saved to `data/uploads/` prefixed with collision-resistant UUIDs (`uuid4().hex_filename`).
- **Multi-Format Text Extraction**:
  - Plaintext & Markdown: `.txt`, `.md`
  - Structured Data: `.csv`, `.tsv`, `.json`, `.yaml`, `.xml`
  - Source Code: `.py`, `.js`, `.ts`, `.html`, `.css`, `.sql`, `.java`, `.cpp`, `.c`
  - Formatted Documents: `.pdf` (via `pypdf`), `.docx` (via `python-docx`)

### 2. Automated AI Tagging & Summarization
- On upload, the backend extracts document text and dispatches it to the AI engine.
- Generates **3 to 5 domain-relevant subject tags** (auto-populated in the sidebar tag cloud).
- Synthesizes a **crisp one-sentence executive summary** embedded onto each library card.

### 3. Natural-Language Search ("Ask" Mode)
- Query files using human conversational language (e.g., *"budget spreadsheets from last month"*, *"architecture specifications for databases"*).
- The AI engine analyzes document metadata and summaries across the catalog, returning ranked matches paired with an **Archival Synthesis Explanation** banner explaining why those files were selected.
- Switch seamlessly between **"Ask AI"** and **"Keyword Filter"** modes with the header toggle.

### 4. Per-File Conversational AI Chat ("Inquire with the Archivist")
- Clicking any catalog card opens the slide-over **Inspector Drawer**.
- The **"Inquire with AI"** tab allows users to ask specific questions about that document.
- Answers are strictly grounded in the document's content.
- Conversation history is preserved across turns in SQLite.
- Includes starter question chips (*"Bullet breakdown"*, *"Extract metrics"*, *"Action items"*) and a clear history button.

### 5. Collections & Subject Taxonomies
- Organize files into custom Collections with custom brass/foil color badges.
- Interactive Tag Cloud in the sidebar with item count badges for instant multi-tag filtering.
- Full manual tag management (add manual tags, remove existing tags).

### 6. Archival Library Catalog Aesthetic
- **Palette**: Warm cream parchment background (`#F8F5EE`), deep India ink typography (`#1C1917`), and burnished brass/gold accents (`#C09543`).
- **Typography**: Display headings in *Fraunces* serif; body text in *IBM Plex Sans*; code snippets in *JetBrains Mono*.
- **Nocturne / Dark Mode**: Toggle between Warm Parchment (Light) and Antique Study Leather (Dark).
- **Responsive**: Fully responsive across desktop, tablet, and mobile.

---

## 4. Database Schema (SQLite)

Foreign keys are strictly enforced on every connection (`PRAGMA foreign_keys = ON;`).

```sql
-- 1. Folders (Collections)
CREATE TABLE folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    color TEXT DEFAULT '#C09543',
    icon TEXT DEFAULT 'folder',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Files (Documents & Metadata)
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    original_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    extension TEXT NOT NULL,
    folder_id INTEGER REFERENCES folders(id) ON DELETE SET NULL,
    summary TEXT DEFAULT '',
    extracted_text TEXT DEFAULT '',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tags (Subject Index)
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. File-Tags (M:N Relational Junction)
CREATE TABLE file_tags (
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    is_ai_generated INTEGER DEFAULT 0,
    PRIMARY KEY (file_id, tag_id)
);

-- 5. Chat History (Per-File Conversational Turns)
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. Quick Start & Setup Instructions

### Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- Modern web browser (Chrome, Edge, Firefox, Safari)

### Step 1: Clone or Navigate to Project
```powershell
cd c:\Users\Pattan\Downloads\index-app
```

### Step 2: Activate the Virtual Environment
Windows PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```
*(Or create a new one: `python -m venv venv` followed by `pip install -r requirements.txt`)*

### Step 3: Configure Environment Variables (.env)
The project comes with a pre-configured `.env` file.  
To connect a live Google Gemini LLM, add your API key:
```env
GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

> **Note on Viva / Offline Resilience:**  
> If `GEMINI_API_KEY` is left blank, **Index automatically activates its built-in Intelligent Heuristic Engine**. This guarantees that all features (tagging, summarization, search matching, and chat) remain 100% operational during offline presentations or spotty network conditions without any crashes.

### Step 4: Run the Application
```powershell
python run.py
```
Or with uvicorn directly:
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 5: Access the Interface
- **Main Web Application:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI / Swagger Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 6. Demo & Seed Data

To populate the catalog with realistic sample documents for a viva demonstration:
```powershell
python seed_catalog.py
```
This loads:
1. `annual_budget_2024.csv` — Departmental budget and variances (try asking: *"budget spreadsheets from last month"*).
2. `system_architecture_spec.md` — High-availability specification and database schemas.
3. `employee_handbook_policies.txt` — Remote work rules, per diem rates, and travel allowances.
4. `database_optimizer.py` — Python EXPLAIN query execution utility.
5. `student_enrollment_data.json` — CSBS student registry and course enrollment data.

---

## 7. Running Integration Tests

To run the automated 10-step end-to-end verification suite:
```powershell
python test_flow.py
```
This script programmatically verifies:
- [x] System health and status endpoint
- [x] Seed folder listing
- [x] Multi-format upload and text extraction
- [x] AI auto-tagging and summary generation
- [x] Tag cloud discovery
- [x] Manual tag addition and removal
- [x] Natural language "Ask" search with semantic ranking and explanation
- [x] Multi-turn document chat with context retention
- [x] Physical file download
- [x] Folder creation and file reassignment
- [x] Cascade deletion from database and physical disk

---

## 8. Viva / Evaluation Talking Points (CSBS Focus)

1. **Why keep the LLM API key strictly on the backend?**
   - *Security & Compliance*: Exposing API keys in client-side JavaScript allows malicious users to extract credentials, leading to quota exhaustion and financial liabilities. The backend acts as a secure, authenticated gateway.

2. **Why use SQLite over a NoSQL database for this system?**
   - *Relational Integrity*: SQLite enforces foreign key constraints (`ON DELETE CASCADE` for file tags and chat history), preventing orphaned records. Write-Ahead Logging (WAL) ensures high read throughput while maintaining ACID guarantees.

3. **How does the Natural Language "Ask" Search work?**
   - In "Ask" mode, the user's natural query is passed alongside an optimized catalog summary footprint (filenames, tags, AI summaries, upload timestamps) to the LLM. The model interprets intent (e.g. associating "spreadsheets" with `.csv` files and "financial amounts" with budgets), returning ranked matching IDs and a concise rationale.

4. **How is context handled in per-file chat?**
   - The backend retrieves the document's extracted text alongside recent conversational turns (`chat_messages` table). This payload is injected into a specialized archivist system prompt, ensuring answers are strictly fact-based and anchored in the document without hallucination.

5. **How does the system ensure zero failure during offline demos?**
   - The AI layer uses an adapter pattern. If the external LLM key is absent or network unreachable, the application falls back to an intelligent heuristic engine using token frequency, TF-IDF scoring, and sentence ranking. The system never crashes with 500 errors.

---

## 9. Project Directory Tree

```
index-app/
├── app/
│   ├── __init__.py           # Package initializer
│   ├── config.py             # Settings, paths, and environment variables
│   ├── database.py           # SQLite connection, schema, and queries
│   ├── text_extractor.py     # Multi-format parser (.txt, .md, .csv, .json, .pdf, .docx)
│   ├── ai_service.py         # Google Gemini & Heuristic fallback engine
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── files.py          # Upload, download, metadata, and tags
│   │   ├── folders.py        # Collections and tag cloud
│   │   ├── search.py         # Natural language "Ask" search
│   │   ├── chat.py           # Per-file Q&A chat history
│   │   └── stats.py          # System status and analytics
│   └── main.py               # FastAPI entry point, CORS, and static file mount
├── data/
│   ├── index.db              # SQLite database
│   └── uploads/              # Local storage for uploaded files
├── static/
│   ├── index.html            # Single Page Application
│   ├── css/
│   │   └── style.css         # Archival library catalog stylesheet (Light & Dark)
│   └── js/
│       ├── api.js            # REST API client
│       └── app.js            # SPA Controller: Drag & drop, search, inspector, chat
├── sample_files/             # Test files (budgets, architecture, handbook, code)
├── .env.example              # Environment template
├── .env                      # Active configuration
├── requirements.txt          # Python dependencies
├── run.py                    # Server launch script (python run.py)
├── seed_catalog.py           # Demo seeding script
├── test_flow.py              # Automated 10-step integration test suite
└── README.md                 # Project documentation & viva guide
```
