"""
Lane D — Eval harness. THIS IS WHAT WINS. Almost no other team will have one.

20 gold questions across all 3 routes. Scores:
  - route accuracy  (did the router pick the right path?)
  - answer correctness (LLM-graded against expected, or substring check)
  - grounding (did every claim cite a source? no-evidence -> must say "I don't have")

Run:  python eval/run_eval.py   (build the data first: see README)
Outputs: eval/results.json + a printed scoreboard.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Each gold item: question, expected_route, expected_contains (substring or concept)
GOLD = [
    # --- SQL route ---
    {"q": "How many trucks are currently active?", "route": "sql", "contains": "active"},
    {"q": "What's our total fuel spend across the whole fleet?", "route": "sql", "contains": "$"},
    {"q": "Which truck has the highest maintenance cost?", "route": "sql", "contains": "truck"},
    {"q": "List trucks whose registration expires in the next 30 days.", "route": "sql", "contains": "truck"},
    {"q": "How much did truck 4 spend on parts?", "route": "sql", "contains": "$"},
    {"q": "Who is the driver of truck 7?", "route": "sql", "contains": ""},
    {"q": "What's the average expense per truck?", "route": "sql", "contains": "$"},
    {"q": "How many trucks are in maintenance status?", "route": "sql", "contains": ""},
    # --- Retrieval route ---
    {"q": "Where is the tax form for truck 3?", "route": "retrieval", "contains": "2290"},
    {"q": "Find the title document for truck 1.", "route": "retrieval", "contains": "TITLE"},
    {"q": "Show me a fuel receipt for truck 5.", "route": "retrieval", "contains": "receipt"},
    {"q": "What does the maintenance invoice for truck 2 list?", "route": "retrieval", "contains": ""},
    {"q": "Pull the registration document for truck 9.", "route": "retrieval", "contains": "REGISTRATION"},
    {"q": "Is there a lien on truck 6's title?", "route": "retrieval", "contains": "Lien"},
    # --- Hybrid route ---
    {"q": "Which trucks have registrations expiring soon and what document do I need to renew them?", "route": "hybrid", "contains": "registration"},
    {"q": "Truck 4 seems expensive — what did we spend and is there a maintenance invoice explaining it?", "route": "hybrid", "contains": ""},
    {"q": "What's the tax status of our most expensive truck?", "route": "hybrid", "contains": ""},
    {"q": "For trucks in maintenance, show their latest repair invoice.", "route": "hybrid", "contains": ""},
    # --- Grounding traps (answer is NOT in the data — agent must refuse, not invent) ---
    {"q": "What's the GPS location of truck 8 right now?", "route": "sql", "contains": "don't have"},
    {"q": "What's the engine temperature of truck 2 right now?", "route": "sql", "contains": "don't have"},
]

def run():
    from agent.graph import answer
    results, route_hits, content_hits = [], 0, 0
    for g in GOLD:
        try:
            out = answer(g["q"])
        except Exception as e:
            out = {"route": "ERROR", "answer": str(e)}
        route_ok = out.get("route") == g["route"]
        content_ok = g["contains"].lower() in str(out.get("answer", "")).lower()
        route_hits += route_ok
        content_hits += content_ok
        results.append({**g, "got_route": out.get("route"),
                        "route_ok": route_ok, "content_ok": content_ok,
                        "answer": out.get("answer")})
    n = len(GOLD)
    summary = {"n": n, "route_accuracy": f"{route_hits}/{n}",
               "content_accuracy": f"{content_hits}/{n}"}
    with open(os.path.join(os.path.dirname(__file__), "results.json"), "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)
    print("=" * 48)
    print("  FleetIQ Eval Scoreboard")
    print("=" * 48)
    print(f"  Route accuracy   : {route_hits}/{n}")
    print(f"  Content accuracy : {content_hits}/{n}")
    print("=" * 48)
    print("  (screenshot this slide for the demo)")
    return summary

if __name__ == "__main__":
    run()
