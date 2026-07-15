from __future__ import annotations

import os
from sentence_transformers import CrossEncoder
from google import genai
from backend.vector_db import search as vector_search

GEMINI_MODEL = "gemini-2.5-flash"

# Below this cosine-similarity threshold, the best retrieved evidence is
# considered too weak to ground an answer -> the system must say so instead
# of guessing (Requerimiento F: "indicar quando el corpus no contenga
# información suficiente").
INSUFFICIENT_EVIDENCE_THRESHOLD = 0.30

RETRIEVE_TOP_K = 10
RERANK_TOP_K = 4

_cross_encoder = None


def get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        print("Cargando modelo Cross-Encoder para Re-ranking...")
        try:
            _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            print("Cross-Encoder cargado exitosamente.")
        except Exception as e:
            print(f"Error al cargar Cross-Encoder: {e}. Se omitirá el re-ranking.")
            _cross_encoder = None
    return _cross_encoder


def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ADVERTENCIA: GEMINI_API_KEY no configurada. Las llamadas al LLM fallarán.")
    return genai.Client(api_key=api_key)


def retrieve_and_rerank(query: str) -> list[dict]:
    """Semantic search over the FAISS index, then cross-encoder re-ranking."""
    candidates = vector_search(query, top_k=RETRIEVE_TOP_K)
    if not candidates:
        return []

    cross_encoder = get_cross_encoder()
    if cross_encoder:
        pairs = [(query, f"{c['title']}. {c['abstract'][:300]}") for c in candidates]
        ce_scores = cross_encoder.predict(pairs)
        for c, score in zip(candidates, ce_scores):
            c["re_rank_score"] = float(score)
        candidates = sorted(candidates, key=lambda x: x["re_rank_score"], reverse=True)

    return candidates[:RERANK_TOP_K]


def build_context(evidences: list[dict]) -> str:
    context_str = ""
    for i, item in enumerate(evidences):
        context_str += f"[Documento {i + 1}] (ID: {item['paper_id']}, categorías: {', '.join(item['categories'])})\n"
        context_str += f"Título: {item['title']}\n"
        context_str += f"Abstract: {item['abstract']}\n\n"
    return context_str


def generate_rag_response(query: str, chat_history: list[dict] | None = None) -> dict:
    """RAG pipeline: vector search -> cross-encoder re-rank -> grounded LLM answer.

    Each query is processed independently (conversational memory is explicitly
    NOT required by the exam guide), so `chat_history` is accepted for
    frontend compatibility but ignored.
    """
    print(f"Procesando consulta RAG: '{query}'...")

    evidences = retrieve_and_rerank(query)
    best_similarity = max((e["similarity"] for e in evidences), default=0.0)
    insufficient_evidence = (not evidences) or (best_similarity < INSUFFICIENT_EVIDENCE_THRESHOLD)

    context_str = build_context(evidences)

    system_prompt = (
        "Eres un asistente de investigación que responde preguntas sobre un corpus de abstracts "
        "de papers de arXiv. Debes responder ÚNICAMENTE con base en los documentos recuperados que "
        "se muestran a continuación como contexto. Si el contexto es insuficiente, irrelevante o no "
        "cubre la pregunta, dilo EXPLÍCITAMENTE al inicio de tu respuesta (por ejemplo: 'El corpus no "
        "contiene información suficiente para responder esta consulta con certeza') en vez de inventar "
        "una respuesta. Cuando sí haya evidencia suficiente, integra información de varios documentos "
        "si es relevante y cita el número de documento entre corchetes (ej. [Documento 1]) al usar su "
        "contenido.\n\n"
        f"### Contexto recuperado:\n{context_str if context_str else '(sin documentos relevantes)'}\n"
        f"### Consulta del usuario: {query}\n"
        "Genera tu respuesta final en inglés (el mismo idioma del corpus y de la consulta):"
    )

    answer = "No se pudo contactar al servicio de Gemini en este momento."
    try:
        client = get_gemini_client()
        response = client.models.generate_content(model=GEMINI_MODEL, contents=system_prompt)
        answer = response.text.strip()
    except Exception as e:
        print(f"Error al llamar al LLM Gemini: {e}")
        if evidences:
            bullets = "\n".join(f"- {e_['title']} (similitud: {e_['similarity']:.2f})" for e_ in evidences)
            answer = (
                "No se pudo contactar al LLM (revisa GEMINI_API_KEY), pero se recuperaron estos "
                f"documentos como evidencia:\n{bullets}"
            )
        else:
            answer = "No se pudo contactar al LLM y tampoco se encontró evidencia relevante en el corpus."

    return {
        "answer": answer,
        "evidences": evidences,
        "insufficient_evidence": insufficient_evidence,
    }
