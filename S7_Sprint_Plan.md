# Buildathon Dallas — S7 Sprint Plan
## Fleet Document Q&A System

**Track:** RAG & Retrieval (with Agent Orchestration + Data Pipelines elements)
**Team size:** 4
**Duration:** 18 hours
**Stack:** FastAPI · LangChain · ChromaDB · SQLite · Featherless (inference) · Tavily (web enrichment) · Lovable (UI)

---

## The problem

Trucking carriers run on paper. An active fleet generates 50+ documents every week — titles, tax forms, fuel records, registration renewals, maintenance receipts — living in filing cabinets, glove boxes, and email threads. Nothing is searchable, nothing is organized by truck.

Operators can't answer basic questions without digging through physical files: *Which trucks are profitable? How much did I spend on parts last month? Where's the tax form for truck 84? What documents do I need to renew these plates?*

## What we're building

A system that ingests every fleet document, links each one to the correct truck/driver/trailer, and lets an operator ask any question in plain English. Some questions need a database query, some need document retrieval, some need both — the system routes intelligently and answers accurately, grounded, with no hallucinations.

## Why we win this one

- **Low competition.** Operationally real but visually unglamorous, so few teams pick it. Expect 1–2 competitors.
- **We already have the stack.** This is the Research Paper Q&A Engine rebuilt for a new domain — LangChain + ChromaDB + entity extraction + hybrid retrieval, all previously built.
- **Hybrid RAG + SQL is rare** at hackathons and exactly what the problem demands.
- **Resources remove the bottlenecks.** Lovable kills the frontend bottleneck, Featherless makes inference free, Tavily adds a surprise web-fallback feature.

---

## Architecture

```
Documents (PDFs)
      |
      v
  INGEST PIPELINE
  - PyMuPDF text extraction + chunking
  - Featherless entity extraction (truck_id, doc_type, date, amount, driver)
      |
      +----------------------------+
      v                            v
  SQLite                       ChromaDB
  (structured fields,          (full-text chunks,
   truck linkage)               semantic search)
      |                            |
      +-------------+--------------+
                    v
              QUERY ROUTER
        classifies each question:
        SQL_ONLY | VECTOR_ONLY | HYBRID
                    |
          (fallback: Tavily web search
           for compliance/regulation Qs)
                    v
        Grounded answer + cited sources
                    v
        LOVABLE UI (operator dashboard)
```

---

## Team roles (4 people)

| Role | Owner | Responsibility |
|------|-------|----------------|
| **BE-1 · Ingest** | _assign_ | PDF extraction, LLM entity extraction, SQLite schema + truck linkage, `/ingest` endpoint |
| **BE-2 · Retrieval** | _assign_ | ChromaDB + embeddings, query classifier, SQL/vector/hybrid paths, Tavily tool, `/query` endpoint |
| **FE · Lovable** | _assign_ | Lovable scaffold (starts H2 on mocked API), Q&A + sources UI, truck explorer, upload, route badges, polish |
| **Lead · Sanket** | Sanket | Synthetic docs (early), float/integrate/unblock both BE tracks, demo questions + script, pitch narrative + Q&A prep |

**The linchpin:** lock the API contract for `/query` and `/ingest` at H2. Once the request/response JSON is fixed, all four people work in parallel without blocking each other.

---

## Parallel execution map

| | H0–2 | H2–6 | H6–10 | H10–14 | H14–16 | H16–18 |
|---|---|---|---|---|---|---|
| **BE-1 Ingest** | Setup + FastAPI skeleton | Extraction + SQLite pipeline | `/ingest` + entity linkage | Support hybrid + tune extraction | Edge cases + guardrail | Q&A prep |
| **BE-2 Retrieval** | Featherless smoke test + Chroma setup | Embeddings + vector search | Query router + 3 paths + `/query` | Tavily fallback + response schema | Anti-hallucination + latency | Q&A prep |
| **FE Lovable** | Plan UI, wait for skeleton | Scaffold UI on mocked API | Q&A + sources + truck panel | Wire real API + upload + chips | Route badges + responsive polish | Drive demo UI |
| **Sanket Lead** | Synthetic docs + architecture | Finish docs + define demo Qs | Float / integrate / unblock | E2E testing + demo script | Integration test + buffer | Pitch + rehearse ×2 |

---

## Phase 1 — Foundation & data setup (H0–H2)

**Goal:** Repo initialized, synthetic documents generated, FastAPI skeleton running, Featherless + Tavily keys confirmed. Everyone can run the project locally by H2.

- **Kickoff + architecture alignment** (30 min, ALL) — Whiteboard the system, assign owners, create shared GitHub repo. **Lock the API contract here.**
- **Generate synthetic fleet documents** (45 min, Sanket) — 30–40 realistic synthetic PDFs: maintenance receipts, fuel records, titles, registrations, tax forms. Name them realistically (`truck_84_title.pdf`). Messiness = realism.
- **FastAPI skeleton + env setup** (30 min, BE-1) — Init FastAPI, wire `.env` with `FEATHERLESS_API_KEY` + `TAVILY_API_KEY`, placeholder endpoints. Install langchain, chromadb, fastapi, pymupdf, tavily-python.
- **Featherless smoke test** (15 min, BE-2) — Confirm `mistralai/Mistral-7B-Instruct-v0.3` responds via `api.featherless.ai/v1`. Set as default model.

> **Milestone:** Repo live, docs ready, API skeleton running, all keys green.

---

## Phase 2 — Ingest pipeline (H2–H6)

**Goal:** A working pipeline that reads any PDF, extracts entities, stores structured fields in SQLite and full text in ChromaDB. The hardest technical work of the sprint — run BE-1 and BE-2 in parallel.

**BE-1 (ingest track):**
- **PDF text extraction + chunking** (45 min) — PyMuPDF to extract text. Chunk into 400-token segments, 50-token overlap. Tag each chunk with source filename. Flag scanned/image PDFs rather than crash.
- **LLM entity extraction per document** (75 min) — Featherless structured extraction prompt → JSON (`truck_id`, `driver_name`, `trailer_id`, `doc_type`, `date`, `amount`). Store in SQLite: `documents(id, truck_id, driver_name, doc_type, date, amount_usd, source_file, raw_text)`. **This is the linkage layer.**
- **`/ingest` endpoint** (30 min) — Accept files/folder → extraction → store to SQLite + Chroma → return summary.

**BE-2 (retrieval track):**
- **Vector embedding + ChromaDB storage** (45 min) — Embed chunks with `all-MiniLM-L6-v2` (free, local, fast). Store in Chroma with metadata `{truck_id, doc_type, date, source_file}`.
- **Tavily enrichment tool** (45 min) — LangChain tool `enrich_entity(entity_type, value)` → web context for VINs, parts, recalls, regulations. The "wow" feature judges won't expect.

> **Milestone:** All ~35 docs ingested, entities linked, Chroma + SQLite both populated.

---

## Phase 3 — Query router + answer engine (H6–H10)

**Goal:** A working router that classifies any plain-English question, hits the right data source, and returns a grounded answer with cited sources. This is what judges probe hardest. Primarily BE-2, with BE-1 supporting the hybrid path.

- **Query classifier** (45 min, BE-2) — Featherless prompt returns `SQL_ONLY` / `VECTOR_ONLY` / `HYBRID`. Keep it simple — no complex routing logic.
- **SQL answer path** (60 min, BE-2) — Featherless generates SQLite query from question + schema → execute → generate NL answer. Guard: reject + retry once if generated SQL touches nonexistent tables/columns.
- **Vector answer path** (45 min, BE-2) — Embed question → top-5 Chroma chunks → answer with Featherless → return answer + sources (filename, doc_type, truck_id). **Sources are non-negotiable.**
- **Hybrid path + Tavily fallback** (60 min, BE-2 + BE-1) — Run SQL + vector in parallel (`asyncio.gather`), merge context, unified answer. Tavily fallback when neither is confident (e.g. "what docs to renew plates in Texas?").
- **`/query` endpoint + response schema** (30 min, BE-2) — Response: `{answer, route_used: 'sql'|'vector'|'hybrid'|'tavily', sources: [...], sql_used?}`. The `route_used` field shows judges how the system thinks.

> **Milestone:** Core system works end-to-end. Ask any question, get a grounded answer with sources.

---

## Phase 4 — Lovable UI build (H10–H14)

**Goal:** A production-quality operator dashboard, done in 4 hours, looks like 4 days. (FE has been scaffolding on mocked data since H2, so this is mostly wiring + polish.)

- **Lovable project init + API wiring** (30 min) — Set FastAPI backend URL, fetch wrapper for `/query`, `/trucks`, `/documents`.
- **Main Q&A interface** (60 min) — Prompt Lovable: *"Clean operator dashboard with a prominent search bar, answer panel below, sources panel with document cards (filename, truck ID, doc type, date), and a route indicator badge showing SQL / Vector / Hybrid / Web."* The demo centerpiece.
- **Truck explorer panel** (45 min) — Sidebar list of trucks → click shows all linked documents in a table + total spend metric card.
- **Document browser + upload** (45 min) — Documents tab, searchable/filterable table, Upload button POSTing to `/ingest` with progress. Critical for the live demo.
- **Demo queries as chips** (30 min) — 5–6 clickable question chips: *"Which trucks are most profitable?"*, *"Where is the tax form for truck 84?"*, *"How much did I spend on parts last month?"*, *"What documents do I need to renew these plates?"*, *"Show all maintenance records from March."* Makes the demo foolproof.
- **Mobile responsive + polish** (30 min) — Responsive layout, loading spinners on async calls, dark mode if time permits.

> **Milestone:** Full working UI. Any judge can click a chip and see a real answer with sources in under 3 seconds.

---

## Phase 5 — Integration, edge cases & hardening (H14–H16)

**Goal:** Handles edge cases gracefully, never crashes during a live demo, answers the 6 most likely judge questions correctly. Hold any freed time here as buffer.

- **End-to-end integration test** (45 min, ALL) — Run all 6 demo questions through the full stack. Fix broken paths. If any query >8s, add streaming or a progress indicator.
- **Edge case handling** (45 min, BE-1) — Nonexistent truck → graceful "no data found". Ambiguous question → ask for clarification. Missing doc → clear "document not found". Malformed PDF → skip with error log, don't crash. No silent failures.
- **Anti-hallucination guardrail** (30 min, BE-2) — If an answer contains a truck_id or dollar amount not in retrieved sources, flag with a yellow badge: *"This answer may not be fully grounded — verify with source documents."* Judges will probe for this.

> **Milestone:** System is demo-safe. No crashes, no silent hallucinations, all edge cases handled.

---

## Phase 6 — Pitch prep + final polish (H16–H18)

**Goal:** A rehearsed 4-minute demo, a sharp narrative, a team that can answer any technical question.

- **Pitch narrative — 2 slides max** (30 min, Sanket) — Slide 1: the problem. Slide 2: the solution (30-second architecture diagram). The demo IS the pitch.
- **Demo script — 4 minutes** (20 min, ALL):
  1. Show a messy pile of synthetic docs *(15s)*
  2. Upload one live *(30s)*
  3. Ask "where is truck 84's tax form?" — show sources *(45s)*
  4. Ask "how much did I spend on maintenance last month?" — show SQL path *(45s)*
  5. Ask "what docs do I need to renew plates?" — show Tavily web fallback *(45s)*
  6. Show truck explorer panel *(30s)*

  Total ~3.5 min, 30s buffer.
- **2× full rehearsal** (40 min, ALL) — Once clean, once on throttled 3G (DevTools). One speaker, one driver, one live-fixer.
- **Judge Q&A prep** (30 min, ALL) — Prepare answers:
  - *How does it handle hallucinations?* → show the confidence flag
  - *Scanned/non-OCR docs?* → flag gracefully
  - *SQL vs vector decision?* → show route_used badge
  - *Latency?* → under 4s average
  - *How would you scale?* → SQLite → Postgres, Chroma → Pinecone

> **Final milestone:** Team ready, system live, demo rehearsed. Ship it.

---

## Key technical decisions

- **Model:** `mistralai/Mistral-7B-Instruct-v0.3` via Featherless for extraction, classification, and generation. Free, fast enough.
- **Embeddings:** `all-MiniLM-L6-v2` — local, free, no API cost.
- **The `route_used` badge is the most important UI element.** When a judge asks "how does it know whether to use SQL or search?", you click a chip and the badge answers for you. That's the difference between "interesting demo" and "they actually built it."
- **Tavily web fallback is the surprise punch.** For "what documents to renew plates in Texas?", no internal doc has the answer — Tavily fetches it live, answer comes back with a `WEB` badge. Judges won't expect it.

## Risks to watch

- **Entity extraction quality** on messy PDFs — prompt quality matters more than model size. Keep the schema tight.
- **Don't over-extract.** Five fields (`truck_id`, `doc_type`, `date`, `amount_usd`, `driver_name`) beats fifteen.
- **Latency** on hybrid queries — run SQL + vector in parallel, never sequentially.
- **Integration at H8** is the highest-risk moment — the API contract from H2 is what de-risks it.

---

## Resource setup checklist

- [ ] Featherless — `BUILDATHON26` promo, API key from profile → API Keys, base URL `https://api.featherless.ai/v1`
- [ ] Tavily — free account at app.tavily.com, `TAVILY_API_KEY=tvly-...`, `pip install tavily-python`
- [ ] Lovable — Pro Plan 1 via code `COMM-DATHON-9535` at lovable.dev
- [ ] Shared GitHub repo created, everyone has push access
- [ ] `.env` template shared with all key names (not values) committed
