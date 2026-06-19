"""Unit tests for the agent graph — no live LLM required (we monkeypatch call_llm)."""
import sqlite3
import agent.graph as G


def test_graph_compiles():
    assert G.build_graph() is not None


def test_sql_node_blocks_writes(monkeypatch):
    monkeypatch.setattr(G, "call_llm", lambda *a, **k: "DROP TABLE trucks;")
    state = {"question": "delete everything"}
    out = G.sql_node(state)
    assert out["sql_rows"] == [{"error": "unsafe query blocked"}]


def test_friendly_error_hides_sql_internals():
    msg = G._friendly_sql_error(sqlite3.OperationalError("no such column: location"))
    assert "location" in msg                 # tells the user what isn't tracked
    assert "no such column" not in msg.lower()  # but never leaks the raw SQL error


def test_classify_rejects_truck_id_zero(monkeypatch):
    import json
    monkeypatch.setattr(G, "call_llm",
                        lambda *a, **k: json.dumps({"route": "sql", "truck_id": 0}))
    out = G.classify({"question": "which trucks are profitable?"})
    assert out["truck_id"] is None           # 0 is never a real truck -> no scope
    assert out["route"] == "sql"


def test_classify_keeps_positive_truck_id(monkeypatch):
    import json
    monkeypatch.setattr(G, "call_llm",
                        lambda *a, **k: json.dumps({"route": "retrieval", "truck_id": 7}))
    out = G.classify({"question": "title for truck 7"})
    assert out["truck_id"] == 7


def test_retrieval_failure_does_not_crash(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("Vector DB not found.")
    monkeypatch.setattr(G, "doc_search", boom)
    out = G.retr_node({"question": "show me a title", "truck_id": None})
    assert out["docs"] == []                  # degrades instead of raising
    assert "note" in out and "unavailable" in out["note"].lower()
