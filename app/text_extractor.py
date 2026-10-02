"""
Text extraction module for Index.
Extracts searchable text from varied document formats:
- Plain text & Markdown (.txt, .md)
- Tabular & Structured data (.csv, .json, .tsv, .yaml, .xml)
- Code files (.py, .js, .ts, .html, .css, .sql, .java, etc.)
- PDF documents (.pdf via pypdf)
- Microsoft Word documents (.docx via python-docx)
"""

import os
from pathlib import Path
from typing import Tuple

# Extensions categorized as text-based
TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".xml", ".yaml", ".yml",
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".htm", ".css", ".scss",
    ".sql", ".sh", ".bash", ".bat", ".ps1", ".java", ".c", ".cpp", ".h",
    ".cs", ".rs", ".go", ".php", ".rb", ".ini", ".cfg", ".conf", ".log"
}

# Maximum character length to extract for AI token/memory efficiency
MAX_EXTRACT_CHARS = 100_000

def extract_text_from_file(file_path: str, extension: str) -> Tuple[str, bool]:
    """
    Attempts to extract text content from the file at file_path.
    Returns:
        (extracted_text, is_text_based)
    """
    ext = extension.lower().strip()
    path = Path(file_path)

    if not path.exists():
        return "", False

    # 1. Plain text & code files
    if ext in TEXT_EXTENSIONS:
        encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        for enc in encodings_to_try:
            try:
                with open(path, "r", encoding=enc, errors="replace") as f:
                    content = f.read(MAX_EXTRACT_CHARS)
                    return content.strip(), True
            except Exception:
                continue
        return "", True

    # 2. PDF Documents
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            extracted_pages = []
            char_count = 0
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                extracted_pages.append(f"--- Page {i+1} ---\n{page_text}")
                char_count += len(page_text)
                if char_count >= MAX_EXTRACT_CHARS:
                    break
            full_text = "\n\n".join(extracted_pages).strip()
            return full_text, True
        except Exception as e:
            return f"[PDF text extraction notice: {str(e)}]", True

    # 3. Word Documents (.docx)
    if ext == ".docx":
        try:
            import docx
            doc = docx.Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            full_text = "\n\n".join(paragraphs).strip()
            return full_text[:MAX_EXTRACT_CHARS], True
        except Exception as e:
            return f"[DOCX text extraction notice: {str(e)}]", True

    # 4. Binary/Other formats
    return "", False
