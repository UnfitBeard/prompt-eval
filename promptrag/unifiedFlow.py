from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from scorer import load_scorer, score_prompt, apply_vagueness_penalty, TARGETS
from sentence_transformers import SentenceTransformer
from langchain.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from utils import clean_text, extract_json_inside_codeblock
from chromadb import PersistentClient
import os
import json

# -------------------------------
# Init scorer
# -------------------------------
ART_DIR = "./scoring_artifacts"
EMBED_SCORER, REG, SCALER, TARGETS_SCORER, VERSION_SCORER = load_scorer(
    ART_DIR)
_ = EMBED_SCORER.encode(
    ["warmup"], normalize_embeddings=True, show_progress_bar=False)

# -------------------------------
# Init RAG & LLM
# -------------------------------
CHROMA_DIR = os.environ.get("CHROMA_DIR", "./vectorstore")
EMBED_MODEL_NAME = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY is None:
    raise RuntimeError("Set GEMINI_API_KEY in env")

embedder = SentenceTransformer(EMBED_MODEL_NAME)
client = PersistentClient(path=CHROMA_DIR)
col = client.get_collection("promptset")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GEMINI_API_KEY,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# -------------------------------
# FastAPI
# -------------------------------
app = FastAPI(title="Unified Scoring + RAG Service")


class PromptIn(BaseModel):
    prompt: str
    k: int = 3  # top k RAG suggestions

# -------------------------------
# Helpers
# -------------------------------


def _retrieve_similar(prompt: str, k: int = 3):
    emb = embedder.encode(clean_text(prompt)).tolist()
    res = col.query(query_embeddings=[emb], n_results=k)
    docs = []
    doc_texts = res.get("documents", [[]])[0]
    metadatas = res.get("metadatas", [[]])[0]
    for d_text, meta in zip(doc_texts, metadatas):
        docs.append({"content": d_text, "metadata": meta})
    return docs


def _parse_json_response(raw: str):
    candidate = extract_json_inside_codeblock(raw).strip()
    try:
        return json.loads(candidate)
    except Exception:
        return {"raw": raw}
