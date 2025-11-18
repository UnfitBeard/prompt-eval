1. Create a python venv and install requirements:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Put your promptset csv in the project root: `promptset.csv`

   The CSV should contain at least: repo,file,prompt,code_context

3. Set environment variables:
   export OPENAI_API_KEY="sk-..."
   (optionally) export CHROMA_DIR="./chroma_db"
   (optionally) export EMBED_MODEL="all-MiniLM-L6-v2"

4. Ingest dataset:
   python ingest.py

   This will create a local Chroma DB in CHROMA_DIR.

5. Run server:
   uvicorn server:app --reload --port 8000

6. API endpoints:
   POST http://localhost:8000/evaluate
   body: {"prompt": "Write a short poem about AI", "k": 5}

   POST http://localhost:8000/improve
   body: {"prompt": "write poem ai", "k": 5}
