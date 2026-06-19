"""
Lane C — The LangGraph hybrid agent. THE CORE.

    question -> classify -> [sql | retrieval | hybrid] -> ground -> answer

Nodes:
  classify   : LLM decides route (sql / retrieval / hybrid) + extracts truck_id
  sql_node   : LLM writes a safe read-only query over the fleet DB, executes it
  retr_node  : calls Lane B retrieval (optionally scoped to truck_id / doc_type)
  hybrid_node: runs BOTH, merges evidence
  ground     : LLM writes the final answer ONLY from evidence, with citations,
               and says "I don't have that" when evidence is missing.

Wire call_llm() to your provider abstraction (Claude/Groq/etc). Everything else runs.
"""
import os, sys, json, sqlite3
from typing import TypedDict, Optional, List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langgraph.graph import StateGraph, END
from retrieval.search import search as doc_search

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "db", "fleet.db")

SCHEMA = """trucks(truck_id, unit, make, model, year, vin, plate, state, driver_id, trailer_id, status, odometer, reg_expires, gvw, fuel, color, lienholder)
drivers(driver_id, name, cdl, cdl_state, phone, dob, med_cert_expires, hire_date)
trailers(trailer_id, type, plate, vin, year)
loads(load_id, truck_id, driver_name, origin, dest, miles, rate, broker, commodity, weight, ship_date)   -- rate = revenue ($) earned for that load
expenses(id, truck_id, category, vendor, amount, date, source_doc)   -- category: fuel|parts|maintenance|tires|fines ; amount in $ ; date is YYYY-MM-DD
registrations(truck_id, plate, expires, state)   -- expires is YYYY-MM-DD"""

# ============ LLM HOOK — replace with your provider abstraction ============
from agent.llm import llm as _llm

def call_llm(system: str, user: str, role: str = "ground") -> str:
    """Role-aware multi-provider call. role: classify | sql | ground.
    Uses Groq/Claude/OpenAI based on env keys; falls back to mock if none set."""
    return _llm(system, user, role=role)
# ===========================================================================

class State(TypedDict):
    question: str
    route: Optional[str]
    truck_id: Optional[int]
    sql: Optional[str]
    sql_rows: Optional[list]
    docs: Optional[list]
    answer: Optional[str]

# ---------- classify ----------
CLASSIFY_SYS = """You route fleet-operator questions. Output JSON only:
{"route":"sql"|"retrieval"|"hybrid","truck_id":<int or null>}
- sql: counts, totals, filters, "which trucks", costs, due dates, profitability (structured data)
- retrieval: find/show/quote a specific document (a receipt, title, tax form, the actual paper)
- hybrid: needs a DB lookup AND a document together — e.g. "what's expiring AND what doc do I
  need to renew it", or asking for the document/status of a truck identified by a DB superlative
  ("the most expensive truck", "the highest-mileage truck").
Extract truck_id ONLY if the question names a specific truck number; otherwise use null
(never 0 — no truck is numbered 0)."""

def classify(state: State) -> State:
    raw = call_llm(CLASSIFY_SYS, state["question"], role="classify")
    try:
        j = json.loads(raw)
        state["route"] = j.get("route", "hybrid")
        tid = j.get("truck_id")
        # guard: only keep a positive integer truck id; 0/negative/garbage -> no scope
        state["truck_id"] = int(tid) if isinstance(tid, int) and tid > 0 else None
    except Exception:
        state["route"] = "hybrid"; state["truck_id"] = None
    return state

# ---------- sql ----------
SQL_SYS = f"""Write ONE safe read-only SQLite query answering the question.
Schema:
{SCHEMA}

Domain hints (SQLite syntax):
- Revenue/income for a truck = SUM(loads.rate) for that truck_id.
- Cost/spend for a truck = SUM(expenses.amount) for that truck_id.
- Profit / "is it profitable" = revenue - cost, e.g.
    SELECT t.truck_id,
           COALESCE((SELECT SUM(rate)   FROM loads    WHERE truck_id=t.truck_id),0) -
           COALESCE((SELECT SUM(amount) FROM expenses WHERE truck_id=t.truck_id),0) AS profit
    FROM trucks t ORDER BY profit DESC;
- "last month" = date BETWEEN date('now','start of month','-1 month') AND date('now','start of month','-1 day').
- "expiring soon / next N days" = expires BETWEEN date('now') AND date('now','+N days').
- Spend on a category (e.g. parts) = SUM(amount) WHERE category='parts'.

Rules: SELECT only. No DROP/DELETE/UPDATE/INSERT/ALTER. Output only the SQL, no prose."""

def _friendly_sql_error(e: Exception) -> str:
    """Turn a raw SQLite error into a clean message that doesn't leak SQL internals.
    Most common case here: the question asks for data the fleet DB doesn't track
    (e.g. GPS 'location'), which sqlite reports as 'no such column/table'."""
    msg = str(e)
    low = msg.lower()
    if "no such column" in low:
        field = msg.split("no such column:")[-1].strip().split(".")[-1]
        return (f"The fleet database doesn't track a '{field}' field, "
                "so that information isn't available in this dataset.")
    if "no such table" in low:
        return ("That kind of record isn't kept in the fleet database, "
                "so that information isn't available in this dataset.")
    # anything else: stay generic, never surface raw SQL/driver text
    return ("That request couldn't be answered from the fleet database "
            "(the data may not be tracked in this dataset).")

def sql_node(state: State) -> State:
    sql = call_llm(SQL_SYS, state["question"], role="sql").strip().strip("`").replace("sql\n", "")
    low = sql.lower()
    if any(k in low for k in ["drop","delete","update","insert","alter",";--"]):
        state["sql"] = sql; state["sql_rows"] = [{"error": "unsafe query blocked"}]; return state
    con = sqlite3.connect(DB)
    try:
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()[:50]]
        state["sql"] = sql; state["sql_rows"] = rows
    except Exception as e:
        state["sql"] = sql; state["sql_rows"] = [{"note": _friendly_sql_error(e)}]
    finally:
        con.close()
    return state

# ---------- retrieval ----------
def retr_node(state: State) -> State:
    state["docs"] = doc_search(state["question"], k=4, truck_id=state.get("truck_id"))
    return state

# ---------- hybrid ----------
def hybrid_node(state: State) -> State:
    sql_node(state)
    retr_node(state)
    return state

# ---------- ground ----------
GROUND_SYS = """Answer ONLY from the evidence below. Cite sources inline: [truck N / DB] for
database rows, [filename] for documents. Report money with a $ and group thousands
(e.g. $12,480.00); keep units (gal, mi, lbs) where the evidence has them. If the evidence
doesn't contain the answer, say "I don't have a record or document for that." Never use
outside knowledge or guess. Be concise and operator-friendly."""

def ground(state: State) -> State:
    ev = {}
    if state.get("sql_rows") is not None:
        ev["sql_query"] = state.get("sql"); ev["sql_rows"] = state["sql_rows"]
    if state.get("docs") is not None:
        ev["documents"] = [{"file": d["file"], "truck_id": d["truck_id"],
                            "doc_type": d["doc_type"], "excerpt": d["text"][:300]}
                           for d in state["docs"]]
    state["answer"] = call_llm(GROUND_SYS, f"Question: {state['question']}\n\nEvidence:\n{json.dumps(ev, default=str, indent=2)}", role="ground")
    return state

# ---------- build graph ----------
def route_selector(state: State) -> str:
    return state["route"]

def build_graph():
    g = StateGraph(State)
    g.add_node("classify", classify)
    g.add_node("sql", sql_node)
    g.add_node("retrieval", retr_node)
    g.add_node("hybrid", hybrid_node)
    g.add_node("ground", ground)
    g.set_entry_point("classify")
    g.add_conditional_edges("classify", route_selector,
                            {"sql": "sql", "retrieval": "retrieval", "hybrid": "hybrid"})
    for n in ["sql", "retrieval", "hybrid"]:
        g.add_edge(n, "ground")
    g.add_edge("ground", END)
    return g.compile()

AGENT = None
def answer(question: str) -> Dict[str, Any]:
    global AGENT
    if AGENT is None: AGENT = build_graph()
    final = AGENT.invoke({"question": question})
    return {"question": question, "route": final.get("route"),
            "truck_id": final.get("truck_id"), "sql": final.get("sql"),
            "n_docs": len(final.get("docs") or []), "answer": final.get("answer")}

if __name__ == "__main__":
    # graph builds without a live LLM; this just verifies wiring
    g = build_graph()
    print("LangGraph compiled OK. Nodes: classify -> [sql|retrieval|hybrid] -> ground")
    print("Wire call_llm() then: from agent.graph import answer")
