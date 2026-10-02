"""
AI Service module for Index.
Handles:
1. Auto-tagging & Summarization on file upload
2. Natural-language "Ask" search matching
3. Interactive Per-file Q&A Chat

Supports:
- Google Gemini API (v1beta REST via httpx)
- OpenAI API (via httpx)
- Offline Intelligent Heuristic fallback (guarantees viva/demo never fails if API key is absent)
"""

import json
import re
import collections
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import httpx
from app import config

# --- Prompt Templates ---

TAG_SUMMARY_PROMPT = """You are an expert archival cataloger. Analyze the following document text and metadata.
Filename: {filename}
Extension: {extension}

Document Content Sample:
\"\"\"
{content}
\"\"\"

Respond strictly with a JSON object in this exact schema:
{{
  "summary": "A concise, informative one-sentence summary of the document's contents and purpose.",
  "tags": ["tag1", "tag2", "tag3", "tag4"]
}}
Generate between 3 to 5 lowercase tags that accurately classify the document's topic, format, or domain.
"""

SEARCH_ASK_PROMPT = """You are a smart file retrieval assistant. A user has typed the following natural language search request:
User Query: "{query}"

Here is the catalog of available files:
{catalog_json}

Analyze which files best match the user's intent, topic, date, or content.
Respond strictly in JSON format with this exact structure:
{{
  "matched_file_ids": [1, 4],
  "explanation": "Brief 1-2 sentence explanation of what was searched for and why these files match."
}}
If no files match well, return an empty array for matched_file_ids and explain why.
"""

CHAT_SYSTEM_PROMPT = """You are the Index Archivist, an AI assistant dedicated to answering questions about this specific document.
You have access to the document's content below. Answer accurately, clearly, and cite details directly from the text.
If the answer is not contained in the text, politely state that the document does not contain that information.

Document Name: {filename}
Document Content:
\"\"\"
{content}
\"\"\"
"""

# --- Fallback Heuristic Helpers (Offline / No Key Mode) ---

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "did", "do",
    "does", "doing", "don't", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it", "its",
    "itself", "let's", "me", "more", "most", "my", "myself", "no", "nor", "not",
    "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such",
    "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "with", "won't", "would", "you", "your", "yours"
}

def _heuristic_tag_and_summary(filename: str, extension: str, content: str) -> Dict[str, Any]:
    """Generates clean tags and a summary offline without external API."""
    clean_name = Path(filename).stem.replace("_", " ").replace("-", " ")
    
    if not content or len(content.strip()) < 15:
        ext_tag = extension.lstrip(".").lower() or "file"
        return {
            "summary": f"Uploaded {ext_tag.upper()} document named '{filename}'.",
            "tags": list(filter(None, [ext_tag, "document", "upload", clean_name.lower().split()[0] if clean_name else ""]))[:4],
            "provider": "offline_heuristic"
        }

    # Extract words
    words = re.findall(r'[a-zA-Z]{3,}', content.lower())
    meaningful_words = [w for w in words if w not in STOPWORDS and not w.isdigit()]
    
    # Compute frequency
    freq = collections.Counter(meaningful_words)
    top_words = [word for word, _ in freq.most_common(5)]
    
    # Add extension tag
    ext_clean = extension.lstrip(".").lower()
    tags = [ext_clean] if ext_clean else []
    for w in top_words:
        if w not in tags and len(tags) < 4:
            tags.append(w)
    if "document" not in tags and len(tags) < 3:
        tags.append("document")

    # Generate summary from first sentence or key lines
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
    first_sentence = lines[0] if lines else f"{clean_name} document containing {len(words)} words."
    if len(first_sentence) > 160:
        first_sentence = first_sentence[:157] + "..."

    return {
        "summary": f"Document covering {', '.join(top_words[:3]) or clean_name}: {first_sentence}",
        "tags": tags[:5],
        "provider": "offline_heuristic"
    }

def _heuristic_search(query: str, catalog: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Scores files against natural query using token matching and metadata."""
    q_tokens = set(re.findall(r'\w+', query.lower()))
    scored_files = []

    for f in catalog:
        score = 0
        name = f.get("original_name", "").lower()
        summary = f.get("summary", "").lower()
        tags = [t.lower() for t in f.get("tags", [])]
        date = f.get("uploaded_at", "")

        for token in q_tokens:
            if token in name:
                score += 5
            for tag in tags:
                if token in tag:
                    score += 4
            if token in summary:
                score += 2

        # Check for month / recent keywords
        if "recent" in q_tokens or "latest" in q_tokens or "month" in q_tokens:
            score += 1

        if score > 0:
            scored_files.append((score, f["id"]))

    scored_files.sort(reverse=True, key=lambda x: x[0])
    matched_ids = [fid for score, fid in scored_files[:10]]

    return {
        "matched_file_ids": matched_ids,
        "explanation": f"Matched {len(matched_ids)} files referencing key terms from '{query}'.",
        "provider": "offline_heuristic"
    }

def _heuristic_chat(prompt: str, filename: str, content: str, history: List[Dict[str, str]]) -> str:
    """Answers document inquiries offline by extracting matching sentences."""
    if not content or len(content.strip()) < 10:
        return f"This document ({filename}) has no extracted text content available to inspect."

    p_tokens = set(re.findall(r'\w+', prompt.lower())) - STOPWORDS
    if not p_tokens:
        p_tokens = set(re.findall(r'\w+', prompt.lower()))

    # Split into sentences or lines
    chunks = [c.strip() for c in re.split(r'[.\n]+', content) if len(c.strip()) > 15]
    
    scored_chunks = []
    for c in chunks:
        c_lower = c.lower()
        matches = sum(1 for t in p_tokens if t in c_lower)
        if matches > 0:
            scored_chunks.append((matches, c))

    scored_chunks.sort(reverse=True, key=lambda x: x[0])

    if scored_chunks:
        best_matches = [c for _, c in scored_chunks[:3]]
        return f"Based on **{filename}**:\n\n> " + "\n\n> ".join(best_matches)
    else:
        return f"I reviewed **{filename}**, but could not find a direct reference answering '{prompt}'. Here is an excerpt from the document:\n\n> {chunks[0] if chunks else 'No text preview available.'}"

# --- Gemini API Caller ---

async def _call_gemini(system_instruction: str, user_content: str, json_mode: bool = False) -> Optional[str]:
    """Call Google Gemini generateContent endpoint via httpx."""
    if not config.GEMINI_API_KEY:
        return None

    model = config.GEMINI_MODEL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={config.GEMINI_API_KEY}"
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_instruction}\n\n{user_content}"}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024
        }
    }

    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        else:
            print(f"[Gemini API Error] {response.status_code}: {response.text}")
            return None

# --- Unified AI Interface ---

async def generate_file_tags_and_summary(filename: str, extension: str, content: str) -> Dict[str, Any]:
    """
    Analyzes document text and returns 3-5 tags and a 1-sentence summary.
    Uses Gemini if key is present; falls back to heuristic engine.
    """
    truncated_content = content[:8000] if content else ""
    
    # 1. Try Gemini
    if config.GEMINI_API_KEY:
        try:
            prompt = TAG_SUMMARY_PROMPT.format(
                filename=filename,
                extension=extension,
                content=truncated_content or "[No readable text content]"
            )
            raw = await _call_gemini(
                system_instruction="You are a cataloging AI that outputs strictly valid JSON.",
                user_content=prompt,
                json_mode=True
            )
            if raw:
                # Clean markdown backticks if any
                clean_raw = re.sub(r"^```json\s*", "", raw.strip())
                clean_raw = re.sub(r"```$", "", clean_raw.strip())
                parsed = json.loads(clean_raw)
                return {
                    "summary": parsed.get("summary", ""),
                    "tags": [t.strip().lower() for t in parsed.get("tags", []) if t.strip()][:5],
                    "provider": "gemini"
                }
        except Exception as e:
            print(f"[AI Service] Gemini call failed, falling back to heuristic: {e}")

    # 2. Offline Heuristic Fallback
    return _heuristic_tag_and_summary(filename, extension, content)

async def natural_language_search(query: str, catalog: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Natural-language search ("Ask" mode).
    Takes a query e.g. "budget spreadsheets from last month", passes file metadata
    to LLM, and returns matched file IDs + explanation.
    """
    # Prepare minimal catalog footprint for prompt
    catalog_summary = []
    for f in catalog:
        catalog_summary.append({
            "id": f["id"],
            "filename": f["original_name"],
            "tags": [t["name"] for t in f.get("tags", [])] if isinstance(f.get("tags"), list) and f.get("tags") and isinstance(f["tags"][0], dict) else f.get("tags", []),
            "summary": f.get("summary", ""),
            "uploaded_at": f.get("uploaded_at", "")
        })

    # 1. Try Gemini
    if config.GEMINI_API_KEY:
        try:
            prompt = SEARCH_ASK_PROMPT.format(
                query=query,
                catalog_json=json.dumps(catalog_summary, indent=2)
            )
            raw = await _call_gemini(
                system_instruction="You are an intelligent file retrieval engine that outputs strictly JSON.",
                user_content=prompt,
                json_mode=True
            )
            if raw:
                clean_raw = re.sub(r"^```json\s*", "", raw.strip())
                clean_raw = re.sub(r"```$", "", clean_raw.strip())
                parsed = json.loads(clean_raw)
                return {
                    "matched_file_ids": parsed.get("matched_file_ids", []),
                    "explanation": parsed.get("explanation", ""),
                    "provider": "gemini"
                }
        except Exception as e:
            print(f"[AI Service] Search Gemini call failed, falling back to heuristic: {e}")

    # 2. Heuristic Search Fallback
    # Normalize tags format for heuristic search
    normalized_catalog = []
    for c in catalog_summary:
        norm_item = dict(c)
        if isinstance(norm_item.get("tags"), list) and norm_item["tags"] and isinstance(norm_item["tags"][0], dict):
            norm_item["tags"] = [t["name"] for t in norm_item["tags"]]
        normalized_catalog.append(norm_item)

    return _heuristic_search(query, normalized_catalog)

async def chat_with_file(
    filename: str,
    content: str,
    user_prompt: str,
    history: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Answers a user question about a specific file, taking conversation history into account.
    """
    truncated_content = content[:15000] if content else "[No readable text in this file]"

    # 1. Try Gemini
    if config.GEMINI_API_KEY:
        try:
            # Build conversation context
            history_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-6:]])
            combined_prompt = f"Previous Conversation:\n{history_text}\n\nUser Question: {user_prompt}"
            
            system_instruction = CHAT_SYSTEM_PROMPT.format(
                filename=filename,
                content=truncated_content
            )
            
            reply = await _call_gemini(
                system_instruction=system_instruction,
                user_content=combined_prompt,
                json_mode=False
            )
            if reply:
                return {
                    "reply": reply.strip(),
                    "provider": "gemini"
                }
        except Exception as e:
            print(f"[AI Service] Chat Gemini call failed, falling back to heuristic: {e}")

    # 2. Heuristic Chat Fallback
    reply = _heuristic_chat(user_prompt, filename, content, history)
    return {
        "reply": reply,
        "provider": "offline_heuristic"
    }
