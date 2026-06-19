"""
Rule-based mock LLM so the FULL graph runs end-to-end WITHOUT API keys (or when a
real provider is rate-limited). It is NOT a language model — it pattern-matches the
three system prompts (classify / sql / ground) and returns plausible, *grounded*
output for the common families of fleet questions.

It exists so the system always works offline and degrades gracefully. A real
provider (Groq/Claude/OpenAI) is far more fluent and general; wire one via .env.
"""
import re, json

# ---------------------------------------------------------------- helpers
def _truck_id(q):
    m = re.search(r"truck\s+#?(\d+)", q)
    return int(m.group(1)) if m else None

def _money(v):
    try:
        return "${:,.2f}".format(float(v))
    except (TypeError, ValueError):
        return str(v)

# ---------------------------------------------------------------- classify
DOC_WORDS = ["where", "show", "find", "copy", "document", "receipt", "form", "title",
             "tax form", "2290", "certificate", "lien", "pull up", "pull the",
             "invoice for", "registration document", "the paper", "scan"]
SQL_WORDS = ["how many", "total", "which truck", "average", "avg", "sum", "count",
             "cost", "spend", "spent", "profit", "profitable", "revenue", "expires",
             "expiring", "due", "list", "highest", "lowest", "most", "cheapest",
             "per truck", "status"]
HYBRID_HINTS = ["renew", "and what document", "and which document", "what do i need to",
                "expiring soon and", "most expensive truck", "highest-mileage",
                "and is there", "and show", "explaining it"]

# Live-telemetry concepts this static dataset does NOT track -> must refuse, not invent.
# Maps a phrase in the question to the (non-existent) column the SQL would need, so the
# query hits the friendly "not tracked" error path just like a real model would.
TELEMETRY = {
    "gps": "location", "location": "location", "coordinate": "location",
    "temperature": "temperature", "tire pressure": "tire_pressure",
    "fuel level": "fuel_level", "engine": "engine_temp", "speed": "speed",
}

def _telemetry_col(q):
    return next((col for phrase, col in TELEMETRY.items() if phrase in q), None)

def _classify(q):
    if _telemetry_col(q):
        return json.dumps({"route": "sql", "truck_id": _truck_id(q) or None})
    is_doc = any(w in q for w in DOC_WORDS)
    is_sql = any(w in q for w in SQL_WORDS)
    if any(h in q for h in HYBRID_HINTS) or (is_doc and is_sql):
        route = "hybrid"
    elif is_doc:
        route = "retrieval"
    elif is_sql:
        route = "sql"
    else:
        route = "hybrid"
    tid = _truck_id(q)
    return json.dumps({"route": route, "truck_id": tid if (tid and tid > 0) else None})

# ---------------------------------------------------------------- NL -> SQL
LAST_MONTH = ("date BETWEEN date('now','start of month','-1 month') "
              "AND date('now','start of month','-1 day')")

def _to_sql(q):
    tid = _truck_id(q)
    # live telemetry isn't in the schema: reference the missing column on purpose so the
    # SQL layer returns its clean "not tracked" note and the agent refuses to invent data.
    tcol = _telemetry_col(q)
    if tcol:
        return f"SELECT {tcol} FROM trucks WHERE truck_id={tid or 1}"
    cat = next((c for c in ["fuel", "parts", "maintenance", "tires", "fines"] if c in q), None)

    # profitability = revenue (loads.rate) - cost (expenses.amount)
    if "profit" in q or "profitable" in q:
        return ("SELECT t.truck_id, "
                "COALESCE((SELECT SUM(rate) FROM loads WHERE truck_id=t.truck_id),0) - "
                "COALESCE((SELECT SUM(amount) FROM expenses WHERE truck_id=t.truck_id),0) AS profit "
                "FROM trucks t ORDER BY profit DESC")
    # most expensive / highest cost truck
    if ("most expensive" in q or "highest" in q) and ("truck" in q or "cost" in q or "spend" in q):
        return ("SELECT truck_id, SUM(amount) AS total_cost FROM expenses "
                "GROUP BY truck_id ORDER BY total_cost DESC LIMIT 5")
    # active trucks
    if "how many" in q and "active" in q:
        return "SELECT COUNT(*) AS active_trucks FROM trucks WHERE status='active'"
    # maintenance status count
    if "maintenance" in q and "status" in q:
        return "SELECT COUNT(*) AS in_maintenance FROM trucks WHERE status='maintenance'"
    # category spend (optionally per-truck, optionally last month)
    if cat and ("spend" in q or "spent" in q or "how much" in q or "total" in q):
        where = [f"category='{cat}'"]
        if tid: where.append(f"truck_id={tid}")
        if "last month" in q: where.append(LAST_MONTH)
        return f"SELECT SUM(amount) AS {cat}_total FROM expenses WHERE " + " AND ".join(where)
    # average expense per truck
    if ("average" in q or "avg" in q) and ("expense" in q or "spend" in q or "cost" in q):
        return ("SELECT AVG(total) AS avg_per_truck FROM "
                "(SELECT truck_id, SUM(amount) AS total FROM expenses GROUP BY truck_id)")
    # registration expiring
    if "registration" in q and ("expir" in q or "due" in q or "renew" in q):
        return ("SELECT truck_id, plate, expires FROM registrations "
                "WHERE expires <= date('now','+30 day') ORDER BY expires")
    # driver of a truck
    if "driver" in q and tid:
        return (f"SELECT t.truck_id, d.name AS driver FROM trucks t "
                f"JOIN drivers d ON t.driver_id=d.driver_id WHERE t.truck_id={tid}")
    # generic total spend
    if ("total" in q or "spend" in q or "spent" in q) and "fuel" not in q:
        if tid: return f"SELECT SUM(amount) AS total_spend FROM expenses WHERE truck_id={tid}"
        return "SELECT SUM(amount) AS total_spend FROM expenses"
    # fallback: a small fleet listing
    return "SELECT truck_id, unit, make, model, status FROM trucks LIMIT 10"

# ---------------------------------------------------------------- grounding
def _looks_unavailable(rows):
    return bool(rows) and len(rows) == 1 and isinstance(rows[0], dict) and \
        ("error" in rows[0] or "note" in rows[0])

def _format_rows(rows):
    """Render SQL rows into a short, operator-readable string."""
    if not rows:
        return None
    # single scalar (e.g. a count or a sum)
    if len(rows) == 1 and len(rows[0]) == 1:
        k, v = next(iter(rows[0].items()))
        label = k.replace("_", " ")
        if any(t in k for t in ["total", "spend", "cost", "profit", "amount", "avg", "average"]):
            return f"{label}: {_money(v)}"
        return f"{label}: {v}"
    # a handful of rows -> compact lines
    lines = []
    for r in rows[:5]:
        parts = []
        for k, v in r.items():
            if any(t in k for t in ["total", "cost", "profit", "amount", "rate", "spend"]):
                v = _money(v)
            parts.append(f"{k}={v}")
        lines.append("  - " + ", ".join(parts))
    more = "" if len(rows) <= 5 else f"\n  …and {len(rows)-5} more"
    return "\n".join(lines) + more

def _ground(user):
    try:
        ev = json.loads(user.split("Evidence:", 1)[1])
    except Exception:
        return "I don't have a record or document for that."

    rows = ev.get("sql_rows")
    docs = ev.get("documents")
    parts = []

    if rows is not None and not _looks_unavailable(rows):
        body = _format_rows(rows)
        if body:
            parts.append(f"{body} [from fleet records / DB]")

    if docs:
        cites = ", ".join(f"[{d['file']}]" for d in docs[:3])
        types = ", ".join(sorted({d["doc_type"] for d in docs[:3]}))
        parts.append(f"Relevant document(s) — {types}: {cites}")

    if not parts:
        return "I don't have a record or document for that."
    return "  ".join(parts)

# ---------------------------------------------------------------- dispatch
def mock_call_llm(system: str, user: str) -> str:
    s, q = system.lower(), user.lower()
    if "route" in s and "json" in s:
        return _classify(q)
    if "sqlite query" in s or "select only" in s:
        return _to_sql(q)
    if "answer only from the evidence" in s:
        return _ground(user)
    return ""
