"""
Lightweight evaluation history using SQLite (stdlib only, no new deps).
Every run of the judges gets logged so past evaluations can be reviewed —
this is what turns MergeGuardian from a one-shot tool into something with
basic observability over time.
"""

import sqlite3
import datetime

DB_PATH = "history.db"


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            code_preview TEXT NOT NULL,
            overall_verdict TEXT NOT NULL,
            overall_score INTEGER NOT NULL,
            security_verdict TEXT,
            correctness_verdict TEXT,
            maintainability_verdict TEXT
        )
    """)
    return conn


def save_evaluation(code: str, results: list[dict], consensus: dict) -> None:
    """Log one judge run to history."""
    conn = _get_conn()
    by_judge = {r["judge"]: r["verdict"] for r in results}
    conn.execute(
        """INSERT INTO evaluations
           (timestamp, code_preview, overall_verdict, overall_score,
            security_verdict, correctness_verdict, maintainability_verdict)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.datetime.now().isoformat(timespec="seconds"),
            code[:120].replace("\n", " ") + ("..." if len(code) > 120 else ""),
            consensus["overall_verdict"],
            consensus["overall_score"],
            by_judge.get("security"),
            by_judge.get("correctness"),
            by_judge.get("maintainability"),
        ),
    )
    conn.commit()
    conn.close()


def get_history(limit: int = 20) -> list[dict]:
    """Fetch the most recent evaluations, newest first."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM evaluations ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def clear_history() -> None:
    conn = _get_conn()
    conn.execute("DELETE FROM evaluations")
    conn.commit()
    conn.close()