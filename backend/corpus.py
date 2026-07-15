import os
import json
import ast
import glob
import pandas as pd

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CORPUS_PATH = os.path.join(DATA_DIR, "corpus.json")
QRELS_PATH = os.path.join(DATA_DIR, "qrels.json")
KAGGLE_DATASET = "spsayakpaul/arxiv-paper-abstracts"
SUBSET_SIZE = 4000

# Synthetic relevance judgments: each benchmark query is mapped to the arXiv
# category codes ("terms") that should be considered relevant. A paper whose
# `categories` list contains a mapped code gets that code's score; papers that
# match no mapped code are irrelevant (score 0). This mirrors how the earlier
# `proyecto/` project derived qrels from Reuters topic categories, since the
# raw Kaggle dataset ships no query/relevance judgments of its own.
BENCHMARK_QUERIES = [
    {"query": "What are the main applications of Graph Neural Networks?",
     "categories": {"cs.LG": 3, "cs.AI": 2, "cs.SI": 2}},
    {"query": "How is reinforcement learning used in robotics?",
     "categories": {"cs.RO": 3, "cs.LG": 2}},
    {"query": "Recent advances in diffusion models for image generation.",
     "categories": {"cs.CV": 3, "cs.LG": 2}},
    {"query": "Techniques for improving retrieval-augmented generation systems.",
     "categories": {"cs.CL": 3, "cs.IR": 3, "cs.LG": 1}},
    {"query": "Advances in transformer architectures for natural language processing.",
     "categories": {"cs.CL": 3, "cs.LG": 2}},
    {"query": "Convolutional neural networks for image classification.",
     "categories": {"cs.CV": 3, "cs.LG": 2}},
    {"query": "Explainability and interpretability of deep learning models.",
     "categories": {"cs.LG": 3, "cs.AI": 2}},
    {"query": "Federated learning for privacy preserving machine learning.",
     "categories": {"cs.LG": 3, "cs.CR": 2}},
    {"query": "Statistical methods for time series forecasting.",
     "categories": {"stat.ML": 3, "cs.LG": 2}},
    {"query": "Robustness and adversarial attacks on neural networks.",
     "categories": {"cs.LG": 3, "cs.CR": 2, "cs.CV": 1}},
]


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)


def _parse_terms(raw_terms) -> list[str]:
    """The Kaggle CSV stores `terms` as a stringified Python list, e.g. "['cs.CV', 'cs.LG']"."""
    if isinstance(raw_terms, list):
        return raw_terms
    if not isinstance(raw_terms, str):
        return []
    try:
        parsed = ast.literal_eval(raw_terms)
        return list(parsed) if isinstance(parsed, (list, tuple)) else [str(parsed)]
    except (ValueError, SyntaxError):
        return [t.strip() for t in raw_terms.strip("[]").replace("'", "").split(",") if t.strip()]


def _locate_csv(dataset_dir: str) -> str:
    csv_files = glob.glob(os.path.join(dataset_dir, "**", "*.csv"), recursive=True)
    if not csv_files:
        raise FileNotFoundError(f"No se encontró ningún CSV dentro de {dataset_dir}")
    # Prefer the canonical file name used by the dataset if present.
    for f in csv_files:
        if os.path.basename(f) == "arxiv_data.csv":
            return f
    return csv_files[0]


def build_qrels(corpus_list: list[dict]) -> list[dict]:
    qrels = []
    for q in BENCHMARK_QUERIES:
        relevance = []
        for paper in corpus_list:
            paper_cats = set(paper["categories"])
            matched_scores = [score for cat, score in q["categories"].items() if cat in paper_cats]
            if matched_scores:
                relevance.append({"paper_id": paper["paper_id"], "score": max(matched_scores)})
        qrels.append({
            "query_id": f"Q{len(qrels) + 1:02d}",
            "query": q["query"],
            "relevance": relevance,
        })
    return qrels


def download_and_prepare_corpus():
    print("Iniciando la preparación del corpus de arXiv Paper Abstracts...")
    ensure_dirs()

    if os.path.exists(CORPUS_PATH) and os.path.exists(QRELS_PATH):
        print(f"El corpus ya existe en {CORPUS_PATH}. Saltando descarga.")
        return

    try:
        import kagglehub

        print(f"Descargando '{KAGGLE_DATASET}' desde Kaggle (kagglehub)...")
        dataset_dir = kagglehub.dataset_download(KAGGLE_DATASET)
        csv_path = _locate_csv(dataset_dir)
        print(f"Archivo encontrado: {csv_path}")

        df = pd.read_csv(csv_path)
        df = df.dropna(subset=["titles", "summaries"]).reset_index(drop=True)
        if len(df) > SUBSET_SIZE:
            df = df.sample(n=SUBSET_SIZE, random_state=42).reset_index(drop=True)

        corpus_list = []
        for idx, row in df.iterrows():
            corpus_list.append({
                "paper_id": f"P{idx:05d}",
                "title": str(row["titles"]).strip(),
                "abstract": str(row["summaries"]).strip(),
                "categories": _parse_terms(row.get("terms")),
            })

        with open(CORPUS_PATH, "w", encoding="utf-8") as f:
            json.dump(corpus_list, f, indent=2, ensure_ascii=False)
        print(f"Corpus guardado: {len(corpus_list)} papers en {CORPUS_PATH}")

        qrels = build_qrels(corpus_list)
        with open(QRELS_PATH, "w", encoding="utf-8") as f:
            json.dump(qrels, f, indent=2, ensure_ascii=False)
        print(f"Qrels sintéticos guardados: {len(qrels)} consultas en {QRELS_PATH}")

    except Exception as e:
        print(f"Error al descargar/preparar el corpus desde Kaggle: {e}")
        print("Generando corpus y qrels simulados para desarrollo local...")
        generate_mock_corpus()


def generate_mock_corpus():
    ensure_dirs()
    mock_papers = [
        {"paper_id": "P00001", "title": "Graph Neural Networks for Node Classification",
         "abstract": "We study graph neural networks (GNNs) and their applications to node classification, "
                      "link prediction and recommendation tasks over large-scale graphs.",
         "categories": ["cs.LG", "cs.AI"]},
        {"paper_id": "P00002", "title": "Deep Reinforcement Learning for Robotic Manipulation",
         "abstract": "This paper presents a reinforcement learning framework for robotic manipulation tasks "
                      "using policy gradient methods trained in simulation and transferred to real robots.",
         "categories": ["cs.RO", "cs.LG"]},
        {"paper_id": "P00003", "title": "Denoising Diffusion Probabilistic Models for Image Synthesis",
         "abstract": "We propose improvements to diffusion probabilistic models that achieve state of the art "
                      "sample quality for high resolution image generation.",
         "categories": ["cs.CV", "cs.LG"]},
        {"paper_id": "P00004", "title": "Improving Retrieval-Augmented Generation with Re-ranking",
         "abstract": "We introduce a re-ranking stage for retrieval-augmented generation (RAG) pipelines that "
                      "improves answer faithfulness by filtering irrelevant retrieved passages.",
         "categories": ["cs.CL", "cs.IR"]},
        {"paper_id": "P00005", "title": "A Survey of Transformer Architectures in NLP",
         "abstract": "This survey reviews transformer-based architectures for natural language processing, "
                      "covering attention mechanisms, pretraining objectives and downstream fine-tuning.",
         "categories": ["cs.CL", "cs.LG"]},
    ]
    with open(CORPUS_PATH, "w", encoding="utf-8") as f:
        json.dump(mock_papers, f, indent=2, ensure_ascii=False)

    qrels = build_qrels(mock_papers)
    with open(QRELS_PATH, "w", encoding="utf-8") as f:
        json.dump(qrels, f, indent=2, ensure_ascii=False)

    print(f"Corpus de prueba y qrels creados exitosamente en {DATA_DIR}")


if __name__ == "__main__":
    download_and_prepare_corpus()
