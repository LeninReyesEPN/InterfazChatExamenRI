# Sistema RAG sobre arXiv Paper Abstracts

Examen final de Recuperación de Información (EPN-FIS). Chat que responde preguntas en lenguaje
natural sobre el corpus [arXiv Paper Abstracts](https://www.kaggle.com/datasets/spsayakpaul/arxiv-paper-abstracts),
usando búsqueda semántica y un LLM para generar respuestas con evidencias.

## Estructura

- `src/` — frontend (Next.js).
- `backend/` — API RAG (FastAPI, FAISS, Gemini). Se despliega por separado en Hugging Face Spaces.
- `examen_rag_arxiv.ipynb` — notebook del examen.
- `Guia del examen/` — enunciado.

## Correr en local

**Backend**

```bash
python3.11 -m venv backend/.venv && source backend/.venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # y agrega tu GEMINI_API_KEY
python -m uvicorn backend.main:app --reload --port 8000
```

**Frontend**

```bash
npm install
cp .env.local.example .env.local
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000).
