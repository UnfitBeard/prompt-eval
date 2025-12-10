# server.py (patched to include tracing + logging)
import uuid
from utils import Trace, logger
import time
from tqdm import tqdm
from chromadb.config import Settings
from chromadb import PersistentClient

import chromadb
from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import HumanMessage, SystemMessage
from utils import extract_json_inside_codeblock, clean_text
from prompts import EVAL_SYSTEM_PROMPT, IMPROVE_SYSTEM_PROMPT, build_eval_user_message, build_improve_user_message
from scorer import load_scorer, score_prompt, apply_vagueness_penalty, TARGETS
import os
import json
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime

TRACE_STORE = {}  # { trace_id: { "created": ts, "items": [...] } }

# NEW imports

load_dotenv()

# scoring imports (unchanged)

# embedding + vectorstore

# progress indicator (optional)

# -------------------------------
# Load env / config
# -------------------------------
ART_DIR = "./scoring_artifacts"
EMBEDDER_SCORER, REG, SCALER, TARGETS_SCORER, VERSION_SCORER = load_scorer(
    ART_DIR)
# warmup the scorer embedder (keeps previous behavior)
_ = EMBEDDER_SCORER.encode(
    ["warmup"], normalize_embeddings=True, show_progress_bar=False)

# or whatever your Chroma impl string is
CHROMA_IMPL = os.environ.get("CHROMA_IMPL", "duckdb+parquet")
CHROMA_PERSIST_DIR = os.environ.get("CHROMA_DIR", "./chroma_db")
CHROMA_COLLECTION = os.environ.get(
    "CHROMA_COLLECTION", "anthropic")  # new collection name default
EMBED_MODEL_NAME = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY is None:
    raise RuntimeError("Set GEMINI_API_KEY in env")

# -------------------------------
# FastAPI app + CORS
# -------------------------------
app = FastAPI(title="PromptSet RAG Service (chroma)")

origins = [
    "http://localhost:4200",
    "http://localhost:3000",
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Embedding model & Chroma client
# -------------------------------
embedder = SentenceTransformer(EMBED_MODEL_NAME)

# create chroma client with configured backend (duckdb+parquet typical)
client = PersistentClient(path="./vectorstore")

# ensure collection exists (create if missing)
existing = [c.name for c in client.list_collections()]
if CHROMA_COLLECTION in existing:
    col = client.get_collection(CHROMA_COLLECTION)
else:
    # create collection if not present (safe default creation)
    col = client.create_collection(CHROMA_COLLECTION)

# -------------------------------
# LLM (unchanged)
# -------------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GEMINI_API_KEY,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# -------------------------------
# Pydantic models
# -------------------------------


class PromptIn(BaseModel):
    prompt: str
    k: int = 5


# -------------------------------
# Helper: retrieve top-k similar docs from Chroma
# -------------------------------
def _retrieve_similar(prompt: str, k: int = 2) -> List[dict]:
    """
    Returns list of dicts: { "content": <doc text>, "metadata": <meta dict>, "distance": <optional> }
    Works with chromadb.Client(Settings(...)) query return format.
    """
    clean = clean_text(prompt)
    q_emb = embedder.encode(clean).tolist()

    # query chroma collection
    try:
        res = col.query(query_embeddings=[q_emb], n_results=k)
    except Exception as e:
        # fallback: return empty list rather than crash the whole API
        logger.exception("Chroma query failed")
        return []

    # Res is typically like: {'ids': [[...]], 'documents': [[...]], 'metadatas': [[...]], 'distances': [[...]]}
    docs_out = []
    doc_texts = res.get("documents", [[]])[0]
    metadatas = res.get("metadatas", [[]])[0]
    distances = res.get("distances", [[]])[0] if res.get(
        "distances") else [None] * len(doc_texts)

    for d_text, meta, dist in zip(doc_texts, metadatas, distances):
        # Normalize metadata keys (older ingest used 'repo'/'file' but new ingest uses 'parent_row','prompt_preview',...)
        normalized_meta = {
            "parent_row": meta.get("parent_row"),
            "source_url": meta.get("source_url"),
            "page_title": meta.get("page_title"),
            "prompt_preview": meta.get("prompt_preview") or meta.get("preview") or None,
            "chunk_index": meta.get("chunk_index"),
            "was_trimmed": meta.get("was_trimmed", False),
            "is_code_like": meta.get("is_code_like", False),
            # keep original metadata for backwards compatibility
            **{k: v for k, v in meta.items() if k not in {"parent_row", "source_url", "page_title", "prompt_preview", "chunk_index", "was_trimmed", "is_code_like"}}
        }
        docs_out.append(
            {"content": d_text, "metadata": normalized_meta, "distance": dist})
    return docs_out


# -------------------------------
# JSON parsing utility (unchanged)
# -------------------------------
def _parse_json_response(raw: str):
    candidate = extract_json_inside_codeblock(raw).strip()
    try:
        return json.loads(candidate)
    except Exception:
        import re
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        return {"raw": raw}


# -------------------------------
# Endpoints (evaluate / improve / score / process_prompt)
# -------------------------------
@app.post("/evaluate")
async def evaluate(p: PromptIn):
    if not p.prompt or p.prompt.strip() == "":
        raise HTTPException(status_code=400, detail="Missing prompt")
    docs = _retrieve_similar(p.prompt, k=p.k)
    sys_msg = SystemMessage(content=EVAL_SYSTEM_PROMPT)
    user_msg = HumanMessage(content=build_eval_user_message(p.prompt, docs))
    try:
        resp = llm.invoke([sys_msg, user_msg])
        raw = resp.content
        parsed = _parse_json_response(raw)
        return {"raw": raw, "parsed": parsed, "retrieved_count": len(docs), "retrieved": docs}
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
        return {"raw": raw, "parsed": parsed, "retrieved_count": len(docs), "retrieved": docs}
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


# Unified endpoint
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
    examples_text = ""
    for i, doc in enumerate(retrieved):
        meta = doc.get("metadata", {})
        examples_text += (
            f"{i+1}) parent_row: {meta.get('parent_row')}, source_url: {meta.get('source_url')}\n"
            f"PROMPT_PREVIEW: {meta.get('prompt_preview')}\n"
            f"WAS_TRIMMED: {meta.get('was_trimmed')}\n"
            f"CONTENT_SNIPPET: {doc.get('content')[:400]}\n\n"
        )

    return f"""
PROMPT TO EVALUATE:
\"\"\"{user_prompt}\"\"\"

Similar prompt examples:
{examples_text}
"""


@app.post("/process_prompt_v2")
async def process_prompt(p: PromptIn):
    if not p.prompt or p.prompt.strip() == "":
        raise HTTPException(status_code=400, detail="Missing prompt")
    # 1) Score prompt
    base_scores = score_prompt(p.prompt, EMBEDDER_SCORER,
                               REG, SCALER, TARGETS_SCORER)
    final_scores = apply_vagueness_penalty(base_scores, p.prompt)

    # 2) Retrieve top-k similar prompts
    retrieved_docs = _retrieve_similar(p.prompt, k=p.k)

    # 3) LLM evaluation using strict JSON template
    sys_msg = SystemMessage(content=SYSTEM_PROMPT)
    user_msg = HumanMessage(
        content=build_eval_user_message(p.prompt, retrieved_docs))
    resp = llm.invoke([sys_msg, user_msg])

    # 4) Parse JSON inside code block
    parsed_llm = _parse_json_response(resp.content)

    # 5) Return unified response
    return {
        "prompt": p.prompt,
        "scores": {
            "base_scores": base_scores,
            "final_scores": final_scores
        },
        "top_rag_prompts": retrieved_docs,
        "llm_evaluation": parsed_llm,
    }


@app.post("/process_prompt")
async def process_prompt(p: PromptIn):
    if not p.prompt or p.prompt.strip() == "":
        raise HTTPException(status_code=400, detail="Missing prompt")

    trace = Trace()
    trace_id = str(uuid.uuid4())
    trace.log("received_prompt", {"prompt_len": len(p.prompt)})

    logger.info("process_prompt start; prompt_len=%d", len(p.prompt))

    start_time = time.time()

    # Configuration
    # original + at most one auto-fix (increase if you want more retries)
    max_iters = 2
    # require this much avg-score improvement to accept a rewrite
    score_improvement_threshold = 0.25
    # if avg final score below this, attempt auto-fix (scale 0-10)
    low_score_threshold = 5.5

    # keep trace of attempts: dict(prompt, base_scores, final_scores, llm_evaluation, retrieved_count)
    attempts = []
    best_result = None
    best_overall = -1.0

    current_prompt = p.prompt

    # Record initial retrieval (before any loop) for visibility
    initial_retrieved = _retrieve_similar(current_prompt, k=p.k)
    trace.log("initial_rag", {"count": len(initial_retrieved)})
    trace.set_metric("num_rag_chunks", len(initial_retrieved))
    logger.info("initial RAG results: %d", len(initial_retrieved))

    raw_eval = None
    parsed_llm = None
    retrieved_docs = initial_retrieved

    first_iteration_llm = None

    for iteration in range(max_iters):
        iter_label = f"iter_{iteration}"
        logger.info("[%s] scoring current prompt (len=%d)",
                    iter_label, len(current_prompt))
        trace.log("scoring_start", {
                  "iteration": iteration, "prompt_len": len(current_prompt)})

        # ---------- 1) Score prompt ----------
        base_scores = score_prompt(
            current_prompt, EMBEDDER_SCORER, REG, SCALER, TARGETS_SCORER)
        final_scores = apply_vagueness_penalty(base_scores, current_prompt)
        trace.log("scoring_result", {
                  "iteration": iteration, "base_scores": base_scores, "final_scores": final_scores})
        logger.info("[%s] base_scores=%s final_scores=%s",
                    iter_label, base_scores, final_scores)

        # compute simple overall average of final_scores
        overall = float(
            sum([
                final_scores.get("clarity", 0),
                final_scores.get("context", 0),
                final_scores.get("relevance", 0),
                final_scores.get("specificity", 0),
                final_scores.get("creativity", 0),
            ]) / 5.0
        )
        trace.log("scoring_overall", {
                  "iteration": iteration, "overall": overall})

        # ---------- 2) Retrieve top-k similar prompts ----------
        retrieved_docs = _retrieve_similar(current_prompt, k=p.k)
        trace.log("rag_retrieved", {
                  "iteration": iteration, "count": len(retrieved_docs)})
        trace.incr("num_rag_chunks", len(retrieved_docs))
        logger.info("[%s] RAG retrieved %d docs",
                    iter_label, len(retrieved_docs))

        # ---------- 3) LLM evaluation using strict JSON template ----------
        sys_msg = SystemMessage(content=SYSTEM_PROMPT)
        user_msg = HumanMessage(content=build_eval_user_message(
            current_prompt, retrieved_docs))
        try:
            resp = llm.invoke([sys_msg, user_msg])
            raw_eval = resp.content
            parsed_llm = _parse_json_response(raw_eval)
            trace.log("llm_evaluation", {
                      "iteration": iteration, "raw": raw_eval[:2000]})
            # if parsed is dict assume successful parse
            if isinstance(parsed_llm, dict):
                trace.incr("num_successful_json_parses", 1)
            logger.info("[%s] LLM evaluation completed (parsed=%s)",
                        iter_label, isinstance(parsed_llm, dict))
        except Exception as e:
            logger.exception("[%s] LLM eval error", iter_label)
            raise HTTPException(status_code=500, detail=f"LLM eval error: {e}")

        attempt = {
            "prompt": current_prompt,
            "base_scores": base_scores,
            "final_scores": final_scores,
            "overall_score": overall,
            "top_rag_prompts": retrieved_docs,
            "llm_raw": raw_eval,
            "llm_parsed": parsed_llm,
            "iteration": iteration,
        }

        if iteration == 0:
            first_iteration_llm = parsed_llm
        attempts.append(attempt)
        trace.log("attempt_recorded", {
                  "iteration": iteration, "overall": overall})

        # update best
        if overall > best_overall:
            best_overall = overall
            best_result = attempt
            trace.log("best_updated", {
                      "iteration": iteration, "best_overall": best_overall})

        # Decide whether to attempt auto-fix:
        needs_fix = False

        # 1) low score trigger
        if overall < low_score_threshold:
            needs_fix = True
            trace.log("needs_fix_reason", {
                      "iteration": iteration, "reason": "low_score", "overall": overall})

        # 2) LLM returned an explicit check result / missing fields
        if isinstance(parsed_llm, dict):
            if parsed_llm.get("missing") or parsed_llm.get("failed_items"):
                needs_fix = True
                trace.log("needs_fix_reason", {
                          "iteration": iteration, "reason": "llm_missing_or_failed", "payload_keys": list(parsed_llm.keys())})
            dims = ["clarity", "context", "relevance",
                    "specificity", "creativity"]
            try:
                dim_vals = [float(parsed_llm.get(d, 0)) for d in dims]
                avg_dim = sum(dim_vals)/len(dim_vals)
                if avg_dim < low_score_threshold:
                    needs_fix = True
                    trace.log("needs_fix_reason", {
                              "iteration": iteration, "reason": "llm_low_dims", "avg_dim": avg_dim})
            except Exception:
                pass

        if not needs_fix:
            trace.log("no_fix_needed", {
                      "iteration": iteration, "overall": overall})
            logger.info(
                "[%s] no fix needed (overall=%.2f) — stopping", iter_label, overall)
            break

        if iteration + 1 >= max_iters:
            trace.log("max_iters_reached", {"iteration": iteration})
            logger.info(
                "[%s] max_iters reached — not attempting improve", iter_label)
            break

        # ---------- 4) Ask the LLM to generate an improved prompt (the "improve" flow) ----------
        trace.log("improve_request", {"iteration": iteration})
        try:
            sys_msg_imp = SystemMessage(content=IMPROVE_SYSTEM_PROMPT)
            user_msg_imp = HumanMessage(
                content=build_improve_user_message(current_prompt, retrieved_docs))
            resp_imp = llm.invoke([sys_msg_imp, user_msg_imp])
            raw_imp = resp_imp.content
            parsed_imp = _parse_json_response(raw_imp)
            trace.log("improve_response", {
                      "iteration": iteration, "raw": raw_imp[:2000]})
            logger.info("[%s] improve flow responded (parsed=%s)",
                        iter_label, isinstance(parsed_imp, dict))
        except Exception as e:
            logger.exception("[%s] improve LLM error", iter_label)
            # If improve call fails, stop retrying and return what we have
            attempts.append({
                "auto_fix_generated": True,
                "improve_raw": None,
                "improve_parsed": None,
                "chosen_candidate": None,
                "reason": "improve_call_failed",
                "iteration": iteration + 0.5,
            })
            break

        # Determine candidate rewritten prompt(s).
        candidate_prompts = []
        if isinstance(parsed_imp, dict):
            if parsed_imp.get("rewriteVersions"):
                for v in parsed_imp["rewriteVersions"]:
                    if isinstance(v, dict) and v.get("content"):
                        candidate_prompts.append(v["content"])
            if parsed_imp.get("rewrite"):
                candidate_prompts.append(parsed_imp.get("rewrite"))
            if parsed_imp.get("improved_prompt"):
                candidate_prompts.append(parsed_imp.get("improved_prompt"))

        if not candidate_prompts:
            candidate_prompts.append(raw_imp)

        trace.log("candidates_extracted", {
                  "iteration": iteration, "num_candidates": len(candidate_prompts)})
        trace.incr("num_rewrite_attempts", 1)

        # ---------- 5) Score candidates and pick best if it improves overall ----------
        best_candidate = None
        best_candidate_overall = overall
        best_candidate_data = None

        for cand_i, cand in enumerate(candidate_prompts):
            cand_text = cand.strip()
            cand_base = score_prompt(
                cand_text, EMBEDDER_SCORER, REG, SCALER, TARGETS_SCORER)
            cand_final = apply_vagueness_penalty(cand_base, cand_text)
            cand_overall = float(
                sum([
                    cand_final.get("clarity", 0),
                    cand_final.get("context", 0),
                    cand_final.get("relevance", 0),
                    cand_final.get("specificity", 0),
                    cand_final.get("creativity", 0),
                ]) / 5.0
            )
            trace.log("candidate_scored", {
                      "iteration": iteration, "candidate_index": cand_i, "cand_overall": cand_overall})
            logger.info("[%s] candidate %d overall=%.3f",
                        iter_label, cand_i, cand_overall)

            if cand_overall > best_candidate_overall + score_improvement_threshold:
                best_candidate_overall = cand_overall
                best_candidate = cand_text
                best_candidate_data = {
                    "base_scores": cand_base,
                    "final_scores": cand_final,
                    "overall_score": cand_overall,
                }

        # If a candidate passes the improvement test, adopt it and iterate again
        if best_candidate:
            trace.log("candidate_chosen", {
                      "iteration": iteration, "new_overall": best_candidate_overall})
            current_prompt = best_candidate
            # also persist the improve attempt in trace
            attempts.append({
                "auto_fix_generated": True,
                "improve_raw": raw_imp,
                "improve_parsed": parsed_imp,
                "chosen_candidate": best_candidate,
                "chosen_candidate_data": best_candidate_data,
                "iteration": iteration + 0.5,
            })
            logger.info("[%s] adopted candidate (new overall=%.3f)",
                        iter_label, best_candidate_overall)
            continue
        else:
            # No candidate passed improvement threshold → stop retrying
            attempts.append({
                "auto_fix_generated": True,
                "improve_raw": raw_imp,
                "improve_parsed": parsed_imp,
                "chosen_candidate": None,
                "reason": "no_candidate_improved_enough",
                "iteration": iteration + 0.5,
            })
            trace.log("no_candidate_improved", {"iteration": iteration})
            logger.info("[%s] no candidate improved enough", iter_label)
            break

    # End loop — finalize trace and return best_result and full attempts trace
    trace.log("process_complete", {"best_overall": best_overall})
    trace.set_metric("final_overall", best_overall)
    trace.set_metric("num_attempts", len(attempts))
    trace.finish()

    logger.info("process_prompt complete; duration_ms=%s best_overall=%.3f attempts=%d",
                trace.metrics.get("duration_ms"), best_overall, len(attempts))

    # save full trace including attempts
    TRACE_STORE[trace_id] = trace.export()

    first_attempt = attempts[0]  # first iteration
    best_attempt = best_result   # best rewritten prompt

    response = {
        "scores": {
            "base_scores": first_attempt["base_scores"],
            "final_scores": first_attempt["final_scores"],
            "final": {
                "base_scores": best_attempt["base_scores"],
                "final_scores": best_attempt["final_scores"],
            },
        },
        "top_rag_prompts": retrieved_docs,
        "llm_evaluation": first_iteration_llm,
        "trace_id": trace_id
    }
    return response


# health


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/trace/{trace_id}")
async def get_trace(trace_id: str):
    trace = TRACE_STORE.get(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


@app.get("/why_iterate/{trace_id}")
async def why_iterate(trace_id: str):
    trace_data = TRACE_STORE.get(trace_id)
    if not trace_data:
        raise HTTPException(status_code=404, detail="Trace not found")

    iterations_summary = {}

    for step in trace_data.get("steps", []):
        detail = step.get("detail", {})
        iteration = detail.get("iteration")
        if iteration is None:
            continue

        # Initialize iteration entry if not exists
        if iteration not in iterations_summary:
            iterations_summary[iteration] = {
                "iteration": iteration,
                "overall_score": None,
                "base_scores": None,
                "final_scores": None,
                "needs_fix_reason": None,
                "llm_missing_fields": [],
                "candidate_adopted": None,
                "improve_suggestions": None
            }

        iter_entry = iterations_summary[iteration]

        # Fill in fields if present
        for key in ["overall", "base_scores", "final_scores", "reason", "chosen_candidate"]:
            if key in detail and detail[key] is not None:
                if key == "overall":
                    iter_entry["overall_score"] = detail[key]
                elif key == "reason":
                    iter_entry["needs_fix_reason"] = detail[key]
                elif key == "chosen_candidate":
                    iter_entry["candidate_adopted"] = detail[key]
                else:
                    iter_entry[key] = detail[key]

        # Check LLM parsed suggestions
        raw = detail.get("raw")
        if raw:
            try:
                parsed = json.loads(raw.strip("```json\n```"))
                if isinstance(parsed, dict):
                    iter_entry["improve_suggestions"] = parsed.get(
                        "suggestions")
                    for k in ["missing", "failed_items"]:
                        if k in parsed:
                            iter_entry["llm_missing_fields"].append(k)
            except Exception:
                pass

    # Return a list of iterations sorted by number
    return {"trace_id": trace_id, "iterations": list(iterations_summary.values())}


@app.get("/debug/trace_store")
async def debug_trace_store():
    return TRACE_STORE
