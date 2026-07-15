import os
import json
import numpy as np
from backend.vector_db import search

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
QRELS_PATH = os.path.join(DATA_DIR, "qrels.json")


def load_qrels():
    if not os.path.exists(QRELS_PATH):
        raise FileNotFoundError(f"No qrels file found at {QRELS_PATH}.")
    with open(QRELS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_metrics_for_query(retrieved_ids: list[str], relevance_list: list[dict], k: int) -> dict:
    """Computes Precision@K, Recall@K, and NDCG@K for a single query."""
    rel_map = {item["paper_id"]: item["score"] for item in relevance_list}

    relevant_retrieved = 0
    actual_relevances = []
    for i in range(min(k, len(retrieved_ids))):
        p_id = retrieved_ids[i]
        rel_score = rel_map.get(p_id, 0)
        actual_relevances.append(rel_score)
        if rel_score > 0:
            relevant_retrieved += 1
    actual_relevances += [0] * (k - len(actual_relevances))

    precision = relevant_retrieved / k

    total_relevant = sum(1 for item in relevance_list if item["score"] > 0)
    recall = (relevant_retrieved / total_relevant) if total_relevant > 0 else 0.0

    dcg = sum((2 ** rel - 1) / np.log2(i + 2) for i, rel in enumerate(actual_relevances[:k]))

    ideal_relevances = sorted([item["score"] for item in relevance_list], reverse=True)
    ideal_relevances += [0] * (k - len(ideal_relevances))
    idcg = sum((2 ** rel - 1) / np.log2(i + 2) for i, rel in enumerate(ideal_relevances[:k]))

    ndcg = (dcg / idcg) if idcg > 0 else 0.0

    return {"precision": precision, "recall": recall, "ndcg": ndcg}


def run_evaluation(k_values=[1, 3, 5]) -> dict:
    """Evaluates all benchmark queries in qrels.json and returns averaged metrics."""
    qrels = load_qrels()
    if not qrels:
        print("La base de qrels está vacía.")
        return {}

    overall_metrics = {k: {"precision": [], "recall": [], "ndcg": []} for k in k_values}

    print(f"Evaluando {len(qrels)} consultas del benchmark experimental...")
    for q_entry in qrels:
        q_text = q_entry["query"]
        relevance_list = q_entry["relevance"]

        max_k = max(k_values)
        retrieved_results = search(q_text, top_k=max_k)
        retrieved_ids = [res["paper_id"] for res in retrieved_results]

        for k in k_values:
            metrics = calculate_metrics_for_query(retrieved_ids, relevance_list, k)
            overall_metrics[k]["precision"].append(metrics["precision"])
            overall_metrics[k]["recall"].append(metrics["recall"])
            overall_metrics[k]["ndcg"].append(metrics["ndcg"])

    report = {}
    for k in k_values:
        report[f"K={k}"] = {
            "Precision@k": round(float(np.mean(overall_metrics[k]["precision"])), 4),
            "Recall@k": round(float(np.mean(overall_metrics[k]["recall"])), 4),
            "NDCG@k": round(float(np.mean(overall_metrics[k]["ndcg"])), 4),
        }

    print("Resultados de la Evaluación Experimental:")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run_evaluation()
