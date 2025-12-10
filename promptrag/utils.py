# utils.py (improved)
import re
import json
import time
from typing import Any, Dict, List, Optional

import logging
from logging.handlers import RotatingFileHandler
import os

LOG_FILE = os.environ.get("PROMPT_PIPELINE_LOG", "pipeline.log")

# ------------------
# Logger


def setup_logger():
    logger = logging.getLogger("prompt_pipeline")
    if logger.handlers:
        # already configured
        return logger

    logger.setLevel(logging.INFO)

    # File handler (rotating)
    fh = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=5)
    fh.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s — %(levelname)s — %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # avoid duplicate logs if root logger is configured elsewhere
    logger.propagate = False
    return logger


logger = setup_logger()


# -------------------
# Trace
class Trace:
    """
    Simple structured trace collector. Use trace.log(...) to append events.
    Finally call trace.export() to get a JSON-serializable object.
    """

    def __init__(self):
        self.start_ts = time.time()
        self.steps: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {
            "num_rag_chunks": 0,
            "num_rewrite_attempts": 0,
            "num_successful_json_parses": 0,
            "duration_ms": None,
        }

    def log(self, step: str, detail: Optional[Dict[str, Any]] = None):
        event = {
            "ts": time.time(),
            "step": step,
            "detail": detail or {}
        }
        self.steps.append(event)

    def incr(self, metric: str, amount: int = 1):
        self.metrics[metric] = self.metrics.get(metric, 0) + amount

    def set_metric(self, metric: str, value: Any):
        self.metrics[metric] = value

    def finish(self):
        self.metrics["duration_ms"] = int((time.time() - self.start_ts) * 1000)

    def export(self) -> Dict[str, Any]:
        self.finish()
        return {
            "start_ts": self.start_ts,
            "steps": self.steps,
            "metrics": self.metrics,
        }


# Regex: find the first fenced code block (``` or ```json or ```lang)
CODEBLOCK_RE = re.compile(
    r"```(?:\w+)?\s*([\s\S]*?)\s*```", flags=re.IGNORECASE)

# Simple HTML tag stripper (best-effort)
_HTML_TAG_RE = re.compile(r"<[^>]+>")

# Obvious API key pattern (OpenAI-like sk-...)
_API_KEY_RE = re.compile(r"sk-[A-Za-z0-9\-_]{8,}", flags=re.IGNORECASE)


def clean_text(s: Optional[str], max_len: Optional[int] = 20000) -> str:
    """
    Basic cleaning:
      - normalize newlines,
      - remove obvious API keys,
      - strip HTML tags,
      - collapse whitespace,
      - optionally truncate to max_len characters.
    """
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\r\n", "\n").replace("\r", "\n").strip()

    # redact obvious API keys
    s = _API_KEY_RE.sub("[REDACTED_KEY]", s)

    # remove HTML tags (best effort)
    s = _HTML_TAG_RE.sub(" ", s)

    # collapse runs of whitespace to single space/newline where appropriate
    # keep paragraphs by collapsing spaces but preserving single newlines
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)  # limit to double newline
    s = s.strip()

    # optional truncation to avoid extremely large payloads
    if max_len and len(s) > max_len:
        return s[:max_len].rsplit(" ", 1)[0] + " ... [TRUNCATED]"
    return s


def extract_json_inside_codeblock(s: Optional[str]) -> str:
    """
    If input contains a fenced code block, return inner content.
    Otherwise try to extract the first JSON object found anywhere in the text.
    If both fail, return the original trimmed string.
    """
    if not s:
        return ""

    text = str(s).strip()

    # 1) prefer fenced code block content
    m = CODEBLOCK_RE.search(text)
    if m:
        return m.group(1).strip()

    # 2) try to find the first JSON object using a simple brace-matching scan
    # This is safer than a plain regex for nested braces.
    start = None
    depth = 0
    for i, ch in enumerate(text):
        if ch == "{":
            if start is None:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    candidate = text[start: i + 1]
                    # quick sanity check: try to parse
                    try:
                        json.loads(candidate)
                        return candidate.strip()
                    except Exception:
                        # not valid JSON — continue searching
                        start = None
                        depth = 0
    # 3) fallback: return trimmed text
    return text


def strip_code_fences(s: Optional[str]) -> str:
    """
    Remove triple-backtick fences and leading language tags, but preserve inner code/text.
    Also remove surrounding leading/trailing blank lines.
    """
    if not s:
        return ""

    text = str(s)

    # Remove triple backtick fences and optional lang label on the opening fence.
    text = re.sub(r"^```[^\n]*\n", "", text)        # opening fence at start
    text = re.sub(r"\n```[^\n]*\s*$", "", text)     # closing fence at end
    # Remove any remaining inline fences
    text = text.replace("```", "")
    # collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: Optional[str], max_chars: int = 1000, overlap: int = 200) -> List[str]:
    """
    Chunk text into character-overlapping segments.
    Guarantees forward progress and avoids infinite loops.
    Returns list of chunks (none empty). Last chunk may be shorter.
    """
    if not text:
        return []
    s = text.strip()
    if len(s) <= max_chars:
        return [s]

    chunks: List[str] = []
    start = 0
    n = len(s)
    while start < n:
        end = start + max_chars
        if end >= n:
            chunk = s[start:n]
            if chunk:
                chunks.append(chunk.strip())
            break

        # prefer cutting at the last space inside the window to avoid half-words
        window = s[start:end]
        cut = window.rfind(" ")
        if cut > int(max_chars * 0.6):  # only cut if reasonable
            end = start + cut

        chunk = s[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # advance start
        next_start = end - overlap
        if next_start <= start:
            # fallback: make sure we always move forward at least by max_chars - overlap/2
            next_start = start + max(1, max_chars - overlap)
        start = next_start

    # optionally drop tiny final chunk by merging with prior if too small
    if len(chunks) >= 2 and len(chunks[-1]) < int(max_chars * 0.2):
        chunks[-2] = (chunks[-2] + "\n\n" + chunks[-1]).strip()
        chunks.pop()
    return chunks
