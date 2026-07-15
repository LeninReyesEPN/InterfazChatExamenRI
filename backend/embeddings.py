import numpy as np
from sentence_transformers import SentenceTransformer

# arXiv abstracts are text-only, so a lightweight sentence-embedding model is
# enough (no need for the CLIP multimodal model used in the sibling e-commerce
# project). all-MiniLM-L6-v2 is the model already used across this course's
# exercises (Ejercicio11 Web Scraping, first-bimester exam).
MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def get_model():
    global _model
    if _model is None:
        print(f"Cargando el modelo de embeddings de texto ({MODEL_NAME})...")
        _model = SentenceTransformer(MODEL_NAME)
        print("Modelo de embeddings cargado exitosamente.")
    return _model


def encode_text(texts: list[str]) -> np.ndarray:
    """Generates embeddings for paper text (titles+abstracts) or user queries."""
    model = get_model()
    # Normalize embeddings so inner product == cosine similarity.
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.array(embeddings, dtype=np.float32)
