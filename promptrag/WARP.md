# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common commands

### Environment setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run the FastAPI server
This repo’s main app entrypoint is `server.py`.

```bash
# Requires env (at minimum): GEMINI_API_KEY
uvicorn server:app --reload --port 8000
```

Useful endpoints when the server is running:
- `POST /evaluate` (prompt scoring + suggestions)
- `GET /history` (SQLite-backed prompt evaluation history)
- `POST /batch_evaluate`
- `GET /health`
- `POST /api/v1/chat/ask` (RAG chatbot)

Example request:
```bash
curl -sS -X POST http://localhost:8000/evaluate \
  -H 'content-type: application/json' \
  -d '{"prompt":"Write a short poem about AI","k":3,"improve_if_low":true}'
```

### Build / refresh the evaluator vector store (Chroma)
`ingest.py` creates/updates a persistent Chroma DB (default `./vectorstore`) from a JSON dataset.

```bash
python ingest.py
```

Common ingest environment overrides (all optional):
- `CHROMA_DIR` (default: `./vectorstore`)
- `ANTHROPIC_JSON` (default: `anthropic_prompts_extracted.json`)
- `EMBED_MODEL` (default: `all-MiniLM-L6-v2`)
- `CHROMA_COLLECTION` (default: `anthropic`)

### Smoke-test server (minimal app)
`server_test.py` is a standalone minimal FastAPI app with `/` and `/health`.

```bash
python server_test.py
```

### Lint / tests
There is no repo-configured lint or test runner (no `pyproject.toml`, `pytest.ini`, etc.).

If you need a fast “does it import” check:
```bash
python -m compileall -q .
```

## High-level architecture

### Two subsystems share one FastAPI process
The repository currently mixes:
1. **Prompt evaluator API** (RAG + scoring)
2. **“Prompt Engineering Academy” API** (users/courses/lessons/progress + auth)

They are wired together in `server.py` via `app.include_router(...)`.

### Prompt evaluator flow
- Entry point: `server.py`
- Scoring model: `scorer.py` loads artifacts from `./scoring_artifacts/` (expects `meta.json` + `*.joblib` files).
- Vector search:
  - Persistent Chroma client at `./vectorstore`.
  - Query embeddings created by `sentence_transformers` (`all-MiniLM-L6-v2` by default).
  - Data is typically populated by `ingest.py`.
- LLM calls:
  - Uses Gemini via `langchain_google_genai` (`GEMINI_API_KEY` env var).
  - Suggestions/improvements are driven by prompts in `prompts.py`.
- Persistence:
  - Writes prompt evaluation history to SQLite: `prompt_history.db` (table `prompt_evaluations`).

### Chatbot (RAG tutor) flow
- Router: `services/prompt_evaluator_endpoint.py` exposes `/api/v1/chat/*`.
- Implementation: `services/chatbot_service.py`
  - Maintains its own Chroma persistence dir: `./chroma_chatbot_db`.
  - Scrapes a small set of prompt-engineering URLs and chunks/indexes content.
  - Stores conversations in `./chatbot_conversations.json`.

### “Prompt Engineering Academy” (Mongo-backed) flow
- Routers: `api/routers/*.py` (auth/courses/lessons/progress)
- Services: `services/*_service.py` contain most MongoDB reads/writes.
- Data model split:
  - `models/`: Pydantic domain models (e.g. `models/user.py`, `models/course.py`).
  - `schemas/`: API request/response schemas.
- DB connection:
  - `core/database.py` manages a singleton `mongodb` client using `MONGO_DB_URI`.
  - Collections used include: `users`, `courses`, `lessons`, `user_progress`, `lesson_attempts`.
- Auth:
  - JWT helpers in `core/security.py`.
  - Settings/env parsing in `config.py` (expects `MONGO_DB_URI`, `JWT_SECRET_KEY`, `SECRET_KEY`, `GEMINI_API_KEY`).

### Common “where is X implemented?” pointers
- FastAPI app composition + prompt evaluator endpoints: `server.py`
- Academy auth endpoints: `api/routers/auth.py` + `services/user_service.py`
- Courses and enrollment: `api/routers/courses.py` + `services/course_service.py`
- Lessons and attempts: `api/routers/lessons.py` + `services/lesson_service.py`
- Progress summary/leaderboard: `api/routers/progress.py` + `services/progress_service.py`

## Repo gotchas (useful when debugging)
- `READme.md` references `OPENAI_API_KEY`, but the current server runtime expects `GEMINI_API_KEY` (Gemini via `langchain_google_genai`).
- `docker-compose.yml` appears stale: it references `main:app`, `mongo-init.js`, and `build: .`, but there is no `Dockerfile`, `main.py`, or `mongo-init.js` in the repo.
- `server.py` imports `api.routers.chat` and `api.routers.prompt_evaluator`, but only `auth.py`, `courses.py`, `lessons.py`, and `progress.py` exist under `api/routers/`.
- There is both a root-level `utils.py` (used heavily by `server.py`) and a `utils/` package (used more by the “academy” code). Be explicit about which one you mean when importing/editing.
