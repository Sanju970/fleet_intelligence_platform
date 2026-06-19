# FleetIQ — Grounded Hybrid Document Agent for Trucking Fleets

FleetIQ ingests an entire fleet's paperwork — titles, tax forms, fuel receipts,
registrations, maintenance invoices, logs — links every document to the right
**truck, driver, and trailer**, and lets an operator ask anything in plain English.

Each question is routed to the right engine — a **SQL query**, **document
retrieval**, or **both** — and answered **grounded in the evidence, with inline
citations, and an honest "I don't have that" when the answer isn't in the data.**
No hallucinations.

```
"Which trucks are profitable?"               → SQL over the fleet database
"Where's the tax form for truck 8?"          → semantic search over scanned docs
"What do I need to renew truck 9's plates?"  → DB lookup + the registration document
"What's the GPS location of truck 5?"        → "I don't track that" (data doesn't exist)
```

---

## The problem

Trucking carriers run on paper. An active fleet generates 50+ documents every
week. Today it lives in filing cabinets, glove boxes, and email threads — nothing
is searchable, nothing is organized by truck. Operators can't answer basic
questions without digging through physical files: *Which trucks are profitable?
How much did I spend on parts last month? Where's the tax form for truck 84? What
documents do I need to renew these plates?*

FleetIQ turns that pile of paper into a question-answering system.

## How it works

```
                       ┌──────────────────────────┐
   operator question   │   CLASSIFY  (LLM router) │
   ──────────────────► │  sql / retrieval / hybrid│
                       └────────────┬─────────────┘
            ┌───────────────────────┼────────────────────────┐
            ▼                       ▼                         ▼
    ┌───────────────┐      ┌────────────────┐       ┌──────────────────┐
    │   SQL path    │      │ Retrieval path │       │   Hybrid path    │
    │ NL→SQL over   │      │ vector search  │       │  SQL + retrieval │
    │ fleet.db      │      │ over documents │       │  merged          │
    └───────┬───────┘      └───────┬────────┘       └────────┬─────────┘
            └───────────────────────┼─────────────────────────┘
                                    ▼
                       ┌─────────────────────────┐
                       │   GROUNDED SYNTHESIS     │
                       │  answer + citations +    │
                       │  "I don't have that"     │
                       └─────────────────────────┘
```

The agent is a small **LangGraph** state machine ([agent/graph.py](agent/graph.py)):

1. **Classify** — an LLM picks the route (`sql` / `retrieval` / `hybrid`) and
   extracts a `truck_id` if the question names one.
2. **Execute**
   - **SQL** — the LLM writes ONE read-only SQLite query (writes are blocked) and
     it's executed against the structured fleet DB. Errors are caught and
     translated into clean, non-leaky messages.
   - **Retrieval** — semantic search over the vector store, optionally scoped to
     a `truck_id` / `doc_type` via metadata filters.
   - **Hybrid** — runs both and merges the evidence.
3. **Ground** — a final LLM call answers **only** from the collected evidence,
   cites every source inline, and refuses to guess when evidence is missing.

### Why route per question?

A pure RAG chatbot answers "how much did I spend on parts?" by stuffing receipts
into context and hoping the model adds them up. FleetIQ sends that to **SQL** and
gets an exact number. It sends "show me the title for truck 6" to **retrieval**.
It sends "what's expiring and what do I need to renew it" to **both**. Routing is
what makes the answers *correct* instead of *plausible*.

## The dataset (synthetic, realistic, internally consistent)

`make data` generates ~1,000 documents for a 25-truck carrier across **13 document
types**, plus a structured backbone that the database and the documents both draw
from — so truck 4's VIN on its title matches truck 4's VIN on its Form 2290.

| Category            | Document types                                                                 |
|---------------------|--------------------------------------------------------------------------------|
| Vehicle / tax       | `vehicle_title`, `vehicle_registration`, `form_2290`, `ifta_return`            |
| Maintenance / safety| `repair_invoice`, `dot_inspection`, `roadside_inspection`                       |
| Operations          | `fuel_receipt`, `eld_log`, `bill_of_lading`, `rate_confirmation`, `proof_of_delivery` |
| Driver              | `medical_cert`                                                                 |

**Realistic messiness:** ~25% of field-collected documents (fuel receipts, PODs,
repair invoices, inspections) are rendered as **degraded scanned PNGs** — skew,
stains, handwriting — and must be read with **OCR (Tesseract)**. Clean office
documents are native PDFs read with `pdfplumber`. Frequencies are realistic too:
fuel receipts and logs are frequent; titles and 2290s are annual/rare — a genuine
retrieval challenge.

Every document is tagged to its `truck_id` / `driver_id` / `load_id` in
`manifest.json`, which is also the ground truth the evaluation grades against.

## Tech stack

- **Orchestration:** LangGraph
- **LLM:** pluggable — Groq (Llama 3.3, free), Anthropic Claude, or OpenAI; falls
  back to a rule-based mock if no key is set, so the graph always runs
- **Vector store:** Chroma with `sentence-transformers` (all-MiniLM-L6-v2)
  embeddings (deterministic hash-embedder fallback if offline)
- **Structured store:** SQLite
- **Ingestion:** pdfplumber (native PDF) + Tesseract OCR (scans)
- **API / UI:** FastAPI + a single-file HTML chat console that shows the route,
  the SQL, and the cited documents for every answer

---

## Quick start

### Prerequisites

- Python 3.10+
- **Tesseract OCR** and **Poppler** (system binaries for reading scanned docs):
  - macOS: `brew install tesseract poppler`
  - Debian/Ubuntu: `sudo apt-get install tesseract-ocr poppler-utils`

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Add an API key (free)

Copy the template and drop in a Groq key (free at
[console.groq.com/keys](https://console.groq.com/keys)):

```bash
cp .env.example .env
# edit .env -> GROQ_API_KEY=gsk_...
```

The `.env` is loaded automatically. With no key set, FleetIQ still runs end-to-end
on a rule-based mock LLM. Confirm routing with `python agent/llm.py`.

### 3. Build the data, database, and vector index

```bash
make build      # = generate docs -> build SQLite DB -> OCR + embed into Chroma
```

(First run downloads the embedding model and OCRs the scans — a couple of minutes.)

### 4. Run it

```bash
make serve      # web console at http://127.0.0.1:8000
```

…or from the CLI:

```bash
python -c "from agent.graph import answer; print(answer('Which trucks are profitable?')['answer'])"
```

> Using raw commands instead of `make`? See the [Makefile](Makefile) — every target
> is a one-line script (`python data/generate_docs.py`, `uvicorn ui.app:app …`, etc.).

---

## Evaluation

Most teams ship a RAG demo. FleetIQ ships a **measured** agent. The harness
([eval/run_eval.py](eval/run_eval.py)) runs a gold set of questions spanning all
three routes plus deliberate **grounding traps** (questions whose answer is *not*
in the data — the agent must refuse, not invent).

```bash
make eval
```

It scores:

- **Route accuracy** — did the classifier pick the right path?
- **Content accuracy** — does the answer contain the expected fact / citation /
  refusal?

Results are written to `eval/results.json` and printed as a scoreboard:

```
================================================
  FleetIQ Eval Scoreboard
================================================
  Route accuracy   : 16/20
  Content accuracy : 16/20
================================================
```

*(Representative run on Groq `llama-3.3-70b-versatile`. Exact numbers vary by LLM
provider and model. Note: Groq's free tier caps you at ~100K tokens/day — a full
ingest plus several eval runs can exhaust it, after which calls fall back to the
mock LLM and scores drop. Wait for the daily reset or use a paid tier/another
provider for a clean run.)*

The traps matter as much as the hits: when asked for a truck's GPS location or
live engine temperature — data this fleet doesn't track — the agent must answer
*"I don't have a record or document for that,"* never invent a number.

## Project structure

```
fleetiq/
├── agent/            # the hybrid agent (LangGraph)
│   ├── graph.py        classify → [sql | retrieval | hybrid] → ground
│   ├── llm.py          multi-provider LLM layer (Groq/Claude/OpenAI/mock)
│   └── mock_llm.py     rule-based fallback so the graph runs with no API key
├── data/             # Lane A — synthetic data generation
│   ├── fleet_backbone.py   single source of truth (trucks/drivers/trailers/loads)
│   ├── renderers.py        authentic-layout PDF renderers per document type
│   ├── messify.py          degrades a subset into realistic scanned PNGs
│   └── generate_docs.py    emits docs + manifest.json (ground truth)
├── db/
│   └── build_db.py     builds fleet.db; derives expenses from the documents
├── ingest/
│   └── pipeline.py     PDF text + OCR → chunk → embed → Chroma
├── retrieval/
│   └── search.py       search(query, k, truck_id, doc_type) → ranked docs
├── eval/
│   └── run_eval.py     gold-set scoreboard (route + content + traps)
├── ui/
│   ├── app.py          FastAPI: POST /ask returns the full agent trace
│   └── index.html      chat console showing route + SQL + citations
├── Makefile  ·  requirements.txt  ·  .env.example
```

## Design choices & honesty

- **Grounding is enforced at the prompt and the data layer.** The synthesis step
  is instructed to use only the supplied evidence; when a query references data
  the fleet doesn't track (e.g. GPS location), the SQL layer returns a clean
  "not tracked" note instead of leaking a raw database error.
- **DB and documents describe the same fleet.** Expenses are *derived* from the
  fuel/repair documents, so hybrid questions join cleanly across both sides.
- **Fails safe.** A bad key or rate limit falls back to the mock for that turn so
  a live demo never hard-crashes.

## Generalizes beyond trucking

The router + grounding engine is data-source agnostic. Swap the SQLite backbone
and document corpus and the same `classify → execute → ground` machine answers
hybrid questions over enterprise warehouses, manufacturing manuals, or any mix of
structured records and unstructured documents. Trucking is the demo, not the limit.

## License

[MIT](LICENSE)
