# Sistema RAG sobre arXiv Paper Abstracts

Examen final de Recuperación de Información (EPN-FIS). Chat que responde preguntas en lenguaje
natural sobre el corpus [arXiv Paper Abstracts](https://www.kaggle.com/datasets/spsayakpaul/arxiv-paper-abstracts),
usando búsqueda semántica y un LLM para generar respuestas con evidencias.

## Entrega del examen

- **Chat desplegado**: https://main.d1ngrhzkw2klti.amplifyapp.com/
- **API del backend**: https://steering-assembled-talks-tissue.trycloudflare.com (EC2 + Cloudflare Tunnel)
- **Notebook del examen** (requerimientos A–I, con evidencias, evaluación y esta misma URL):
  [`examen_rag_arxiv.ipynb`](./examen_rag_arxiv.ipynb)
- **Enunciado**: [`Guia del examen/examen2bim.pdf`](./Guia%20del%20examen/examen2bim.pdf)

## Estructura

- `src/` — frontend (Next.js), desplegado en **AWS Amplify**.
- `backend/` — API RAG (FastAPI, FAISS, Gemini), desplegado en **AWS EC2** detrás de un
  Cloudflare Tunnel (HTTPS). Ver [`DEPLOY.md`](./DEPLOY.md).
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
