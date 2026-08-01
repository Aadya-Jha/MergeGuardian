"""
Core MergeGuardian logic:
- call_judge(): runs one judge prompt against a code diff via Groq
- run_all_judges(): runs all three judges
- compute_consensus(): combines the three verdicts into one merge decision
"""

import json
import os
from groq import Groq
from prompts import JUDGES

MODEL = "llama-3.3-70b-versatile"


def get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY not set. Copy .env.example to .env and add your "
            "free key from https://console.groq.com/keys"
        )
    return Groq(api_key=api_key)


def call_judge(client: Groq, judge_name: str, code: str, requirement: str = "") -> dict:
    """Run a single judge against the given code. Returns a parsed verdict dict."""
    system_prompt = JUDGES[judge_name]

    user_content = f"```\n{code}\n```"
    if requirement.strip():
        user_content = f"Original requirement:\n{requirement}\n\nCode to review:\n{user_content}"

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)

        # Defensive defaults in case the model omits a field
        parsed.setdefault("score", 50)
        parsed.setdefault("verdict", "WARN")
        parsed.setdefault("issues", [])
        parsed.setdefault("explanation", "No explanation returned.")
        parsed["judge"] = judge_name
        return parsed

    except Exception as e:
        # A judge failing (bad JSON, API hiccup) should not crash the app.
        # Surface it as a WARN so a human notices, rather than silently
        # dropping that judge's opinion.
        return {
            "judge": judge_name,
            "score": 50,
            "verdict": "WARN",
            "issues": [f"Judge failed to run: {e}"],
            "explanation": "This judge encountered an error and could not "
                            "complete its review. Treat this PR with extra "
                            "manual scrutiny in this area.",
        }


def run_all_judges(code: str, requirement: str = "") -> list[dict]:
    client = get_client()
    return [call_judge(client, name, code, requirement) for name in JUDGES]


def compute_consensus(results: list[dict]) -> dict:
    """
    Merge policy: any single BLOCK from any judge blocks the merge,
    regardless of the other scores. This is a deliberate design choice —
    security/correctness problems don't average away just because style
    is clean. WARN-only results merge with a caution flag. All-PASS merges
    cleanly.
    """
    verdicts = [r["verdict"] for r in results]
    scores = [r["score"] for r in results]
    overall_score = round(sum(scores) / len(scores))

    if "BLOCK" in verdicts:
        overall_verdict = "BLOCK"
    elif "WARN" in verdicts:
        overall_verdict = "WARN"
    else:
        overall_verdict = "PASS"

    return {
        "overall_score": overall_score,
        "overall_verdict": overall_verdict,
        "blocking_judges": [r["judge"] for r in results if r["verdict"] == "BLOCK"],
        "warning_judges": [r["judge"] for r in results if r["verdict"] == "WARN"],
    }