import os
from dotenv import load_dotenv

load_dotenv()  # carga backend/.env en desarrollo local; en HF Spaces/EC2 las variables ya vienen del entorno

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from backend.corpus import download_and_prepare_corpus
from backend.vector_db import build_index, load_index
from backend.rag import generate_rag_response
from backend.evaluation import run_evaluation

app = FastAPI(
    title="arXiv RAG API",
    description="Sistema de Recuperación de Información con RAG sobre arXiv Paper Abstracts",
)

# Comma-separated list of allowed origins, e.g. "https://mi-front.vercel.app,http://localhost:3000".
# Defaults to "*" for local development.
_cors_origins = os.environ.get("CORS_ORIGINS", "*")
allow_origins = ["*"] if _cors_origins.strip() == "*" else [o.strip() for o in _cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    query: str
    history: Optional[List[MessageItem]] = []


@app.on_event("startup")
def startup_event():
    print("Iniciando servicio y preparando datos...")
    try:
        download_and_prepare_corpus()
        load_index()  # reutiliza faiss.index si ya existe; solo lo reconstruye si falta
    except Exception as e:
        print(f"Error durante la inicialización de inicio: {e}")


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
        response = generate_rag_response(request.query, history_dicts)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/evaluate")
async def evaluate_endpoint():
    try:
        metrics = run_evaluation()
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/index")
async def index_endpoint():
    try:
        build_index()
        return {"status": "success", "message": "Base vectorial FAISS reindexada con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
