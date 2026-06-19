"""
Demo UI backend — a small FastAPI server wrapping agent.answer().

    uvicorn ui.app:app --port 8000      (then open http://127.0.0.1:8000)
or  python ui/app.py                     (serves UI + API on :8000)

Endpoints:
  GET  /          -> the chat console (ui/index.html)
  GET  /health    -> liveness + which subsystems are ready
  GET  /stats     -> fleet/document counts for the UI header
  POST /ask {question} -> full agent trace (route, sql, docs, answer)

Every response carries the routing decision and the evidence so the frontend can
SHOW how the answer was reached, not just the final text.
"""
import os, sys, sqlite3, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="FleetIQ")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB = os.path.join(ROOT, "db", "fleet.db")
MANIFEST = os.path.join(ROOT, "data", "manifest.json")

_RETRIEVAL_READY = False


@app.on_event("startup")
def _warmup():
    # Show which LLM each role will use, then build the graph and prime Chroma so
    # the first request is fast and the sync worker doesn't stall mid-request.
    global _RETRIEVAL_READY
    try:
        from agent.llm import status
        status()
    except Exception:
        pass
    import agent.graph as G
    if G.AGENT is None:
        G.AGENT = G.build_graph()
    try:
        from retrieval.search import _collection
        _collection()
        _RETRIEVAL_READY = True
    except Exception as e:
        print("warmup: retrieval not ready:", e,
              "\n  -> run `python ingest/pipeline.py` to enable document search.")
    print("FleetIQ warm — graph ready; retrieval", "ready." if _RETRIEVAL_READY else "DISABLED.")


class Q(BaseModel):
    question: str


@app.post("/ask")
def ask(q: Q):
    question = (q.question or "").strip()
    if not question:
        return JSONResponse({"error": "Empty question."}, status_code=400)
    import agent.graph as G
    if G.AGENT is None:
        G.AGENT = G.build_graph()
    try:
        final = G.AGENT.invoke({"question": question})
    except Exception as e:
        # Never leak a stack trace to the client; degrade gracefully.
        return JSONResponse({
            "question": question, "route": None, "answer": None,
            "error": f"The agent hit an error processing that question: {e}",
        }, status_code=500)
    docs = final.get("docs") or []
    return JSONResponse({
        "question": question,
        "route": final.get("route"),
        "truck_id": final.get("truck_id"),
        "sql": final.get("sql"),
        "sql_rows": final.get("sql_rows"),
        "documents": [{"file": d["file"], "doc_type": d["doc_type"],
                       "truck_id": d["truck_id"], "score": d.get("score")} for d in docs],
        "note": final.get("note"),
        "answer": final.get("answer"),
    })


@app.get("/health")
def health():
    retrieval = _RETRIEVAL_READY or os.path.exists(os.path.join(ROOT, "db", "chroma"))
    return {"status": "ok", "db": os.path.exists(DB), "retrieval": bool(retrieval)}


@app.get("/stats")
def stats():
    """Fleet + document counts so the UI header reflects the real dataset."""
    out = {"trucks": None, "documents": None, "doc_types": None}
    try:
        con = sqlite3.connect(DB)
        out["trucks"] = con.execute("SELECT COUNT(*) FROM trucks").fetchone()[0]
        con.close()
    except Exception:
        pass
    try:
        with open(MANIFEST) as f:
            docs = json.load(f)["documents"]
        out["documents"] = len(docs)
        out["doc_types"] = len({d["doc_type"] for d in docs})
    except Exception:
        pass
    return out


@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
