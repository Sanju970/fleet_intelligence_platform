"""Retrieval tests over the Chroma vector store. Skipped until `make ingest` has run."""
import os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA = os.path.join(ROOT, "db", "chroma")

pytestmark = pytest.mark.skipif(
    not os.path.exists(CHROMA),
    reason="vector store not built — run `python ingest/pipeline.py` first",
)


def test_search_returns_results():
    from retrieval.search import search
    hits = search("repair invoice brake job", k=3)
    assert hits and all("file" in h and "score" in h for h in hits)


def test_truck_scoping_filters_by_truck():
    from retrieval.search import search
    hits = search("vehicle certificate of title", k=5, truck_id=3)
    assert hits, "expected truck 3 to have documents"
    assert all(h["truck_id"] == 3 for h in hits)


def test_doc_type_filter():
    from retrieval.search import search
    hits = search("heavy highway vehicle use tax", k=3, doc_type="form_2290")
    assert hits and all(h["doc_type"] == "form_2290" for h in hits)
