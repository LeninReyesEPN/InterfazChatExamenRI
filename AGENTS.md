<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# UI Typography Rule
- **Primary Font**: Always use **Josefin Sans** for all text elements across the entire web application interface.
- **Tailwind Configuration**: Under no circumstances should the typography be reverted to default sans-serif, system-ui, or Geist fonts. Keep `--font-sans: var(--font-josefin-sans)` active in Tailwind themes.

# Contexto del proyecto: Examen Final de Recuperación de Información (RAG sobre arXiv)

## Qué es esta carpeta

`ChatExamenRI` es el examen final del curso **ICCD753 Recuperación de Información** (EPN-FIS,
2026-A, Prof. Iván Carrera). El enunciado completo está en
`Guia del examen/examen2bim.pdf`. Este archivo resume ese enunciado y el contexto de cómo se
armaron los ejercicios previos del curso, para que cualquier trabajo aquí sea consistente con
ambos.

## Qué hay que construir

Un sistema RAG (Retrieval-Augmented Generation) completo sobre el corpus **arXiv Paper
Abstracts** (Kaggle: `spsayakpaul/arxiv-paper-abstracts` — títulos, abstracts y tópicos de
papers científicos), con:

1. **Preparación del corpus** (arXiv abstracts).
2. **Embeddings** de los documentos (modelo de texto, no multimodal — el corpus es solo texto).
3. **Almacenamiento y búsqueda vectorial** (una vector DB).
4. **Recuperación** semántica top-k para cada consulta.
5. **Generación aumentada** con un LLM que responda usando los fragmentos recuperados como
   contexto.
6. **Presentación de evidencias**: mostrar al usuario los documentos/fragmentos usados para
   construir la respuesta, de forma que se pueda verificar consulta → evidencia → respuesta.
7. **Interfaz web tipo chat** (esta carpeta, el front de Next.js) — no requiere memoria
   conversacional, cada consulta es independiente.
8. **Despliegue en la nube** con URL pública y accesible durante el periodo de evaluación
   (Hugging Face Spaces, Streamlit Community Cloud, Render, Railway, Google Cloud Run, AWS o
   Azure). Las API keys van por variables de entorno/secrets, nunca hardcodeadas ni en el repo.
9. **Evaluación**: juicio subjetivo documentado sobre corrección, relevancia, fidelidad a las
   evidencias, capacidad de integrar varios documentos, y capacidad de reconocer cuando el
   corpus no tiene información suficiente.

**Entregable final**: un **Jupyter Notebook** con al menos un bloque de Markdown y uno de
código por cada ítem A–I de Requerimientos, más el link a la URL del chat desplegado.

## Estado actual: ya implementado

Esto ya está construido (no es un plan, es lo que hay en el repo):

- **Backend** (`backend/`): paquete Python ejecutado como `backend.main:app` (FastAPI, sin
  `__init__.py`, mismo patrón que `ProyectoFinal/backend`).
  - `corpus.py` — descarga `spsayakpaul/arxiv-paper-abstracts` vía `kagglehub` (sin credenciales
    manuales), toma un subconjunto de ~4000 papers, y genera `data/corpus.json`
    (`paper_id`, `title`, `abstract`, `categories`) + `data/qrels.json` (10 consultas de
    referencia con relevancia sintética derivada de las categorías arXiv de cada paper — el
    dataset crudo no trae juicios de relevancia). Fallback a un corpus mock si falla la descarga.
  - `embeddings.py` — `sentence-transformers/all-MiniLM-L6-v2` (texto puro, sin CLIP),
    `normalize_embeddings=True`.
  - `vector_db.py` — FAISS `IndexFlatIP` sobre `title + abstract`, persistido en
    `data/faiss.index`.
  - `rag.py` — vector search (top-10) → re-rank con `cross-encoder/ms-marco-MiniLM-L-6-v2` (top-4)
    → generación con **Gemini** (`gemini-2.5-flash`, `GEMINI_API_KEY` por variable de entorno) →
    devuelve `{answer, evidences, insufficient_evidence}`. `insufficient_evidence=True` cuando la
    mejor similitud recuperada cae bajo `INSUFFICIENT_EVIDENCE_THRESHOLD=0.30`; el prompt además
    instruye al LLM a decirlo explícitamente. No implementa memoria conversacional ni relevance
    feedback (el examen no los exige) — cada consulta se procesa de forma independiente.
  - `evaluation.py` — Precision@k/Recall@k/NDCG@k (k=1,3,5) contra `qrels.json`.
  - `main.py` — endpoints `POST /api/chat`, `GET /api/evaluate`, `POST /api/index`,
    `GET /api/health`. CORS configurable vía `CORS_ORIGINS` (env var, default `*`).
  - Validado localmente: descarga real de Kaggle, build de índice FAISS con 4000 papers,
    retrieval de prueba y evaluación corrieron correctamente. **Importante**: usar un venv con
    **Python 3.11+** (`/opt/homebrew/bin/python3.11 -m venv backend/.venv`) — con Python 3.9 el
    import de `google-genai` falla en este Mac por un binario de `cryptography`
    incompatible con OpenSSL del sistema; en la instancia EC2 (Ubuntu 22.04, Python 3.10 de
    fábrica) no debería ocurrir, pero si aparece el mismo error ahí, sube a Python 3.11.
- **Frontend** (`src/`): adaptado para consumir el nuevo shape de evidencia
  (`paper_id`, `title`, `abstract`, `categories`, `similarity` — sin `image_url`), URL del backend
  configurable vía `NEXT_PUBLIC_API_URL` (ver `.env.local.example`), y un aviso visible cuando
  `insufficient_evidence` es `true`. El botón de like/dislike quedó como feedback local de UI
  (ya no llama a un endpoint de relevance feedback, que no es requerido).
- **Notebook** (`examen_rag_arxiv.ipynb`, raíz del repo): documenta y ejecuta A–I importando
  `backend/*`, con la tabla de evaluación subjetiva (ítem I) para completar manualmente tras
  correr el sistema con consultas propias.
- **Despliegue** (`DEPLOY.md` + `deploy/`): guía y scripts para **AWS EC2 t2.micro/t3.micro**
  (decisión del usuario, no una de las sugeridas por defecto en el enunciado, pero permitida —
  el enunciado lista "AWS" como opción válida). Arquitectura: nginx en el puerto 80 enrutando por
  path (`/api/*` → FastAPI en :8000, `/*` → `next start` en :3000), ambos como servicios systemd,
  con swapfile de 2GB por la RAM limitada de la instancia. Nadie ha ejecutado estos pasos en AWS
  todavía — son para que el usuario los corra en su propia cuenta.

## Precedente de origen: `ProyectoFinal/backend`

Todo lo anterior es una adaptación de `../ProyectoFinal/backend`, que implementa un pipeline RAG
**multimodal** (e-commerce, CLIP, dataset de Hugging Face) con bonus features (query expansion,
relevance feedback, memoria conversacional) que aquí se dejaron fuera a propósito porque el
examen no las exige y simplifican el pipeline.

## Convenciones del curso reflejadas en el notebook

Con base en exámenes previos (`Examen/`, `RI-Examen/`, y el examen de un compañero en
`repo-fab/`) y en los ejercicios (`recuperacion-informacion/Ejercicio-*`):

- Título H1 + subtítulo describiendo el examen y el corpus/sistema.
- Secciones nombradas explícitamente según los ítems del enunciado (A. Preparación del corpus,
  B. Representación mediante embeddings, ... I. Evaluación).
- Cada requerimiento: bloque Markdown explicando qué se hace y por qué, seguido de bloque(s) de
  código que lo implementan y muestran resultados (tablas `| Consulta | Documento | Score |`).
- Cierre con una sección de evaluación/conclusiones que cubra los 5 puntos subjetivos del ítem I,
  y el link a la URL desplegada (placeholder `TODO` hasta que el despliegue en EC2 esté listo).

## Librerías usadas

`fastapi`, `uvicorn`, `pydantic`, `pandas`, `numpy<2.0`, `kagglehub`, `faiss-cpu`,
`sentence-transformers` (`all-MiniLM-L6-v2` + `cross-encoder/ms-marco-MiniLM-L-6-v2`),
`google-genai` (Gemini). Ver `backend/requirements.txt`.
