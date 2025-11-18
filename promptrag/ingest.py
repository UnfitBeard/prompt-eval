# ingest.py
import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chromadb import PersistentClient
from utils import clean_text, strip_code_fences, chunk_text

CHROMA_DIR = os.environ.get("CHROMA_DIR", "./vectorstore")
PROMPTSET_CSV = os.environ.get("PROMPTSET_CSV", "promptset.csv")
EMBED_MODEL_NAME = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")


def main():
    print("Loading dataset:", PROMPTSET_CSV)
    df = pd.read_csv(PROMPTSET_CSV)
    print("Rows:", len(df))

    # initialize embedder and chroma
    embedder = SentenceTransformer(EMBED_MODEL_NAME)
    client = PersistentClient(path=CHROMA_DIR)
    if "promptset" in [c.name for c in client.list_collections()]:
        col = client.get_collection("promptset")
    else:
        col = client.create_collection("promptset")

    # ingest
    for idx, row in df.iterrows():
        repo = row.get("repo", "")
        file = row.get("file", "")
        prompt = clean_text(row.get("prompt", ""))
        code_context = clean_text(row.get("code_context", ""))
        # Choose what to index: prompt + short code context
        combined = prompt + "\n\nCONTEXT:\n" + strip_code_fences(code_context)
        # chunk if too large
        chunks = chunk_text(combined, max_chars=1200, overlap=200)
        for chunk_i, chunk in enumerate(chunks):
            item_id = f"{idx}__{chunk_i}"
            emb = embedder.encode(chunk).tolist()
            meta = {
                "repo": repo,
                "file": file,
                "parent_row": int(idx),
                "chunk_index": chunk_i,
                "prompt_preview": prompt[:400]
            }
            col.add(
                ids=[item_id],
                documents=[chunk],
                metadatas=[meta],
                embeddings=[emb]
            )
        if (idx + 1) % 100 == 0:
            print("Ingested", idx + 1)
    print("Ingestion complete. DB persisted to", CHROMA_DIR)


if __name__ == "__main__":
    main()
