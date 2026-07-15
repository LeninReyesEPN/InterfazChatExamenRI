# Sistema RAG sobre arXiv Paper Abstracts

Examen final de Recuperación de Información (EPN-FIS). Chat que responde preguntas en lenguaje
natural sobre el corpus [arXiv Paper Abstracts](https://www.kaggle.com/datasets/spsayakpaul/arxiv-paper-abstracts),
usando búsqueda semántica y un LLM para generar respuestas con evidencias.

## Entrega del examen

- **Chat desplegado**: https://main.d1ngrhzkw2klti.amplifyapp.com/
- **API del backend**: https://connectivity-navigate-insert-genres.trycloudflare.com (EC2 + Cloudflare Tunnel)
- **Notebook del examen** (requerimientos A–I, con evidencias, evaluación y esta misma URL):
  [`examen_rag_arxiv.ipynb`](./examen_rag_arxiv.ipynb)
- **Enunciado**: [`Guia del examen/examen2bim.pdf`](./Guia%20del%20examen/examen2bim.pdf)

### Idioma

El corpus (abstracts de arXiv) y las respuestas generadas están **en inglés**. Se preguntas en
español la búsqueda pierde precisión y de todas formas la respuesta llega en inglés — usa
consultas en inglés para obtener los mejores resultados.

### Preguntas de ejemplo

- "What are the main applications of Graph Neural Networks?"
- "How is reinforcement learning used in robotics?"
- "Recent advances in diffusion models for image generation."
- "Techniques for improving retrieval-augmented generation systems."
- "Explainability and interpretability of deep learning models"
- "Federated learning for privacy preserving machine learning"

Para probar el caso de "el corpus no tiene información suficiente" (Requerimiento F), usa una
consulta fuera de dominio, ej.: "What is the best recipe for a chocolate cake?"

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
