"""
Multi-provider LLM layer for FleetIQ.

Per-node model routing (the smart part):
  - FAST model (Groq/Llama)  -> classify + SQL generation  (speed matters)
  - STRONG model (Claude)    -> grounding/synthesis        (no-hallucination matters)

Config via env vars (set whichever keys you have at the event):
  ANTHROPIC_API_KEY   -> enables Claude
  GROQ_API_KEY        -> enables Groq
  OPENAI_API_KEY      -> enables OpenAI
  FAST_PROVIDER       -> groq | anthropic | openai | mock   (default: auto-detect)
  STRONG_PROVIDER     -> anthropic | groq | openai | mock   (default: auto-detect)

If no keys are set, falls back to the rule-based mock so the system still runs.

Usage:
  from agent.llm import llm
  text = llm(system, user, role="classify")   # role: classify | sql | ground
"""
import os

# Load .env (project root) so keys/providers can live in a file instead of `export`.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass  # python-dotenv not installed -> fall back to real env vars only

# model defaults per provider
MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4o-mini",
}

# role -> which tier
ROLE_TIER = {"classify": "fast", "sql": "fast", "ground": "strong"}

def _have(key): return bool(os.getenv(key))

def _auto(tier):
    """Pick a provider for a tier based on available keys."""
    if tier == "strong":
        if _have("ANTHROPIC_API_KEY"): return "anthropic"
        if _have("GROQ_API_KEY"): return "groq"
        if _have("OPENAI_API_KEY"): return "openai"
    else:  # fast
        if _have("GROQ_API_KEY"): return "groq"
        if _have("OPENAI_API_KEY"): return "openai"
        if _have("ANTHROPIC_API_KEY"): return "anthropic"
    return "mock"

def _provider_for(role):
    tier = ROLE_TIER.get(role, "strong")
    env = "FAST_PROVIDER" if tier == "fast" else "STRONG_PROVIDER"
    return os.getenv(env) or _auto(tier)

# ---- provider calls ----
def _call_anthropic(system, user, model):
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model, max_tokens=1024, system=system,
        messages=[{"role": "user", "content": user}])
    return "".join(b.text for b in msg.content if b.type == "text")

def _call_groq(system, user, model):
    from groq import Groq
    client = Groq()
    r = client.chat.completions.create(
        model=model, max_tokens=1024,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}])
    return r.choices[0].message.content

def _call_openai(system, user, model):
    from openai import OpenAI
    client = OpenAI()
    r = client.chat.completions.create(
        model=model, max_tokens=1024,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}])
    return r.choices[0].message.content

CALLERS = {"anthropic": _call_anthropic, "groq": _call_groq, "openai": _call_openai}

_warned = set()
def llm(system: str, user: str, role: str = "ground") -> str:
    provider = _provider_for(role)
    if provider == "mock":
        from agent.mock_llm import mock_call_llm
        if "mock" not in _warned:
            print("[llm] No API keys set -> using rule-based MOCK. "
                  "Set ANTHROPIC_API_KEY / GROQ_API_KEY to use real models.")
            _warned.add("mock")
        return mock_call_llm(system, user)
    model = os.getenv(f"{provider.upper()}_MODEL", MODELS[provider])
    try:
        return CALLERS[provider](system, user, model)
    except Exception as e:
        # fail safe to mock so a demo never hard-crashes on a bad key/rate limit
        print(f"[llm] {provider} call failed ({e}); falling back to mock for this turn.")
        from agent.mock_llm import mock_call_llm
        return mock_call_llm(system, user)

def status():
    """Print which provider each role will use — run at startup to confirm wiring."""
    print("FleetIQ LLM routing:")
    for role in ["classify", "sql", "ground"]:
        p = _provider_for(role)
        m = "(mock)" if p == "mock" else os.getenv(f"{p.upper()}_MODEL", MODELS.get(p, "?"))
        print(f"  {role:9s} -> {p:10s} {m}")

if __name__ == "__main__":
    status()
