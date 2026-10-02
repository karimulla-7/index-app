"""
Database layer for Index using SQLite3.
Provides schema initialization, relational integrity (Foreign Keys ON),
and clean query helpers for Files, Folders, Tags, and Chat History.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.config import DB_PATH

def get_connection() -> sqlite3.Connection:
    """
    Returns a SQLite connection with foreign keys enabled
    and row_factory configured as dict-like sqlite3.Row.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Creates tables and indices if they do not already exist.
    Also creates initial standard folders if the database is newly initialized.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Folders Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            color TEXT DEFAULT '#C09543',
            icon TEXT DEFAULT 'folder',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Files Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
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
        """)

        # 3. Tags Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE COLLATE NOCASE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 4. File-Tags Junction Table (Many-to-Many)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_tags (
            file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
            tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
            is_ai_generated INTEGER DEFAULT 0,
            PRIMARY KEY (file_id, tag_id)
        );
        """)

        # 5. Chat History Table (Per-file interactive Q&A)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Indices for optimal query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_folder ON files(folder_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_tags_file ON file_tags(file_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_tags_tag ON file_tags(tag_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_file ON chat_messages(file_id);")

        # Seed default sample folders if empty
        cursor.execute("SELECT COUNT(*) AS count FROM folders;")
        if cursor.fetchone()["count"] == 0:
            cursor.executemany("""
                INSERT INTO folders (name, description, color, icon) VALUES (?, ?, ?, ?)
            """, [
                ("Academic & Coursework", "Syllabus, notes, research papers, and assignments", "#C09543", "book"),
                ("Financial & Receipts", "Budgets, invoices, spreadsheets, and accounts", "#487E5A", "receipt"),
                ("Project Specifications", "Technical documentation, code notes, and architectures", "#8C5896", "code"),
                ("Personal & Archives", "General letters, journals, and miscellaneous documents", "#A34839", "archive")
            ])

        conn.commit()

# --- Folder Database Operations ---

def get_all_folders() -> List[Dict[str, Any]]:
    """Retrieve all folders along with their item count."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, COUNT(fi.id) AS file_count
            FROM folders f
            LEFT JOIN files fi ON f.id = fi.folder_id
            GROUP BY f.id
            ORDER BY f.name ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

def get_folder_by_id(folder_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single folder by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM folders WHERE id = ?", (folder_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_folder(name: str, description: str = "", color: str = "#C09543", icon: str = "folder") -> Dict[str, Any]:
    """Create a new folder and return its record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO folders (name, description, color, icon) VALUES (?, ?, ?, ?)",
            (name.strip(), description.strip(), color, icon)
        )
        conn.commit()
        folder_id = cursor.lastrowid
        return get_folder_by_id(folder_id)

def delete_folder(folder_id: int) -> bool:
    """Delete a folder. Files inside are unlinked (folder_id set to NULL)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        conn.commit()
        return cursor.rowcount > 0

# --- File Database Operations ---

def insert_file(
    filename: str,
    original_name: str,
    file_path: str,
    file_size: int,
    mime_type: str,
    extension: str,
    folder_id: Optional[int] = None,
    summary: str = "",
    extracted_text: str = ""
) -> int:
    """Insert a new file record and return its ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO files (
                filename, original_name, file_path, file_size,
                mime_type, extension, folder_id, summary, extracted_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            filename, original_name, file_path, file_size,
            mime_type, extension, folder_id, summary, extracted_text
        ))
        conn.commit()
        return cursor.lastrowid

def update_file_ai_data(file_id: int, summary: str, extracted_text: Optional[str] = None):
    """Update AI-generated summary and extracted text."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if extracted_text is not None:
            cursor.execute("""
                UPDATE files
                SET summary = ?, extracted_text = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (summary, extracted_text, file_id))
        else:
            cursor.execute("""
                UPDATE files
                SET summary = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (summary, file_id))
        conn.commit()

def update_file_folder(file_id: int, folder_id: Optional[int]):
    """Move a file to another folder or set to uncategorized (None)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE files SET folder_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (folder_id, file_id))
        conn.commit()

def get_file_by_id(file_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve file record with folder details and associated tags."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, fo.name AS folder_name, fo.color AS folder_color
            FROM files f
            LEFT JOIN folders fo ON f.folder_id = fo.id
            WHERE f.id = ?
        """, (file_id,))
        row = cursor.fetchone()
        if not row:
            return None
        file_dict = dict(row)
        file_dict["tags"] = get_tags_for_file(file_id)
        return file_dict

def get_all_files(
    folder_id: Optional[int] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "newest"
) -> List[Dict[str, Any]]:
    """
    Retrieve files matching query filters: folder_id, tag name, keyword search,
    and sorting order.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT f.*, fo.name AS folder_name, fo.color AS folder_color
            FROM files f
            LEFT JOIN folders fo ON f.folder_id = fo.id
            LEFT JOIN file_tags ft ON f.id = ft.file_id
            LEFT JOIN tags t ON ft.tag_id = t.id
            WHERE 1=1
        """
        params = []

        if folder_id is not None:
            if folder_id == 0 or folder_id == -1: # Uncategorized
                query += " AND f.folder_id IS NULL"
            else:
                query += " AND f.folder_id = ?"
                params.append(folder_id)

        if tag:
            query += " AND LOWER(t.name) = LOWER(?)"
            params.append(tag)

        if search:
            search_param = f"%{search.strip()}%"
            query += """
                AND (
                    f.original_name LIKE ? OR
                    f.summary LIKE ? OR
                    f.extracted_text LIKE ? OR
                    t.name LIKE ?
                )
            """
            params.extend([search_param, search_param, search_param, search_param])

        if sort_by == "oldest":
            query += " ORDER BY f.uploaded_at ASC"
        elif sort_by == "name":
            query += " ORDER BY f.original_name COLLATE NOCASE ASC"
        elif sort_by == "size":
            query += " ORDER BY f.file_size DESC"
        else: # default "newest"
            query += " ORDER BY f.uploaded_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        files = []
        for r in rows:
            f = dict(r)
            f["tags"] = get_tags_for_file(f["id"])
            files.append(f)
        return files

def delete_file_record(file_id: int) -> Optional[Dict[str, Any]]:
    """Delete a file record from SQLite and return its file metadata (to remove physical file)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
        file_row = cursor.fetchone()
        if not file_row:
            return None
        file_dict = dict(file_row)
        cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
        return file_dict

# --- Tag Database Operations ---

def get_or_create_tag(tag_name: str) -> int:
    """Get existing tag ID or insert new tag (case-insensitive)."""
    clean_name = tag_name.strip()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tags WHERE LOWER(name) = LOWER(?)", (clean_name,))
        row = cursor.fetchone()
        if row:
            return row["id"]
        cursor.execute("INSERT INTO tags (name) VALUES (?)", (clean_name,))
        conn.commit()
        return cursor.lastrowid

def add_tag_to_file(file_id: int, tag_name: str, is_ai_generated: bool = False):
    """Associate a tag with a file."""
    tag_id = get_or_create_tag(tag_name)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO file_tags (file_id, tag_id, is_ai_generated)
            VALUES (?, ?, ?)
        """, (file_id, tag_id, 1 if is_ai_generated else 0))
        conn.commit()

def remove_tag_from_file(file_id: int, tag_id: int) -> bool:
    """Disassociate a tag from a file."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM file_tags WHERE file_id = ? AND tag_id = ?", (file_id, tag_id))
        conn.commit()
        return cursor.rowcount > 0

def get_tags_for_file(file_id: int) -> List[Dict[str, Any]]:
    """Retrieve all tags attached to a given file."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.name, ft.is_ai_generated
            FROM tags t
            JOIN file_tags ft ON t.id = ft.tag_id
            WHERE ft.file_id = ?
            ORDER BY ft.is_ai_generated DESC, t.name ASC
        """, (file_id,))
        return [dict(r) for r in cursor.fetchall()]

def get_all_tags_with_counts() -> List[Dict[str, Any]]:
    """Retrieve all tags with their file count usage for the tag cloud."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.name, COUNT(ft.file_id) as count
            FROM tags t
            LEFT JOIN file_tags ft ON t.id = ft.tag_id
            GROUP BY t.id
            HAVING count > 0
            ORDER BY count DESC, t.name ASC
        """)
        return [dict(r) for r in cursor.fetchall()]

# --- Chat Database Operations ---

def add_chat_message(file_id: int, role: str, content: str) -> Dict[str, Any]:
    """Store a chat message in the conversation history for a file."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_messages (file_id, role, content)
            VALUES (?, ?, ?)
        """, (file_id, role, content))
        conn.commit()
        msg_id = cursor.lastrowid
        cursor.execute("SELECT * FROM chat_messages WHERE id = ?", (msg_id,))
        return dict(cursor.fetchone())

def get_chat_history(file_id: int) -> List[Dict[str, Any]]:
    """Retrieve chronological chat history for a file."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, file_id, role, content, created_at
            FROM chat_messages
            WHERE file_id = ?
            ORDER BY created_at ASC, id ASC
        """, (file_id,))
        return [dict(r) for r in cursor.fetchall()]

def clear_chat_history(file_id: int) -> bool:
    """Clear all chat turns for a file."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE file_id = ?", (file_id,))
        conn.commit()
        return True

# --- System Stats ---

def get_system_stats() -> Dict[str, Any]:
    """Compute overall catalog counts and storage sizes."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count, COALESCE(SUM(file_size), 0) as total_size FROM files")
        file_stats = dict(cursor.fetchone())
        cursor.execute("SELECT COUNT(*) as count FROM folders")
        folder_stats = dict(cursor.fetchone())
        cursor.execute("SELECT COUNT(*) as count FROM tags")
        tag_stats = dict(cursor.fetchone())
        cursor.execute("SELECT COUNT(*) as count FROM chat_messages")
        chat_stats = dict(cursor.fetchone())

        return {
            "total_files": file_stats["count"],
            "total_storage_bytes": file_stats["total_size"],
            "total_folders": folder_stats["count"],
            "total_tags": tag_stats["count"],
            "total_chat_messages": chat_stats["count"]
        }
