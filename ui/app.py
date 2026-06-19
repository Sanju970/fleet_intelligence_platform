"""
Lane D — Demo UI backend. A tiny FastAPI server wrapping agent.answer().

    uvicorn ui.app:app --reload --port 8000   (then open ui/index.html)
or  python ui/app.py                          (serves UI + API on :8000)

Exposes POST /ask {question} -> the full agent trace (route, sql, docs, answer)
so the frontend can SHOW the routing decision, not just the final text.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="FleetIQ")
HERE = os.path.dirname(os.path.abspath(__file__))

@app.on_event("startup")
def _warmup():
    # Show which LLM each role will use, then build the graph and prime Chroma so
    # the first request is fast and the sync worker doesn't stall mid-request.
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
    except Exception as e:
        print("warmup: retrieval not ready:", e)
    print("FleetIQ warm — graph + vector store ready.")

class Q(BaseModel):
    question: str

@app.post("/ask")
def ask(q: Q):
    import agent.graph as G
    if G.AGENT is None: G.AGENT = G.build_graph()
    final = G.AGENT.invoke({"question": q.question})
    docs = final.get("docs") or []
    return JSONResponse({
        "question": q.question,
        "route": final.get("route"),
        "truck_id": final.get("truck_id"),
        "sql": final.get("sql"),
        "sql_rows": final.get("sql_rows"),
        "documents": [{"file": d["file"], "doc_type": d["doc_type"],
                       "truck_id": d["truck_id"], "score": d.get("score")} for d in docs],
        "answer": final.get("answer"),
    })

@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
