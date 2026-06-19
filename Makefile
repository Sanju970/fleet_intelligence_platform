# FleetIQ — common tasks. Run `make help` for the list.
PY ?= python

.PHONY: help install data db ingest build serve eval demo test clean reset

help:
	@echo "FleetIQ make targets:"
	@echo "  make install   Install Python dependencies"
	@echo "  make build     Full pipeline: generate docs -> build DB -> ingest vectors"
	@echo "  make data      Generate synthetic fleet documents + manifest"
	@echo "  make db        Build the structured SQLite database"
	@echo "  make ingest    OCR + embed documents into the Chroma vector store"
	@echo "  make serve     Run the web app at http://127.0.0.1:8000"
	@echo "  make eval      Run the gold-set evaluation scoreboard"
	@echo "  make demo      Ask one sample question from the CLI"
	@echo "  make reset     Delete generated data/DB/vectors"

install:
	$(PY) -m pip install -r requirements.txt

data:
	$(PY) data/generate_docs.py

db:
	$(PY) db/build_db.py

ingest:
	$(PY) ingest/pipeline.py

build: data db ingest
	@echo "Build complete. Run 'make serve' or 'make eval'."

serve:
	uvicorn ui.app:app --host 127.0.0.1 --port 8000

eval:
	$(PY) eval/run_eval.py

test:
	$(PY) -m pytest -q

demo:
	$(PY) -c "from agent.graph import answer; import json; print(json.dumps(answer('Which trucks are profitable?'), indent=2, default=str))"

reset:
	rm -rf data/docs data/manifest.json data/fleet_structured.json db/fleet.db db/chroma eval/results.json
	@echo "Reset done. Run 'make build' to regenerate."
