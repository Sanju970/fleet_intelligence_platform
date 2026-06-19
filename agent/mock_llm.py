"""
A rule-based mock LLM so the FULL graph runs end-to-end WITHOUT API keys.
Lets the team see SQL + retrieval + grounding working before wiring a real provider.
At the event: ignore this file, just point call_llm at Claude/Groq.

It pattern-matches the three system prompts (classify / sql / ground) and returns
plausible structured output. NOT smart — just proves the wiring.
"""
import re, json

def mock_call_llm(system: str, user: str) -> str:
    q = user.lower()
    # truck id extraction
    m = re.search(r"truck\s+#?(\d+)", q)
    tid = int(m.group(1)) if m else None

    if "route" in system and "json" in system.lower():
        doc_words = ["where", "show", "find", "copy", "document", "receipt", "form",
                     "title", "tax form", "certificate", "pull up", "invoice for"]
        sql_words = ["how many", "total", "which trucks", "average", "sum", "cost",
                     "spend", "spent", "profit", "expires", "due", "list"]
        is_doc = any(w in q for w in doc_words)
        is_sql = any(w in q for w in sql_words)
        if is_doc and is_sql: route = "hybrid"
        elif is_doc: route = "retrieval"
        elif is_sql: route = "sql"
        else: route = "hybrid"
        return json.dumps({"route": route, "truck_id": tid})

    if "sqlite query" in system.lower() or "select only" in system.lower():
        # crude NL->SQL for the common demo questions
        if "how many" in q and "active" in q:
            return "SELECT COUNT(*) AS active_trucks FROM trucks WHERE status='active'"
        if "fuel" in q and ("total" in q or "spend" in q or "spent" in q):
            if tid: return f"SELECT SUM(amount) AS fuel_total FROM expenses WHERE category='fuel' AND truck_id={tid}"
            return "SELECT SUM(amount) AS fuel_total FROM expenses WHERE category='fuel'"
        if ("parts" in q) and ("spend" in q or "spent" in q or "how much" in q):
            if tid: return f"SELECT SUM(amount) AS parts_total FROM expenses WHERE category='parts' AND truck_id={tid}"
            return "SELECT SUM(amount) AS parts_total FROM expenses WHERE category='parts'"
        if "registration" in q and ("expir" in q or "due" in q or "renew" in q):
            return "SELECT truck_id, plate, reg_expires FROM trucks WHERE reg_expires <= date('now','+30 day') ORDER BY reg_expires"
        if "profit" in q or "most expensive" in q or "highest" in q:
            return "SELECT truck_id, SUM(amount) AS total_cost FROM expenses GROUP BY truck_id ORDER BY total_cost DESC LIMIT 5"
        if "driver" in q and tid:
            return f"SELECT t.truck_id, d.name AS driver FROM trucks t JOIN drivers d ON t.driver_id=d.driver_id WHERE t.truck_id={tid}"
        if "maintenance" in q and "status" in q:
            return "SELECT COUNT(*) AS in_maintenance FROM trucks WHERE status='maintenance'"
        return "SELECT truck_id, unit, make, model, status FROM trucks LIMIT 10"

    # ground: summarize the evidence JSON plainly with citations
    if "answer only from the evidence" in system.lower():
        try:
            ev = json.loads(user.split("Evidence:",1)[1])
        except Exception:
            return "I don't have a record or document for that."
        parts = []
        rows = ev.get("sql_rows")
        if rows and not (len(rows)==1 and "error" in rows[0]):
            parts.append("From fleet records [DB]: " + json.dumps(rows[:5], default=str))
        docs = ev.get("documents")
        if docs:
            cites = ", ".join(f"[{d['file']}]" for d in docs[:3])
            parts.append(f"Relevant documents: {cites}")
        if not parts:
            return "I don't have a record or document for that."
        return "  ".join(parts)
    return ""
