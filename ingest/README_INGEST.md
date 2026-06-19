# Lane B — OCR Ingestion Pipeline

Turns 1,014 messy fleet documents into a searchable, truck-tagged vector DB.

## Run
```
python ingest/pipeline.py              # full ingest (~1000 docs)
python ingest/pipeline.py --limit 50   # quick smoke test
```

## What it does
1. **Extract** — clean PDFs via pdfplumber (fast, native text); messy scans via
   Tesseract OCR (handles skew/stains/handwriting, with realistic OCR errors).
2. **Tag** — every chunk linked to truck/driver/load via `data/manifest.json`.
3. **Embed + store** — Chroma vector DB at `db/chroma/`.

## ⏱️ TIMING — READ THIS
OCR is the bottleneck. Measured: **~200 docs in ~2 min** (73 of them scans).
Full ~1000-doc set ≈ **8–10 min**, dominated by the ~280 scans.
**Kick this off in HOUR 1** while other lanes build. Don't block on it.

## Embeddings
Ships with a **no-download hash fallback** so it runs anywhere offline.
At the event, swap to real semantic embeddings (one line in `get_embedding_function`):
```python
embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
```
The fallback gives rough ranking; metadata filtering (truck_id, doc_type) is exact
either way — that's what makes "tax form for truck 8" work.

## The contract (Lane C depends on this — don't break it)
```python
from retrieval.search import search
search(query, k=4, truck_id=None, doc_type=None)
#   -> [{file, text, truck_id, driver_id, load_id, doc_type, score}, ...]
```
Optional filters let the agent scope retrieval before semantic ranking.
