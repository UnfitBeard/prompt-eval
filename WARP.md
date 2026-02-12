# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project overview

This repo is a full-stack "prompt evaluation" platform plus an additional Python RAG/evaluator service. At the top level there are four main projects:

- `promptEval/` – Angular 19 SPA frontend used by end users and admins.
- `backend/` – Node.js + Express REST API (auth, templates, prompt evaluation orchestration) talking to MongoDB Atlas.
- `AI_model/` – Python scoring model (scikit-learn Ridge regressor) and artifacts that score prompts 0–10.
- `promptrag/` – Python FastAPI service that provides a RAG-based prompt evaluator and a "Prompt Engineering Academy" API (courses, lessons, user progress, etc.). This subproject has its own `promptrag/WARP.md` with more detail.

The root `ReadME.md` explains how the Angular app calls the Node backend, which in turn calls the Python scoring service. The `promptrag/` service is an additional, more advanced evaluator + learning API that can be run independently.

---

## Common commands

### Frontend: Angular app (`promptEval/`)

All frontend work happens under `promptEval/`.

**Install dependencies**

```bash
cd promptEval
npm install
```

**Run dev server** (http://localhost:4200/)

```bash
cd promptEval
npm start        # wraps `ng serve`
```

**Build for production**

```bash
cd promptEval
npm run build    # wraps `ng build`, outputs to dist/
```

**Run unit tests (Karma + Jasmine)**

```bash
cd promptEval
npm test         # wraps `ng test`
```

**Focus on a single/spec file**

Angular tests are standard Karma/Jasmine specs under `promptEval/src/`. To focus on a single spec, either:
- Temporarily use `fdescribe` / `fit` in the target spec file, or
- Run `ng test` with `--include` pointing at a specific spec:

```bash
cd promptEval
npx ng test --include src/app/path/to/component.component.spec.ts
```

### Backend: Node.js + Express API (`backend/`)

The backend exposes REST APIs for auth, template CRUD, and prompt evaluation, backed by MongoDB Atlas.

**Install dependencies**

```bash
cd backend
npm install
```

**Run dev server** (http://localhost:10000/)

```bash
cd backend
npm run dev
```

**Required environment (`backend/.env`)**

```env
PORT=10000
MONGO_URI=<your_mongodb_atlas_uri>
JWT_SECRET=<your_secret_key>
```

If the API is not reachable from the Angular app, verify CORS configuration and that your IP is whitelisted in MongoDB Atlas.

### Python scoring model (`AI_model/`)

This project contains the Ridge regressor model and inference script used to numerically score prompts.

**Create venv and install deps**

```bash
cd AI_model
python3 -m venv my_venv
source my_venv/bin/activate
pip install -r requirements.txt
```

**Run the scoring script / local server**

The core entry point for inference is:

```bash
cd AI_model
source my_venv/bin/activate
python scoring_artifacts/infer_ridge.py
```

The exact serving mode depends on how `infer_ridge.py` is implemented (script vs Flask/FastAPI). The typical pattern is that the backend calls this service on something like `http://localhost:5000/evaluate`.

**Optional: Dockerize the model**

```bash
cd AI_model
docker build -t prompt-eval-model -f DOCKERFILE .
docker run -p 5000:5000 prompt-eval-model
```

### RAG + Academy FastAPI service (`promptrag/`)

`promptrag/` is a separate FastAPI application that:

- Offers RAG-style prompt evaluation endpoints (scoring + suggestions + history).
- Exposes a tutor/chatbot API backed by a small prompt-engineering corpus.
- Implements a "Prompt Engineering Academy" (users, courses, lessons, progress) backed by MongoDB.

For day-to-day work in this subproject, prefer the more detailed `promptrag/WARP.md`. Key commands are summarized here for convenience.

**Create venv and install deps**

```bash
cd promptrag
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Prepare dataset and environment**

```bash
cd promptrag
# CSV in repo root (promptrag/) with columns: repo,file,prompt,code_context
export OPENAI_API_KEY="sk-..."          # or GEMINI_API_KEY for Gemini via langchain_google_genai
export CHROMA_DIR="./chroma_db"        # optional, default varies
export EMBED_MODEL="all-MiniLM-L6-v2"  # optional
```

**Build / refresh evaluator vector store (Chroma)**

```bash
cd promptrag
source .venv/bin/activate
python ingest.py
```

This creates/updates a persistent Chroma DB in `CHROMA_DIR` (for the prompt evaluation RAG pipeline).

**Run FastAPI server**

Main app entrypoint is `server.py`:

```bash
cd promptrag
source .venv/bin/activate
uvicorn server:app --reload --port 8000
```

Common endpoints include:

- `POST /evaluate` – score a prompt (RAG + scoring model).
- `POST /improve` – suggest better wording for a low-scoring prompt.
- `GET /history` – prompt evaluation history from SQLite.
- `POST /batch_evaluate` – batch scoring.
- `GET /health` – health check.
- `POST /api/v1/chat/ask` – RAG chatbot/tutor.

**Quick smoke test (no full test suite)**

There is no dedicated test runner configured in `promptrag/`. For a fast import/syntax check you can compile all Python modules:

```bash
cd promptrag
python -m compileall -q .
```

---

## High-level architecture

### Angular frontend (`promptEval/`)

- Generated with Angular CLI 19.2.
- Primary code lives under `promptEval/src/app/`:
  - `Components/` – views for login, dashboards, template management, etc.
  - `Guards/` – route guards enforcing authentication.
  - `Services/` – HTTP services that talk to the backend API and (where relevant) AI services.
- Top-level configuration lives in `angular.json` and `package.json`.
- The app calls the backend at `http://localhost:10000/api/v1/...` for auth, templates, and prompt evaluation.

### Node.js backend (`backend/`)

The backend is an Express REST API with a conventional layering:

- `src/Controllers/`
  - `Auth/` – login, registration, and session management.
  - `Prompts/` – template and evaluation-related endpoints.
- `src/Models/` – Mongoose schemas for users, templates, and any supporting collections.
- `src/Routes/` – Express route definitions wiring URLs to controllers.
- `src/Utils/` – shared helpers such as JWT utilities and possibly logging/middleware.
- `server.ts` – main entrypoint; configures Express, CORS, MongoDB connection, and mounts routes.

The backend is responsible for:

1. Authenticating users and issuing JWTs.
2. CRUD around prompt templates and metadata.
3. Forwarding evaluation requests to the Python scoring service (and returning its JSON scores to the frontend).

### Python scoring model (`AI_model/`)

- `scoring_artifacts/infer_ridge.py` – loads the trained Ridge regressor and exposes an inference entrypoint.
- `scoring_artifacts/regressor.joblib` – serialized model.
- `scoring_artifacts/meta.json` – metadata that guides how features and outputs are interpreted.
- `requirements.txt` – Python dependencies for the model service.

The model computes a composite score (0–10) based on aspects such as clarity, context, relevance, specificity, and creativity, and returns structured JSON consumed by the backend.

### FastAPI RAG + Academy service (`promptrag/`)

Within `promptrag/` there is a more complex Python backend (see `promptrag/WARP.md` for details). At a high level:

- **FastAPI app composition**
  - `server.py` creates the FastAPI `app` and includes routers via `app.include_router(...)`.
- **Prompt evaluator subsystem**
  - `scorer.py` loads scoring artifacts from `./scoring_artifacts/` (expects `meta.json` + `*.joblib`).
  - Uses a persistent Chroma client at `./vectorstore` for RAG over prompt examples.
  - Query embeddings are created with `sentence_transformers` (default `all-MiniLM-L6-v2`).
  - LLM calls go through Gemini via `langchain_google_genai`, controlled by prompts in `prompts.py`.
  - Prompt evaluation history is written to a SQLite DB (`prompt_history.db`).
- **Chatbot / tutor subsystem**
  - Routers under `services/prompt_evaluator_endpoint.py` expose `/api/v1/chat/*`.
  - `services/chatbot_service.py` manages RAG over a small set of prompt-engineering URLs, storing:
    - a Chroma DB in `./chroma_chatbot_db`.
    - conversations in `./chatbot_conversations.json`.
- **"Prompt Engineering Academy" subsystem**
  - API routers in `api/routers/*.py` (auth, courses, lessons, progress).
  - Service layer in `services/*_service.py` encapsulates MongoDB access.
  - Pydantic domain models live in `models/` (e.g. `models/user.py`, `models/course.py`).
  - Request/response schemas live in `schemas/`.
  - `core/database.py` manages a singleton MongoDB client using `MONGO_DB_URI` and exposes named collections (`users`, `courses`, `lessons`, `user_progress`, `lesson_attempts`, ...).
  - Auth and JWT helpers live in `core/security.py`.
  - `config.py` and/or Pydantic settings models parse env vars like `MONGO_DB_URI`, `JWT_SECRET_KEY`, `SECRET_KEY`, and `GEMINI_API_KEY`.

---

## Notes and gotchas

- The legacy `ReadME.md` and some scripts reference `OPENAI_API_KEY`, but the RAG evaluator in `promptrag/` currently expects `GEMINI_API_KEY` (using `langchain_google_genai`). Be explicit about which provider you are using when wiring up environment variables.
- `promptrag/docker-compose.yml` (if present) may be stale – it references `main:app`, `mongo-init.js`, and `build: .`, but there is no `Dockerfile`, `main.py`, or `mongo-init.js` in the Python project.
- In `promptrag/` there is both a root-level `utils.py` and a `utils/` package. Be explicit about imports to avoid grabbing the wrong helpers.
- For project-specific details inside `promptrag/` (API contracts, DB collections, etc.), consult `promptrag/WARP.md`, which has more granular guidance for that subproject.
