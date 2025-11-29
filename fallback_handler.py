# fallback_integration.py
from chromadb import PersistentClient
import re
from typing import Optional

def vector_search(query_text: str, top_k: int = 20, chroma_path: str = "chroma_store", collection_name: str = "employee_collection"):
    client = PersistentClient(path=chroma_path)
    collection = client.get_collection(collection_name)
    results = collection.query(query_texts=[query_text], n_results=top_k)
    return results

def rerank_by_distance(results: dict) -> dict:
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    combined = list(zip(distances, ids, docs, metas))
    combined_sorted = sorted(combined, key=lambda x: x[0] if x[0] is not None else float("inf"))

    reranked = {
        "ids": [[c[1] for c in combined_sorted]],
        "documents": [[c[2] for c in combined_sorted]],
        "metadatas": [[c[3] for c in combined_sorted]],
        "distances": [[c[0] for c in combined_sorted]],
    }
    return reranked

def summarize_results(results: dict) -> str:
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    parts = []
    for i, doc in enumerate(docs):
        meta = metas[i] if i < len(metas) else {}
        dist = distances[i] if i < len(distances) else None
        row_id = meta.get("row_id") if isinstance(meta, dict) else None
        # Keep the doc (which is your denormalized employee content) short
        parts.append(
            f"Rank {i+1} — ID: {row_id} — score: {dist:.4f}\n{doc.strip()}"
        )
    return "\n\n".join(parts)

def semantic_fallback(user_nl_query, top_k: int = 20, chroma_path: str = r"C:\Users\H A R I H A R A N\Desktop\My works\Nectar\Project\vector_db"):

    # 1) choose query
    query_used = user_nl_query.strip()

    # 2) perform vector search
    raw = vector_search(query_used, top_k=top_k, chroma_path=chroma_path)

    # 3) rerank results
    reranked = rerank_by_distance(raw)

    # 4) summarize
    summary_text = summarize_results(reranked)

    return {
        "query_used": query_used,
        "summary": summary_text,
        "raw_results": reranked
    }

if __name__ == "__main__":
    res = semantic_fallback(user_nl_query="list out the employees with javascript skills")
    print(res['query_used'])
    print(res['summary'])