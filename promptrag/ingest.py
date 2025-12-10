# ingest_anthropic.py
import os
import json
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb import PersistentClient
from tqdm import tqdm

# Config (env overrides)
CHROMA_DIR = os.environ.get("CHROMA_DIR", "./vectorstore")
SRC_JSON = os.environ.get("ANTHROPIC_JSON", "anthropic_prompts_extracted.json")
EMBED_MODEL_NAME = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")
COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION", "anthropic")
MAX_CHARS = int(os.environ.get("CHUNK_MAX_CHARS", "1200"))
OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "200"))

# -------------------------
# small utils (inlined replacements for your previous utils)
# -------------------------


def clean_text(s: str) -> str:
    """Basic cleaning: remove HTML, excessive whitespace."""
    if not s:
        return ""
    s = re.sub(r"<script[\s\S]*?</script>", " ", s, flags=re.I)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def strip_code_fences(s: str) -> str:
    """Remove fenced code blocks and inline code fences."""
    if not s:
        return ""
    s = re.sub(r"```[\s\S]*?```", " ", s)       # fenced triple-backtick blocks
    s = re.sub(r"`{1,3}[\s\S]*?`{1,3}", " ", s)  # inline/backtick code
    return s


def chunk_text(text: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP):
    """Chunk by characters with overlap; avoid tiny chunks."""
    if text is None:
        return []
    t = text.strip()
    if len(t) <= max_chars:
        return [t]
    chunks = []
    start = 0
    while start < len(t):
        end = start + max_chars
        chunk = t[start:end]
        # try not to cut mid-word — roll back to last space inside chunk
        if end < len(t):
            rp = chunk.rfind(" ")
            if rp > 100:  # if there's a reasonable space, cut there
                chunk = chunk[:rp]
                end = start + rp
        chunks.append(chunk.strip())
        start = max(end - overlap, end)
    # filter very short
    return [c for c in chunks if len(c) > 50]

# -------------------------
# assemble instruction from Anthropic entry
# -------------------------


def assemble_instruction(entry: dict) -> (str, bool):
    """
    Return (assembled_text, was_trimmed_flag)
    Prefers explicit 'system' + 'user'; falls back to raw_blocks label scanning.
    """
    system = (entry.get("system") or "").strip()
    user = (entry.get("user") or "").strip()
    was_trimmed = False

    raw_blocks = entry.get("raw_blocks", []) or []
    if not (system or user) and raw_blocks:
        # gather first system/user blocks if available
        for b in raw_blocks:
            lbl = (b.get("label") or "").lower()
            txt = (b.get("text") or "").strip()
            if "system" in lbl and not system:
                system = txt
            elif "user" in lbl and not user:
                user = txt

    system = clean_text(strip_code_fences(system))
    user = clean_text(strip_code_fences(user))

    combined = ""
    if system:
        combined += f"SYSTEM: {system}. "
    if user:
        combined += f"USER: {user}"

    # fallback: if still empty, try to concatenate all textual raw_blocks (but avoid huge examples)
    if not combined.strip() and raw_blocks:
        pieces = []
        for b in raw_blocks:
            lbl = (b.get("label") or "").lower()
            txt = clean_text(strip_code_fences(b.get("text", "")))
            # skip blocks that look like huge example outputs (heuristic)
            if len(txt) > 10000:
                txt = txt[:2400] + " ... [TRIMMED]"
                was_trimmed = True
            pieces.append(f"{lbl.upper()}: {txt}")
        combined = " ".join(pieces)

    # final safety: if extremely long, trim but mark was_trimmed
    if len(combined) > 4000:
        combined = combined[:4000].rsplit(" ", 1)[0] + " ... [TRIMMED]"
        was_trimmed = True

    return combined.strip(), was_trimmed

# -------------------------
# main ingest
# -------------------------


def main():
    src = Path(SRC_JSON)
    if not src.exists():
        raise SystemExit(f"Source file not found: {SRC_JSON}")

    print("Loading Anthropic JSON:", SRC_JSON)
    raw = json.load(src.open(encoding="utf-8"))
    print("Total entries:", len(raw))

    # init embedder & chroma persistent client
    embedder = SentenceTransformer(EMBED_MODEL_NAME)
    client = PersistentClient(path=CHROMA_DIR)
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        col = client.get_collection(COLLECTION_NAME)
    else:
        col = client.create_collection(COLLECTION_NAME)

    print(f"Using Chroma collection '{COLLECTION_NAME}' at {CHROMA_DIR}")
    total_chunks = 0

    for idx, entry in enumerate(tqdm(raw, desc="ingest entries")):
        parent_row = entry.get("id") or entry.get("source_url") or idx
        assembled, was_trimmed = assemble_instruction(entry)
        if not assembled:
            continue

        # make a short prompt preview for metadata (first 400 chars)
        preview = assembled[:400]

        # chunk the assembled instruction
        chunks = chunk_text(assembled, max_chars=MAX_CHARS, overlap=OVERLAP)
        if not chunks:
            continue

        for chunk_i, chunk in enumerate(chunks):
            item_id = f"{parent_row}__{chunk_i}"
            emb = embedder.encode(chunk).tolist()
            meta = {
                "parent_row": parent_row,
                "source_url": entry.get("source_url"),
                "page_title": entry.get("page_title"),
                "chunk_index": chunk_i,
                "prompt_preview": preview,
                "was_trimmed": was_trimmed
            }
            # add to chroma
            try:
                col.add(
                    ids=[item_id],
                    documents=[chunk],
                    metadatas=[meta],
                    embeddings=[emb]
                )
                total_chunks += 1
            except Exception as e:
                print("Failed to add chunk:", item_id, "error:", e)

        # progress logging similar to old script
        if (idx + 1) % 100 == 0:
            print("Processed entries:", idx + 1,
                  "Total chunks upserted:", total_chunks)

    print("Ingestion complete. Total chunks upserted:", total_chunks)
    print("DB persisted to", CHROMA_DIR)


if __name__ == "__main__":
    main()
