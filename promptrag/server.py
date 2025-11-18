# server.py
from fastapi import Body
from scorer import load_scorer, score_prompt, apply_vagueness_penalty, TARGETS
import os
import json
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chromadb import PersistentClient
from prompts import EVAL_SYSTEM_PROMPT, IMPROVE_SYSTEM_PROMPT, build_eval_user_message, build_improve_user_message
from utils import extract_json_inside_codeblock, clean_text
from langchain.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tqdm import tqdm
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# scorer
ART_DIR = "./scoring_artifacts"
EMBEDDER_SCORER, REG, SCALER, TARGETS_SCORER, VERSION_SCORER = load_scorer(
    ART_DIR)
_ = EMBEDDER_SCORER.encode(
    ["warmup"], normalize_embeddings=True, show_progress_bar=False)

# scorer

CHROMA_DIR = os.environ.get("CHROMA_DIR", "./chroma_db")
EMBED_MODEL_NAME = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY is None:
    raise RuntimeError("Set GEMINI_API_KEY in env")

app = FastAPI(title="PromptSet RAG Service")

# CORS config
origins = [
    "http://localhost:4200",  # Angular dev server
    "http://localhost:3000",  # React dev server, optional
    "*",  # allow all origins (use carefully in production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # list of allowed origins
    allow_credentials=True,      # allow cookies/auth headers
    allow_methods=["*"],         # allow all HTTP methods
    allow_headers=["*"],         # allow all headers
)

# -----------------------------------

embedder = SentenceTransformer(EMBED_MODEL_NAME)
client = PersistentClient(path="./vectorstore")
col = client.get_collection("promptset")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    google_api_key=GEMINI_API_KEY,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)


class PromptIn(BaseModel):
    prompt: str
    k: int = 5


def _retrieve_similar(prompt: str, k: int = 5):
    emb = embedder.encode(clean_text(prompt)).tolist()
    res = col.query(query_embeddings=[emb], n_results=k)
    docs = []
    # res fields: 'ids', 'documents', 'metadatas', 'distances' depending on chroma
    doc_texts = res.get("documents", [[]])[0]
    metadatas = res.get("metadatas", [[]])[0]
    for d_text, meta in zip(doc_texts, metadatas):
        docs.append({"content": d_text, "metadata": meta})
    return docs


def _parse_json_response(raw: str):
    # try to extract json inside codeblock
    candidate = extract_json_inside_codeblock(raw).strip()
    try:
        return json.loads(candidate)
    except Exception:
        # try to find first { ... } block
        m = None
        import re
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        # fallback: try to convert simple key:value pairs
        return {"raw": raw}


@app.post("/evaluate")
async def evaluate(p: PromptIn):
    if not p.prompt or p.prompt.strip() == "":
        raise HTTPException(status_code=400, detail="Missing prompt")
    # retrieve
    docs = _retrieve_similar(p.prompt, k=p.k)
    sys_msg = SystemMessage(content=EVAL_SYSTEM_PROMPT)
    user_msg = HumanMessage(content=build_eval_user_message(p.prompt, docs))
    try:
        resp = llm.invoke([sys_msg, user_msg])
        raw = resp.content
        parsed = _parse_json_response(raw)
        return {"raw": raw, "parsed": parsed, "retrieved_count": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/improve")
async def improve(p: PromptIn):
    if not p.prompt or p.prompt.strip() == "":
        raise HTTPException(status_code=400, detail="Missing prompt")
    docs = _retrieve_similar(p.prompt, k=p.k)
    sys_msg = SystemMessage(content=IMPROVE_SYSTEM_PROMPT)
    user_msg = HumanMessage(content=build_improve_user_message(p.prompt, docs))
    try:
        resp = llm.invoke([sys_msg, user_msg])
        raw = resp.content
        parsed = _parse_json_response(raw)
        return {"raw": raw, "parsed": parsed, "retrieved_count": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PromptScoreIn(BaseModel):
    prompt: str


@app.post("/score")
async def score_endpoint(p: PromptScoreIn):
    base_scores = score_prompt(
        p.prompt, EMBEDDER_SCORER, REG, SCALER, TARGETS_SCORER)
    final_scores = apply_vagueness_penalty(base_scores, p.prompt)
    return {
        "prompt": p.prompt,
        "base_scores": base_scores,
        "final_scores": final_scores,
        "scorer_version": VERSION_SCORER
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# -------------------------------
# Unified endpoint
# -------------------------------


SYSTEM_PROMPT = """
You are a strict evaluator for programming prompts.

Return ONLY JSON in a single fenced code block like:

```json
{
  "clarity": 7.5,
  "context": 7.0,
  "relevance": 9.0,
  "specificity": 7.5,
  "creativity": 6.0,
  "suggestions": [
    { "text": "Add input/output examples." },
    { "text": "Specify language/runtime and constraints." }
  ],
  "rewriteVersions": [
    {
      "title": "Enhanced Version",
      "content": "...",
      "improvements": [{ "text": "..." }]
    },
    {
      "title": "Alternative Version",
      "content": "...",
      "improvements": [{ "text": "..." }]
    },
    {
      "title": "Minimalist Version",
      "content": "...",
      "improvements": [{ "text": "..." }]
    }
  ]
}
Scoring scale: 1–10 (decimals allowed).
"""


def build_eval_user_message(user_prompt: str, retrieved: List[dict]) -> str:
    """
    retrieved: list of dicts {"content": ..., "metadata": {...}}
    """
    examples_text = ""
    for i, doc in enumerate(retrieved):
        meta = doc.get("metadata", {})
        examples_text += (
            f"{i+1}) repo: {meta.get('repo')}, file: {meta.get('file')}\n"
            f"PROMPT_PREVIEW: {meta.get('prompt_preview')}\n"
            f"CONTENT_SNIPPET: {doc.get('content')[:300]}\n\n"
        )

    return f"""
PROMPT TO EVALUATE:
\"\"\"{user_prompt}\"\"\"

Similar prompt examples:
{examples_text}
"""


# **2️⃣ Integrate into the unified endpoint**


@app.post("/process_prompt")
async def process_prompt(p: PromptIn):
    if not p.prompt or p.prompt.strip() == "":
        raise HTTPException(status_code=400, detail="Missing prompt")

    # 1️⃣ Score prompt
    base_scores = score_prompt(
        p.prompt, EMBEDDER_SCORER, REG, SCALER, TARGETS_SCORER
    )
    final_scores = apply_vagueness_penalty(base_scores, p.prompt)

    # 2️⃣ Retrieve top-k similar prompts
    retrieved_docs = _retrieve_similar(p.prompt, k=p.k)

    # 3️⃣ LLM evaluation using strict JSON template
    sys_msg = SystemMessage(content=SYSTEM_PROMPT)
    user_msg = HumanMessage(
        content=build_eval_user_message(p.prompt, retrieved_docs)
    )
    resp = llm.invoke([sys_msg, user_msg])

    # 4️⃣ Parse JSON inside code block
    parsed_llm = _parse_json_response(resp.content)

    # 5️⃣ Return unified response
    return {
        "prompt": p.prompt,
        "scores": {
            "base_scores": base_scores,
            "final_scores": final_scores
        },
        "top_rag_prompts": retrieved_docs,
        "llm_evaluation": parsed_llm,
    }
