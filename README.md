# Sistema RAG sobre arXiv Paper Abstracts

Examen final de **ICCD753 Recuperación de Información** (EPN-FIS, 2026-A, Prof. Iván Carrera).
Sistema de Recuperación Aumentada por Generación (RAG) que responde consultas en lenguaje natural
sobre el corpus [arXiv Paper Abstracts](https://www.kaggle.com/datasets/spsayakpaul/arxiv-paper-abstracts)
(Kaggle), usando búsqueda semántica sobre una base de datos vectorial y un LLM (Gemini) para
generar respuestas fundamentadas en la evidencia recuperada.

El enunciado completo está en `Guia del examen/examen2bim.pdf`. El notebook
[`examen_rag_arxiv.ipynb`](./examen_rag_arxiv.ipynb) documenta e implementa cada requerimiento
(A–I) del enunciado.

---

## Arquitectura

* **Frontend (Next.js/React, `src/`)**: interfaz de chat conversacional. Envía cada consulta al
  backend y muestra la respuesta junto con las evidencias (papers) usadas para generarla.
* **Backend (FastAPI, `backend/`)**: pipeline RAG completo.
  1. **Corpus** (`corpus.py`): descarga el dataset de Kaggle vía `kagglehub`, toma un subconjunto
     de ~4000 papers y genera `data/corpus.json` + juicios de relevancia sintéticos
     (`data/qrels.json`) para evaluación.
  2. **Embeddings** (`embeddings.py`): `sentence-transformers/all-MiniLM-L6-v2` sobre
     `título + abstract`.
  3. **Vector DB** (`vector_db.py`): índice FAISS (`IndexFlatIP`) para búsqueda por similitud
     coseno.
  4. **RAG** (`rag.py`): búsqueda vectorial (top-10) → re-ranking con cross-encoder
     (`cross-encoder/ms-marco-MiniLM-L-6-v2`, top-4) → generación con **Gemini**
     (`gemini-2.5-flash`), indicando explícitamente cuando la evidencia recuperada es
     insuficiente para responder con certeza.
  5. **Evaluación** (`evaluation.py`): Precision@k, Recall@k, NDCG@k contra los qrels sintéticos.

Cada consulta se procesa de forma independiente (no hay memoria conversacional — no es un
requisito del examen).

---

## Instalación y ejecución local

### Requisitos previos
* Python 3.11+ (evita usar 3.9: en algunos entornos `google-genai`/`cryptography` fallan por un
  binario incompatible con Python < 3.10).
* Node.js 18+ y npm.
* Una API key de Gemini ([Google AI Studio](https://aistudio.google.com/)).

### Backend

```bash
python3.11 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
export GEMINI_API_KEY="tu-api-key-aquí"
python -m uvicorn backend.main:app --reload --port 8000
```

En el primer arranque, descarga el corpus de Kaggle y construye el índice FAISS automáticamente
(tarda 1-3 minutos).

### Frontend

```bash
npm install
cp .env.local.example .env.local   # ajusta NEXT_PUBLIC_API_URL si el backend no está en localhost:8000
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000).

---

## Evaluación experimental

```bash
curl http://localhost:8000/api/evaluate
# o directamente:
python -m backend.evaluation
```

Imprime Precision@k / Recall@k / NDCG@k (k=1,3,5) contra los juicios de relevancia sintéticos
descritos en `backend/corpus.py`. El juicio subjetivo sobre la calidad de la generación
(corrección, relevancia, fidelidad, integración multi-documento, reconocimiento de información
insuficiente) se documenta en la Sección I del notebook.

---

## Despliegue en la nube

**Backend → Hugging Face Spaces (Docker)**: la carpeta `huggingface-space/` (no versionada en
este repo, ver `.gitignore`) contiene un espejo listo para pushear al Space
`Lenin2008072/BackExamen`: `Dockerfile`, `README.md` con frontmatter `sdk: docker`, y el código
del backend con el corpus y el índice FAISS **ya pre-construidos** (no depende de Kaggle en
runtime). Pasos:

1. Clona tu Space: `git clone https://huggingface.co/spaces/Lenin2008072/BackExamen`
2. Copia dentro el contenido de `huggingface-space/` (sobrescribe `README.md`).
3. En el Space, ve a **Settings → Repository secrets** y agrega `GEMINI_API_KEY`.
4. `git add -A && git commit -m "Deploy backend RAG" && git push`
5. Cuando el Space termine de construir, la URL pública (`https://lenin2008072-backexamen.hf.space`)
   es tu `NEXT_PUBLIC_API_URL`.

**Frontend**: Vercel (gratis, HTTPS automático) apuntando a esa URL vía `NEXT_PUBLIC_API_URL`, o
alternativamente la misma instancia EC2 descrita en `DEPLOY.md`.

**Alternativa: AWS EC2** — ver [`DEPLOY.md`](./DEPLOY.md) y `deploy/` para desplegar todo
(frontend + backend) en una instancia EC2 de capa gratuita (`t2.micro`/`t3.micro`) con nginx.
