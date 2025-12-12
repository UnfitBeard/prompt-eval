# minimal_server.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))


app = FastAPI(
    title="Prompt Engineering Academy",
    description="Interactive learning platform",
    version="1.0.0"
)

# Simple CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "API is running", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy", "database": "not_connected", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting minimal server on http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
