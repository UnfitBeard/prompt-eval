# utils.py
import re
from typing import List

CODEBLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", flags=re.IGNORECASE)

def clean_text(s: str) -> str:
    """Basic cleaning: normalize whitespace, scrub obvious API keys, remove trailing/leading spaces."""
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\r\n", "\n").strip()
    # scrub obvious OpenAI keys like sk-...
    s = re.sub(r"sk-[A-Za-z0-9\-_]{8,}", "[REDACTED_KEY]", s)
    return s

def extract_json_inside_codeblock(s: str) -> str:
    """If s contains a ``` or ```json block, return the inner content; else return s trimmed."""
    if not s:
        return ""
    m = CODEBLOCK_RE.search(s)
    if m:
        return m.group(1).strip()
    return s.strip()

def strip_code_fences(s: str) -> str:
    """Remove code fences but keep inner code/text."""
    if not s:
        return ""
    return re.sub(r"```(?:[a-zA-Z0-9_-]*\n)?", "", s).replace("```", "").strip()

def chunk_text(text: str, max_chars: int = 1000, overlap: int = 200) -> List[str]:
    """Chunk text into overlapping segments (character-based). Good for code_context."""
    if not text:
        return []
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end].strip()
        chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
        if end >= len(text):
            break
    return chunks
