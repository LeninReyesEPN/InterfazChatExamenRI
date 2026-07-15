"""End-to-end smoke test: corpus -> index -> search -> RAG -> evaluation."""
from backend.corpus import download_and_prepare_corpus
from backend.vector_db import build_index, search
from backend.rag import generate_rag_response
from backend.evaluation import run_evaluation

if __name__ == "__main__":
    print("=== 1. Corpus ===")
    download_and_prepare_corpus()

    print("\n=== 2. Índice FAISS ===")
    build_index()

    print("\n=== 3. Búsqueda vectorial ===")
    query = "What are the main applications of Graph Neural Networks?"
    for r in search(query, top_k=3):
        print(f"  [{r['similarity']:.3f}] {r['title']}")

    print("\n=== 4. RAG (retrieval + re-ranking + generación) ===")
    result = generate_rag_response(query)
    print("Respuesta:", result["answer"][:300], "...")
    print("Evidencias:", len(result["evidences"]))
    print("¿Evidencia insuficiente?:", result["insufficient_evidence"])

    print("\n=== 5. Evaluación ===")
    run_evaluation()
