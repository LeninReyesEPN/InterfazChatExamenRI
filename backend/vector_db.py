import os
import json
import faiss
from backend.embeddings import encode_text

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CORPUS_PATH = os.path.join(DATA_DIR, "corpus.json")
INDEX_PATH = os.path.join(DATA_DIR, "faiss.index")

# In-memory corpus cache and FAISS index
_corpus = []
_index = None
_paper_id_map = []  # Maps FAISS row offset -> paper_id


def load_corpus():
    global _corpus
    if not _corpus:
        if not os.path.exists(CORPUS_PATH):
            raise FileNotFoundError(f"El corpus no existe en {CORPUS_PATH}. Ejecuta corpus.py primero.")
        with open(CORPUS_PATH, "r", encoding="utf-8") as f:
            _corpus = json.load(f)
    return _corpus


def _document_text(item: dict) -> str:
    """Text representation indexed per paper: title + abstract."""
    return f"{item['title']}. {item['abstract']}"


def build_index():
    global _index, _paper_id_map
    corpus = load_corpus()
    if not corpus:
        print("El corpus está vacío. Imposible indexar.")
        return

    print("Indexando el corpus de abstracts en la base de datos vectorial FAISS...")
    texts = [_document_text(item) for item in corpus]

    embeddings = encode_text(texts)  # float32 numpy array, L2-normalized
    dimension = embeddings.shape[1]

    # IndexFlatIP over normalized vectors == exact cosine similarity search.
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)

    paper_ids = [item["paper_id"] for item in corpus]
    with open(INDEX_PATH + ".map", "w", encoding="utf-8") as f:
        json.dump(paper_ids, f)

    _index = index
    _paper_id_map = paper_ids
    print(f"Indexación completada. {len(paper_ids)} papers guardados en {INDEX_PATH}")


def load_index():
    global _index, _paper_id_map
    if _index is None:
        if not os.path.exists(INDEX_PATH) or not os.path.exists(INDEX_PATH + ".map"):
            build_index()
        else:
            _index = faiss.read_index(INDEX_PATH)
            with open(INDEX_PATH + ".map", "r", encoding="utf-8") as f:
                _paper_id_map = json.load(f)
    return _index, _paper_id_map


def search(query_text: str, top_k: int = 5) -> list[dict]:
    """Retrieves the top-k closest papers from the FAISS vector index."""
    index, id_map = load_index()
    corpus = load_corpus()
    corpus_by_id = {item["paper_id"]: item for item in corpus}

    query_vector = encode_text([query_text])  # shape (1, dim)
    scores, indices = index.search(query_vector, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        p_id = id_map[idx]
        paper = corpus_by_id.get(p_id)
        if paper:
            results.append({
                "paper_id": p_id,
                "title": paper["title"],
                "abstract": paper["abstract"],
                "categories": paper["categories"],
                # Cosine similarity score as float.
                "similarity": float(score),
            })
    return results


if __name__ == "__main__":
    build_index()
    res = search("graph neural networks applications", top_k=3)
    print("Test Search Results:")
    for r in res:
        print(f"  [{r['similarity']:.3f}] {r['title']}")
