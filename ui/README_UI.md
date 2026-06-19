# Lane D — Demo UI (Dispatch Terminal)

The chat interface that shows not just the answer but **which route the agent took
and what it cited** — the routing visibility is what makes the demo land with judges.

## Run
```
# 1. make sure data + db + ingest are done (see QUICKSTART)
# 2. start the backend (serves API + UI together)
uvicorn ui.app:app --port 8000
# 3. open http://localhost:8000
```

## What judges see
- A **route badge** on every answer: SQL · DATABASE / DOC · RETRIEVAL / HYBRID · BOTH
- The **exact SQL query** executed (for DB answers)
- **Document chips** — cited files with doc_type, truck tag, and relevance score
- Inline **citations** as amber chips
- The **grounding trap**: ask "GPS location of truck 5" — it REFUSES instead of
  hallucinating. Demo this on purpose; it's your strongest no-hallucination proof.

## Demo sequence (rehearse)
1. SQL — "How many trucks are active?"          (watch the query appear)
2. DOC — "Where is the tax form for truck 8?"   (watch it scope to truck 8 + cite)
3. HYBRID — "Registrations expiring + renewal docs?" (DB + documents merged)
4. TRAP — "GPS location of truck 5?"            (watch it refuse — grounded)
5. One line: "same engine, swap the data source → BigQuery, manuals."

## Files
- ui/app.py     — FastAPI backend wrapping agent.answer(), warms up at startup
- ui/index.html — single-file frontend, no build step, talks to /ask
