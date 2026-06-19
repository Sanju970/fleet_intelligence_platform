"""Unit tests for the rule-based fallback LLM (the offline brain)."""
import json
from agent.mock_llm import mock_call_llm

CLASSIFY_SYS = 'Output JSON only route'
SQL_SYS = 'Write ONE safe read-only SQLite query. SELECT only.'
GROUND_SYS = 'Answer ONLY from the evidence below.'


def _route(q):
    return json.loads(mock_call_llm(CLASSIFY_SYS, q))


def test_classify_routes():
    assert _route("how many trucks are active?")["route"] == "sql"
    assert _route("show me the title for truck 3")["route"] == "retrieval"
    assert _route("what's expiring soon and what document do I need to renew it?")["route"] == "hybrid"


def test_classify_telemetry_is_sql_and_unscoped_zero():
    r = _route("what's the gps location of truck 5 right now?")
    assert r["route"] == "sql"
    assert r["truck_id"] == 5


def test_sql_is_select_only():
    for q in ["which trucks are profitable?", "how much did I spend on parts last month?",
              "how many trucks are active?", "average expense per truck"]:
        sql = mock_call_llm(SQL_SYS, q).upper()
        assert sql.lstrip().startswith("SELECT")
        for bad in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]:
            assert bad not in sql


def test_sql_profit_uses_revenue_minus_cost():
    sql = mock_call_llm(SQL_SYS, "which trucks are profitable?").lower()
    assert "loads" in sql and "expenses" in sql and "profit" in sql


def test_sql_telemetry_targets_missing_column():
    sql = mock_call_llm(SQL_SYS, "engine temperature of truck 2 right now?").lower()
    # selects a column that doesn't exist on `trucks` -> triggers the refusal path
    real_cols = {"truck_id", "unit", "make", "model", "year", "vin", "plate", "state",
                 "driver_id", "trailer_id", "status", "odometer", "reg_expires", "gvw",
                 "fuel", "color", "lienholder"}
    selected = sql.split("select", 1)[1].split("from")[0].strip()
    assert selected not in real_cols


def test_ground_formats_money_and_cites():
    ev = {"sql_rows": [{"fuel_total": 12480.5}]}
    out = mock_call_llm(GROUND_SYS, "Question: fuel?\n\nEvidence:\n" + json.dumps(ev))
    assert "$12,480.50" in out and "DB" in out


def test_ground_refuses_on_note():
    ev = {"sql_rows": [{"note": "not tracked in this dataset"}]}
    out = mock_call_llm(GROUND_SYS, "Question: gps?\n\nEvidence:\n" + json.dumps(ev))
    assert "don't have" in out.lower()
