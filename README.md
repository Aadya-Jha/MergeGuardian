# MergeGuardian 🛡️

An AI Pull Request Firewall. Instead of scoring an AI-generated response
after the fact, MergeGuardian sits in the critical path of a code merge:
it judges a code change and returns a **merge decision** (PASS / WARN /
BLOCK), not just a number.

## Problem Statement

AI coding assistants now write large portions of production code, but
that code merges with the same review rigor (or lack of it) as before.
A single reviewer skimming a 350-line AI-generated diff can easily miss a
SQL injection or a requirement gap. MergeGuardian automates the first
pass of that review using LLM-as-judge, so obviously risky changes are
caught before a human even opens the PR.

## Solution Overview

The code (or diff) is evaluated by three independent judges, each with a
narrow, non-overlapping area of concern:

- **Security Judge** — injection risks, hardcoded secrets, unsafe
  patterns
- **Correctness Judge** — does the code do what the stated requirement
  asked, missing edge cases, logic bugs
- **Maintainability Judge** — naming, complexity, style, duplication

Each judge returns a structured verdict (score, PASS/WARN/BLOCK, a
confidence level, specific issues, and a plain-English explanation). A
consensus step then combines the three into one decision using a simple,
deliberate policy: **any single BLOCK vetoes the merge**, regardless of
the other two scores. Security and correctness problems don't average
away just because the code style is clean.

Every evaluation is logged to a local SQLite history so past runs can be
reviewed from the UI — basic observability over judge behavior across
multiple PRs, not just a single one-shot result.

## Architecture

```
User pastes code/diff
        │
        ▼
   app.py (Streamlit UI)
        │
        ▼
   judge.py ─── run_all_judges() ───► Groq API (llama-3.3-70b-versatile)
        │              │                     ▲
        │              │            prompts.py (3 role-separated
        │              │             system prompts: security /
        │              │             correctness / maintainability)
        │              ▼
        │      3x structured JSON verdicts
        ▼
   compute_consensus() → overall risk score + PASS/WARN/BLOCK decision
        │
        ├──────────► history.py → SQLite (history.db) — logs every run
        ▼
   Rendered back in the Streamlit UI
```

## Evaluation Methodology

Each judge is a separate LLM call against the **same underlying model**
(`llama-3.3-70b-versatile` on Groq) but with a distinct, narrowly scoped
system prompt — a "role-separated single model" design rather than three
different models. This keeps latency and cost near zero on Groq's free
tier while still producing genuinely independent perspectives, since each
judge is explicitly instructed to ignore concerns outside its lane (e.g.
the Security judge is told not to comment on naming or style). Swapping
in distinct models per judge is a straightforward future improvement if
budget allows.

Every judge is required to return strict JSON with a score, verdict, a
confidence level (high/medium/low — how certain the judge is given only
the code shown, without full repo context), a list of specific issues,
and a senior-engineer-style explanation — this is what drives the
explainability requirement: users see *why* a verdict was reached, not
just a number.

## Setup Instructions

1. Get a free Groq API key at https://console.groq.com/keys (no credit
   card required).
2. Clone this repo and install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and paste in your key:
   ```
   cp .env.example .env
   ```
4. Run the app:
   ```
   streamlit run app.py
   ```
5. Paste code into the text box (or click one of the sample buttons) and
   click "Run Judges."
6. Expand "📜 Evaluation history" at the bottom to see past runs. This
   creates a local `history.db` file (SQLite) in the project folder —
   already excluded via `.gitignore`, along with `.env`.

## Assumptions

- The tool evaluates a pasted code snippet or diff, not a live GitHub
  webhook integration — this keeps the MVP scoped and demo-friendly.
  Live GitHub PR integration is a natural extension (see below).
- "Test coverage" is intentionally **not** reported by the judges, since
  that is a measured fact (which lines actually executed), not something
  an LLM can honestly assess without running the test suite. A future
  version would run a real coverage tool and feed the result to the
  Correctness judge as context, rather than have the LLM guess it.
- Groq's free tier (≈30 requests/min) is sufficient for this demo's
  single-PR-at-a-time usage pattern; a production version would need the
  paid tier or a self-hosted model at scale.
- Evaluation history is stored locally in SQLite for simplicity; a
  multi-user deployment would move this to a shared database, but no
  access-control layer is needed for a single-user demo tool like this.

## Future Improvements

- Real GitHub App webhook integration (auto-run on PR open)
- Swap in genuinely distinct models per judge for stronger independence
- Feed real static-analysis / coverage tool output into the judges as
  grounding context, rather than relying on LLM judgment alone
- Human-in-the-loop override for BLOCK verdicts before merge is actually
  prevented
- Trend view over history (e.g. average risk score per week) to spot
  prompt or code-quality regressions over time