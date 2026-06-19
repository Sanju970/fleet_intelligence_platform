# Wiring the real LLM

The agent calls models through `agent/llm.py`, which routes per node:

  classify + sql  ->  FAST model   (Groq / Llama 3.3 70B — speed)
  ground          ->  STRONG model (Claude Sonnet — no-hallucination)

## Set keys at the event (whichever you have)
```
export ANTHROPIC_API_KEY=sk-...     # enables Claude (best for grounding)
export GROQ_API_KEY=gsk-...         # enables Groq/Llama (fast classify+SQL)
export OPENAI_API_KEY=sk-...        # optional
```
With both Anthropic + Groq set, you automatically get the optimal split:
Groq for classify/SQL, Claude for grounding. Confirm with:
```
python agent/llm.py        # prints the routing table
```

## Override if needed
```
export FAST_PROVIDER=groq
export STRONG_PROVIDER=anthropic
export ANTHROPIC_MODEL=claude-sonnet-4-6   # override default model per provider
export GROQ_MODEL=llama-3.3-70b-versatile
```

## No keys?
Falls back to the rule-based mock so the system still runs. A failed real call
(bad key / rate limit) also falls back to mock for that turn so a demo never hard-crashes.

## Why split models
Classify and SQL-gen are simple + reward speed. Grounding is where the
no-hallucination guarantee lives and rewards careful instruction-following.
Routing each to the right model is cheaper, faster, AND more accurate than
using one model for everything — and it's a sharp thing to mention to a judge.
