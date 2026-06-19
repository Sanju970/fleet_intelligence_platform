"""
Lane B — Retrieval interface. The CONTRACT Lane C (agent) depends on.

search(query, k=4, truck_id=None, doc_type=None) -> list of:
    {file, text, truck_id, driver_id, load_id, doc_type, score}

Backed by the Chroma vector DB built by ingest/pipeline.py. Supports optional
metadata filters (truck_id, doc_type) so the agent can scope retrieval — e.g.
"tax form for truck 8" filters to truck_id=8 before semantic ranking.

If the vector DB isn't built yet, raises a clear error telling you to run ingest.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(ROOT, "db", "chroma")

_col = None
def _collection():
    global _col
    if _col is None:
        import chromadb
        from ingest.pipeline import get_embedding_function
        if not os.path.exists(CHROMA_DIR):
            raise RuntimeError("Vector DB not found. Run: python ingest/pipeline.py")
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _col = client.get_collection("fleet_docs", embedding_function=get_embedding_function())
    return _col

def search(query, k=4, truck_id=None, doc_type=None):
    col = _collection()
    where = {}
    if truck_id is not None: where["truck_id"] = int(truck_id)
    if doc_type is not None: where["doc_type"] = doc_type
    kwargs = {"query_texts": [query], "n_results": k}
    if where:
        kwargs["where"] = where if len(where) == 1 else {"$and": [{k2: v2} for k2, v2 in where.items()]}
    res = col.query(**kwargs)
    out = []
    if res["ids"] and res["ids"][0]:
        for i in range(len(res["ids"][0])):
            m = res["metadatas"][0][i]
            out.append({
                "file": m["file"], "text": res["documents"][0][i],
                "truck_id": m["truck_id"], "driver_id": m["driver_id"],
                "load_id": m["load_id"], "doc_type": m["doc_type"],
                "score": round(1 - res["distances"][0][i], 3) if res.get("distances") else None,
            })
    return out

if __name__ == "__main__":
    for q in ["tax form 2290 for truck", "repair invoice brake", "registration expires"]:
        print(f"\nQ: {q}")
        for r in search(q, k=3):
            print(f"  [{r['doc_type']:18s} truck {r['truck_id']}] {r['file']}  score={r['score']}")
