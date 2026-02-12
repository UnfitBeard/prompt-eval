# server.py - REDESIGNED FOR SPEED
from api.routers import (
    auth,
    courses,
    lessons,
    progress,
    user_dashboard,
    admin,
    prompt_scores,
    templates,
)
from services.prompt_evaluator_endpoint import chatbot_router, init_chatbot_service
from langchain.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from prompts import EVAL_SYSTEM_PROMPT, IMPROVE_SYSTEM_PROMPT, build_improve_user_message
from scorer import load_scorer, score_prompt, apply_vagueness_penalty, TARGETS
from utils import Trace, logger, clean_text, extract_json_inside_codeblock
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import sqlite3
from core.database import mongodb
from contextlib import asynccontextmanager
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks
import numpy as np
import uuid
import time
import json
import os
import re
from typing import List, Optional, Dict
from datetime import datetime

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


load_dotenv()


# ======================
# CONFIGURATION
# ======================
ART_DIR = "./scoring_artifacts"
EMBEDDER_SCORER, REG, SCALER, TARGETS_SCORER, VERSION_SCORER = load_scorer(
    ART_DIR)

# Warmup
_ = EMBEDDER_SCORER.encode(
    ["warmup"], normalize_embeddings=True, show_progress_bar=False)

CHROMA_PERSIST_DIR = "./vectorstore"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"  # Fast, lightweight
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Thresholds
SCORE_THRESHOLD = 6.0  # Below this, we suggest improvements
MIN_IMPROVEMENT_DELTA = 1.0  # Minimum score improvement to show alternative

# ======================
# DATABASE SETUP (SQLite for history)
# ======================


def init_db():
    conn = sqlite3.connect('prompt_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prompt_evaluations
                 (id TEXT PRIMARY KEY,
                  prompt TEXT,
                  timestamp DATETIME,
                  base_scores TEXT,
                  final_scores TEXT,
                  overall_score REAL,
                  suggestions TEXT,
                  improved_prompt TEXT,
                  improved_scores TEXT,
                  trace_id TEXT)''')
    conn.commit()
    conn.close()


init_db()

# ======================
# FASTAPI APP
# ======================


# Globals that are expensive to initialize (and can fail depending on ML stack)
rag_embedder = None
chroma_client = None
rag_collection = None
llm_fast = None
llm_smart = None
executor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_embedder, chroma_client, rag_collection, llm_fast, llm_smart, executor

    # Startup
    await mongodb.connect()

    # Start chatbot init in the background (non-fatal if it fails)
    try:
        init_chatbot_service()
    except Exception as e:
        logger.error(f"Chatbot init failed during startup: {e}")

    # Thread pool for parallel operations
    executor = ThreadPoolExecutor(max_workers=4)

    # Initialize RAG embedder + vector store (CPU-only). If it fails, keep service running.
    try:
        rag_embedder = SentenceTransformer(
            EMBED_MODEL_NAME,
            device="cpu",
            model_kwargs={"low_cpu_mem_usage": False}
        )

        chroma_client = PersistentClient(path=CHROMA_PERSIST_DIR)
        try:
            rag_collection = chroma_client.get_collection("prompts")
        except Exception:
            rag_collection = chroma_client.create_collection("prompts")

    except Exception as e:
        logger.error(f"RAG embedder init failed: {e}")
        rag_embedder = None
        chroma_client = None
        rag_collection = None

    # Initialize LLM clients (requires GEMINI_API_KEY)
    if GEMINI_API_KEY:
        llm_fast = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0,
            google_api_key=GEMINI_API_KEY,
            max_tokens=500,
            timeout=10,
        )

        llm_smart = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0,
            google_api_key=GEMINI_API_KEY,
            max_tokens=1000,
            timeout=30,
        )
    else:
        logger.warning(
            "GEMINI_API_KEY not set; prompt evaluation endpoints that require LLM will fail")

    print("🚀 Application startup complete")
    yield

    # Shutdown
    try:
        if executor:
            executor.shutdown(wait=True)
    finally:
        await mongodb.disconnect()
        print("👋 Application shutdown complete")


app = FastAPI(title="Fast Prompt Evaluator", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "https://prompt-eval-wz8i.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chatbot_router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(courses.router, prefix="/api/v1")
app.include_router(lessons.router, prefix="/api/v1")
app.include_router(progress.router, prefix="/api/v1")
# New: user-centric dashboard endpoints (progress, modules, badges, certificates)
app.include_router(user_dashboard.router, prefix="/api/v1")
# Admin endpoints
app.include_router(admin.router, prefix="/api/v1")
# Prompt scores endpoints
app.include_router(prompt_scores.router, prefix="/api/v1")
# Templates endpoints
app.include_router(templates.router, prefix="/api/v1")


# ======================
# SERVICES INITIALIZATION
# ======================
# Initialized in lifespan() to avoid import-time crashes.

# ======================
# MODELS
# ======================


class PromptIn(BaseModel):
    prompt: str
    k: int = 3  # Reduced from 5 for speed
    improve_if_low: bool = True


class EvaluationResult(BaseModel):
    prompt: str
    scores: Dict
    overall_score: float
    needs_improvement: bool
    suggestions: List[str]
    similar_prompts: List[Dict]
    improved_version: Optional[Dict] = None
    trace_id: str
    processing_time_ms: float

# ======================
# CORE LOGIC
# ======================


def save_to_history(eval_result: dict):
    """Save evaluation to SQLite for user history"""
    try:
        conn = sqlite3.connect('prompt_history.db')
        c = conn.cursor()
        c.execute('''INSERT INTO prompt_evaluations 
                     (id, prompt, timestamp, base_scores, final_scores, overall_score, 
                      suggestions, improved_prompt, improved_scores, trace_id)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (str(uuid.uuid4()),
                   eval_result['prompt'],
                   datetime.now(),
                   json.dumps(eval_result['scores']['base_scores']),
                   json.dumps(eval_result['scores']['final_scores']),
                   eval_result['overall_score'],
                   json.dumps(eval_result.get('suggestions', [])),
                   eval_result.get('improved_version', {}).get('content', ''),
                   json.dumps(eval_result.get(
                       'improved_version', {}).get('scores', {})),
                   eval_result.get('trace_id', '')))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to save to history: {e}")


async def score_prompt_async(prompt: str):
    """Score prompt in thread pool"""
    global executor
    if executor is None:
        executor = ThreadPoolExecutor(max_workers=4)

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        score_prompt,
        prompt,
        EMBEDDER_SCORER,
        REG,
        SCALER,
        TARGETS_SCORER,
    )


async def retrieve_similar_async(prompt: str, k: int):
    """Retrieve similar prompts in parallel"""
    def _retrieve():
        # If RAG isn't initialized (e.g. CPU embedding load failed), degrade gracefully.
        if rag_embedder is None or rag_collection is None:
            return []

        clean = clean_text(prompt)
        if not clean:
            return []

        q_emb = rag_embedder.encode(clean).tolist()
        results = rag_collection.query(
            query_embeddings=[q_emb],
            n_results=min(k, 10),
            include=["documents", "metadatas", "distances"]
        )

        similar = []
        docs = results.get('documents', [[]])[0]
        metas = results.get('metadatas', [[]])[0]
        dists = results.get('distances', [[]])[0]

        for doc, meta, dist in zip(docs, metas, dists):
            similar.append({
                "content": doc[:300],  # Truncate for speed
                "metadata": meta,
                "similarity": float(1 - dist) if dist is not None else None,
                "source": meta.get('source_url', 'unknown')
            })
        return similar

    global executor
    if executor is None:
        executor = ThreadPoolExecutor(max_workers=4)

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _retrieve)


async def generate_suggestions_fast(prompt: str, scores: Dict, similar_prompts: List):
    """Fast LLM call for suggestions only"""
    if llm_fast is None:
        # No LLM available; caller will fall back to heuristic suggestions.
        return []

    # Prepare context from similar prompts
    context = "\n".join([
        f"Example {i+1}: {p['content'][:200]}..."
        for i, p in enumerate(similar_prompts[:2])  # Use only top 2
    ])

    low_dimensions = [
        dim for dim, score in scores.items()
        if score < SCORE_THRESHOLD
    ]

    system_msg = SystemMessage(content="""You are a prompt optimization assistant. 
Return ONLY a JSON array of 1-3 specific, actionable suggestions to improve the prompt.
Format: ["suggestion 1", "suggestion 2", "suggestion 3"]""")

    user_msg = HumanMessage(content=f"""Prompt: {prompt}

Current scores (1-10):
{json.dumps(scores, indent=2)}

Low dimensions: {', '.join(low_dimensions) if low_dimensions else 'None'}

Similar high-quality prompts:
{context}

Provide 1-3 specific suggestions:""")

    try:
        resp = await asyncio.wait_for(
            llm_fast.ainvoke([system_msg, user_msg]),
            timeout=5.0
        )

        # Parse suggestions
        content = resp.content.strip()
        if content.startswith('[') and content.endswith(']'):
            return json.loads(content)
        elif content.startswith('```json'):
            return json.loads(extract_json_inside_codeblock(content))
        else:
            # Fallback: generate based on low dimensions
            return [f"Improve {dim}: Add more specific details" for dim in low_dimensions[:3]]

    except Exception as e:
        logger.error(f"Fast suggestions failed: {e}")
        return []


async def generate_improved_version(prompt: str, suggestions: List[str], similar_prompts: List):
    """Generate improved prompt (only if really needed)"""
    if llm_smart is None:
        return None

    if not suggestions:
        return None

    # Build context from best similar prompts
    context_examples = "\n\n".join([
        f"High-quality example {i+1}:\n{p['content']}"
        for i, p in enumerate(similar_prompts[:3])
    ])

    system_msg = SystemMessage(content=IMPROVE_SYSTEM_PROMPT)
    user_msg = HumanMessage(content=f"""Original prompt (needs improvement):
{prompt}

Specific issues to fix:
{chr(10).join(f"- {s}" for s in suggestions)}

High-quality reference prompts:
{context_examples}

Please provide ONE improved version that addresses the issues while maintaining the original intent.""")

    try:
        resp = await asyncio.wait_for(
            llm_smart.ainvoke([system_msg, user_msg]),
            timeout=15.0
        )

        # Parse improved prompt
        content = resp.content
        parsed = json.loads(extract_json_inside_codeblock(content))

        if isinstance(parsed, dict) and 'improved_prompt' in parsed:
            return {
                "content": parsed['improved_prompt'],
                "explanation": parsed.get('explanation', ''),
                "changes": suggestions
            }
        else:
            return {"content": content, "explanation": "AI-generated improvement"}

    except Exception as e:
        logger.error(f"Improvement generation failed: {e}")
        return None

# ======================
# MAIN ENDPOINT - OPTIMIZED
# ======================


@app.post("/evaluate", response_model=EvaluationResult)
async def evaluate_prompt(p: PromptIn, background_tasks: BackgroundTasks):
    """Fast, single-pass evaluation with intelligent suggestions"""
    start_time = time.time()
    trace_id = str(uuid.uuid4())
    trace = Trace()

    logger.info(f"Evaluating prompt (length: {len(p.prompt)})")
    trace.log("start", {"prompt_length": len(p.prompt)})

    try:
        # STEP 1: Score the prompt (fast - 100-300ms)
        trace.log("scoring_start")
        base_scores = await score_prompt_async(p.prompt)
        final_scores = apply_vagueness_penalty(base_scores, p.prompt)

        # Calculate overall score
        overall = np.mean(list(final_scores.values()))
        trace.log("scoring_complete", {
            "base_scores": base_scores,
            "final_scores": final_scores,
            "overall": overall
        })

        # NEW: Override penalty for substantial prompts
        words = re.findall(r"[a-z']+", p.prompt.lower())
        word_count = len(words)
        temp_overall = np.mean(list(final_scores.values()))

        if temp_overall <= 2.5 and word_count > 15:
            logger.info(f"Overriding vagueness penalty for substantial prompt ({word_count} words)")
            final_scores = {k: round(val, 1) for k, val in base_scores.items()}
            trace.log("penalty_override", {"reason": "substantial_prompt", "word_count": word_count})

        overall = np.mean(list(final_scores.values()))

        # STEP 2: Retrieve similar prompts IN PARALLEL with scoring
        trace.log("retrieval_start")
        similar_future = retrieve_similar_async(p.prompt, p.k)

        # Wait for both
        similar_prompts = await similar_future
        trace.log("retrieval_complete", {"count": len(similar_prompts)})

        # STEP 3: Check if improvement is needed
        needs_improvement = overall < SCORE_THRESHOLD and p.improve_if_low
        suggestions = []
        improved_version = None

        if needs_improvement or not needs_improvement:
            # STEP 4: Generate quick suggestions (fast)
            trace.log("suggestions_start")
            suggestions = await generate_suggestions_fast(p.prompt, final_scores, similar_prompts)
            trace.log("suggestions_complete", {"count": len(suggestions)})

            # STEP 5: Generate improved version if suggestions exist
            if suggestions and overall < (SCORE_THRESHOLD - 1.0) or not needs_improvement:
                trace.log("improvement_generation_start")
                improved_version = await generate_improved_version(p.prompt, suggestions, similar_prompts)
                trace.log("improvement_generation_complete")

        # STEP 6: Prepare response
        processing_time = (time.time() - start_time) * 1000

        result = {
            "prompt": p.prompt,
            "scores": {
                "base_scores": base_scores,
                "final_scores": final_scores
            },
            "overall_score": round(overall, 2),
            "needs_improvement": needs_improvement,
            "suggestions": suggestions,
            "similar_prompts": similar_prompts[:3],  # Return top 3 only
            "improved_version": improved_version,
            "trace_id": trace_id,
            "processing_time_ms": round(processing_time, 2)
        }

        # Save to history in background
        background_tasks.add_task(save_to_history, result)

        # Export trace
        trace.finish()

        logger.info(
            f"Evaluation complete in {processing_time:.0f}ms, overall: {overall:.1f}")

        return result

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        trace.log("error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

# ======================
# ADDITIONAL ENDPOINTS
# ======================


@app.get("/history")
async def get_history(limit: int = 20):
    """Get user's evaluation history"""
    try:
        conn = sqlite3.connect('prompt_history.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''SELECT * FROM prompt_evaluations 
                     ORDER BY timestamp DESC LIMIT ?''', (limit,))
        rows = c.fetchall()
        conn.close()

        return [
            {**dict(row),
             "base_scores": json.loads(row["base_scores"]),
             "final_scores": json.loads(row["final_scores"])}
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch_evaluate")
async def batch_evaluate(prompts: List[str], background_tasks: BackgroundTasks):
    """Evaluate multiple prompts efficiently"""
    results = []
    for prompt in prompts:
        result = await evaluate_prompt(
            PromptIn(prompt=prompt, k=2, improve_if_low=False),
            background_tasks
        )
        results.append(result)
    return {"results": results}


# Health endpoint for entire service
@app.get("/health")
async def health():
    """Overall service health check"""
    return {
        "status": "healthy",
        "services": {
            "prompt_evaluator": "active",
            "chatbot": "active"
        },
        "version": "1.0.0"
    }

# ======================
# CLEANUP ON SHUTDOWN
# ======================


@app.on_event("shutdown")
async def shutdown_event():
    # Kept for backwards compatibility, but lifespan() is the primary shutdown hook now.
    try:
        if executor:
            executor.shutdown(wait=True)
    except Exception:
        pass
    logger.info("Executor shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
