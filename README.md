# MergeGuardian 🛡️

An AI Pull Request Firewall. An AI Pull Request Firewall that uses specialized LLM judges to evaluate AI-generated code for security, correctness, and maintainability before it is merged into production.

## 🔗 Resources

- [Project Documentation](https://docs.google.com/document/d/1wr4xZo4MLGu6Aj7QG-jdnr4zAu03NyFnBVwA0EgYfhg/edit?usp=sharing)
- [Demo Video](https://drive.google.com/file/d/1wb_SHv_t5sqhWLNY8sW5nviWb_z5J2L5/view?usp=sharing)
- [Live Demo](https://mergeguardian.streamlit.app/)

## Problem Statement

AI coding assistants now write large portions of production code, but
that code merges with the same review rigor (or lack of it) as before.
A single reviewer skimming a 350-line AI-generated diff can easily miss a
SQL injection or a requirement gap. MergeGuardian automates the first
pass of that review using LLM-as-judge, so obviously risky changes are
caught before a human even opens the PR.

## Why LLM-as-a-Judge?

MergeGuardian uses LLMs as specialized reviewers rather than code generators. Each judge evaluates a single quality dimension (Security, Correctness, or Maintainability) and produces structured, explainable feedback. A consensus engine converts these independent judgments into a merge decision, demonstrating how LLMs can act as governance and quality gates in modern software engineering workflows.

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

## Features

- Security, Correctness and Maintainability judges
- PASS / WARN / BLOCK merge decision
- Consensus-based merge policy
- Explainable verdicts with issues and confidence
- SQLite evaluation history
- Groq-powered low-latency inference
- Sample vulnerable and clean code fixtures

## Tech Stack

- **Language:** Python
- **Frontend:** Streamlit
- **LLM:** Groq API (`llama-3.3-70b-versatile`)
- **Database:** SQLite
- **Configuration:** python-dotenv

## System Architecture

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
6. Expand "Evaluation history" at the bottom to see past runs. This
   creates a local `history.db` file (SQLite) in the project folder —
   already excluded via `.gitignore`, along with `.env`.

## Project Structure

```text
mergeguardian/
├── app.py                  # Streamlit frontend
├── judge.py                # Runs the three LLM judges & consensus logic
├── prompts.py              # System prompts for each judge
├── history.py              # SQLite history management
├── utils.py                # Helper utilities (icons, formatting, etc.)
├── sample_code/
│   ├── bad_example.py      # Vulnerable demo code
│   └── good_example.py     # Clean demo code
├── assets/
│   └── icons/              # SVG icons used in the UI
├── .env.example            # Environment variable template
├── requirements.txt
├── README.md
└── config.toml             # Streamlit configuration
```

## Assumptions

- The MVP evaluates pasted code snippets or diffs rather than integrating directly with GitHub PRs.
- LLM judges evaluate code quality but do not execute code or measure real test coverage.
- Groq's free tier is sufficient for single-user demo usage.
- Evaluation history is stored locally in SQLite for simplicity.

## Future Improvements

- Real GitHub App webhook integration (auto-run on PR open)
- Swap in genuinely distinct models per judge for stronger independence
- Feed real static-analysis / coverage tool output into the judges as
  grounding context, rather than relying on LLM judgment alone
- Human-in-the-loop approval workflow for overriding BLOCK decisions
- Trend view over history (e.g. average risk score per week) to spot
  prompt or code-quality regressions over time

## License

This project is licensed under the MIT License.