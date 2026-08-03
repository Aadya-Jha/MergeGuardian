import streamlit as st
from dotenv import load_dotenv
from judge import run_all_judges, compute_consensus
from history import save_evaluation, get_history, clear_history
from utils import icon
import html

load_dotenv()

st.set_page_config(page_title="MergeGuardian", page_icon=None, layout="wide")

# ----------------------------------------------------------------------
# Design tokens / verdict metadata
# ----------------------------------------------------------------------

VERDICT_META = {
    "PASS": {"color": "#3FB950", "bg": "rgba(63,185,80,0.12)", "border": "#2E7D3B", "label": "PASS"},
    "WARN": {"color": "#D29922", "bg": "rgba(210,153,34,0.12)", "border": "#9A7318", "label": "WARN"},
    "BLOCK": {"color": "#F85149", "bg": "rgba(248,81,73,0.12)", "border": "#B93C36", "label": "BLOCK"},
}
JUDGE_ICONS = {
    "security": icon("check",18),
    "correctness": icon("check",18),
    "maintainability": icon("alert",18),
}

# ----------------------------------------------------------------------
# Global styling — full Streamlit chrome override
# ----------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root{
--bg:#FAF8F3;
--card:#FFFFFF;
--border:#E5DED2;
--primary:#4361EE;
--success:#16A34A;
--warning:#D97706;
--danger:#DC2626;
--text:#1F2937;
--muted:#6B7280;
}

* { font-family: 'Inter', -apple-system, sans-serif; }

.stApp {
    background: var(--bg);
    color: var(--text);
}

#MainMenu, header[data-testid="stHeader"], footer { visibility: hidden; height: 0; }

.block-container {
    padding-top: 2.5rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: #F4EFE6;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .block-container { padding-top: 2rem; }

/* ---- Hero ---- */
.hero{
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:18px 0 36px;
    margin-bottom:42px;
    border-bottom:1px solid var(--border);
}
.hero-title {
     font-size:56px;
    font-weight:800;
    color:#1F2937;
    letter-spacing:-2px; line-height:1.1; margin:0;
    letter-spacing: -2px; margin: 0;
}
.hero-subtitle{
    margin-top:12px;
    font-size:19px;
    color:#6B7280;
    line-height:1.7;
    max-width:650px;
}
.hero-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(88,166,255,0.1); border: 1px solid rgba(88,166,255,0.35);
    color: var(--primary); font-size: 12.5px; font-weight: 600;
    padding: 5px 12px; border-radius: 20px;
}
.hero-dot {
    width: 6px; height: 6px; border-radius: 50%; background: var(--success);
    display: inline-block; box-shadow: 0 0 6px var(--success);
}

/* ---- Section labels ---- */
.section-label {
    font-size: 12px; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; color: var(--muted); margin-bottom: 12px;
}

/* ---- Cards ---- */
.panel {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 22px;
}

/* ---- Sidebar content blocks ---- */
.sb-block { margin-bottom: 26px; }
.sb-title {
    font-size: 13px; font-weight: 700; color: var(--text);
    text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 10px;
}
.sb-text { font-size: 13.5px; color: var(--muted); line-height: 1.6; }
.sb-policy {
    background: var(--card); border: 1px solid var(--border);
    border-left: 3px solid var(--primary); border-radius: 6px;
    padding: 12px 14px; font-size: 12.5px; color: var(--muted); line-height: 1.6;
}

/* ---- Inputs ---- */
.stTextInput input,
.stTextArea textarea{
    background:#FFFFFF !important;
    color:#1F2937 !important;
    border:1px solid #D6D3D1 !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder{
    color:#9CA3AF !important;
    opacity:1 !important;
}
.stTextArea textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 13px !important; }
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.15) !important;
}
.stTextInput label, .stTextArea label {
    color: var(--text) !important; font-size: 13px !important; font-weight: 600 !important;
}

/* ---- Buttons ---- */
.stButton>button {
    background:#4361EE;
    color:white; font-weight: 600;
    border-radius: 7px; border: none; padding: 0.55rem 1.1rem;
    font-size: 13.5px; transition: all 0.15s ease;
}
.stButton>button:hover { background: #79b8ff; box-shadow: 0 0 0 3px rgba(88,166,255,0.2); }
.stButton>button:disabled { background: #21262D; color: var(--muted); }

button[kind="secondary"] {
    background: var(--card) !important; color: var(--text) !important;
    border: 1px solid var(--border) !important;
}
button[kind="secondary"]:hover{
    background:#F3F4F6 !important;
    border-color:#4361EE !important;
}

/* ---- Verdict banner ---- */
.verdict-banner {
    display: flex; align-items: center; justify-content: space-between;
    padding: 26px 30px; border-radius: 12px; margin: 8px 0 28px 0;
    border: 1px solid; flex-wrap: wrap; gap: 16px;
}
.verdict-left { display: flex; align-items: center; gap: 16px; }
.verdict-icon {
    width: 44px; height: 44px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; font-weight: 800;
}
.verdict-title { font-size: 12px; color: var(--muted); font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px; }
.verdict-value { font-size: 36px; font-weight: 800; letter-spacing: -0.3px; }
.verdict-score { text-align: right; }
.verdict-score-num { font-size: 46px; font-weight: 800; }
.verdict-score-label { font-size: 11.5px; color: var(--muted); font-weight: 600; letter-spacing: 0.5px; }

/* ---- Status badge (flag row) ---- */
.flag-row {
    display: flex; align-items: center; gap: 10px;
    background: var(--card); border: 1px solid var(--border);
    border-radius: 8px; padding: 12px 16px; margin-bottom: 28px;
    font-size: 13.5px; color: var(--text);
}
.status-badge {
    display: inline-flex; align-items: center; padding: 3px 10px;
    border-radius: 5px; font-size: 11.5px; font-weight: 700;
    letter-spacing: 0.4px; text-transform: uppercase;
}

/* ---- Judge cards ---- */
.judge-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 26px; min-height:360px; height: 100%;
    display: flex; flex-direction: column;
}
.judge-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.judge-name { display: flex; align-items: center; gap: 9px; font-size: 18px; font-weight: 700; color: var(--text); }
.judge-icon-wrap {
    width: 28px; height: 28px; border-radius: 6px; background: #F8F5EF;
    border: 1px solid var(--border); display: flex; align-items: center;
    justify-content: center; font-size: 13px;
}
.judge-meta { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.judge-score { font-size: 15px; color: var(--muted); font-weight: 600; }
.judge-confidence {
    font-size: 10.5px; color: var(--muted); font-weight: 600;
    border: 1px solid var(--border); border-radius: 4px; padding: 1px 7px;
    text-transform: uppercase; letter-spacing: 0.4px;
}
.judge-explanation { font-size: 13px; color: #374151; line-height: 1.65; margin-bottom: 14px; }
.judge-issues-label { font-size: 11px; color: var(--muted); font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; margin-bottom: 8px; }
.judge-issue {
    font-size: 12.5px; color: #374151; padding: 6px 0 6px 14px;
    border-left: 2px solid var(--border); margin-bottom: 4px; line-height: 1.5;
}

/* ---- History ---- */
div[data-testid="stExpander"] {
    background: var(--card) !important; border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
div[data-testid="stExpander"] summary {
    font-size: 13.5px !important; font-weight: 600 !important; color: var(--text) !important;
}

div[data-testid="stCodeBlock"] pre {
    background: #1F2937 !important;
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
}
.history-row {
    display: flex; align-items: center; gap: 14px;
    padding: 10px 4px; border-bottom: 1px solid var(--border);
    font-size: 12.5px;
}
.history-row:last-child { border-bottom: none; }
.history-time { color: var(--muted); min-width: 150px; font-family: 'JetBrains Mono', monospace; font-size: 11.5px; }
.history-preview { color: #8B949E; font-family: 'JetBrains Mono', monospace; font-size: 11.5px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.history-score { color: var(--muted); font-size: 12px; font-weight: 600; min-width: 60px; text-align: right; }

.stProgress > div > div { background: var(--primary) !important; }
.stProgress > div { background: #21262D !important; }

hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)


def badge_html(verdict: str, extra_style: str = "") -> str:
    m = VERDICT_META[verdict]
    return (f'<span class="status-badge" style="background:{m["bg"]};'
            f'color:{m["color"]};border:1px solid {m["border"]};{extra_style}">{m["label"]}</span>')


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------

with st.sidebar:
    st.markdown('<div class="sb-block">', unsafe_allow_html=True)
    st.markdown('<div class="sb-title">Platform</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sb-text">MergeGuardian runs three independent LLM judges '
        '&mdash; Security, Correctness, and Maintainability &mdash; over every '
        'code change and returns a merge decision, not just a score.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-block">', unsafe_allow_html=True)
    st.markdown('<div class="sb-title">Merge Policy</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sb-policy">Any single judge issuing <b style="color:#F85149">BLOCK</b> '
        'vetoes the merge, regardless of the other two scores. Risk does not '
        'average away.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Hero
# ----------------------------------------------------------------------
st.markdown(
    '<div class="hero"><div><div class="hero-title">MergeGuardian</div>'
    '<div class="hero-subtitle">AI Merge Governance Firewall<br>'
    'Evaluate AI-generated code before merge using specialized LLM judges.</div></div>'
    '<div class="hero-badge"><span class="hero-dot"></span>LLM Judges Active</div></div>',
    unsafe_allow_html=True
)

# ----------------------------------------------------------------------
# Input section
# ----------------------------------------------------------------------

col1, col2 = st.columns([2.2, 1])

with col1:
    st.markdown('<div class="section-label">Pull Request Review</div>', unsafe_allow_html=True)
    requirement = st.text_input(
        "Requirement context (optional)",
        placeholder="e.g. Add a login endpoint that authenticates a user by email and password",
        label_visibility="visible",
    )
    code = st.text_area(
        "Code or diff",
        height=320,
        placeholder="Paste a function, file, or diff here...",
        label_visibility="visible",
    )

with col2:
    st.markdown('<div class="section-label">Quick Test Cases</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel" style="padding:16px;">', unsafe_allow_html=True)
    st.markdown('<div class="sb-text" style="margin-bottom:12px;">Load a fixture to preview judge behavior.</div>', unsafe_allow_html=True)
    if st.button("Load risky example — SQL injection", use_container_width=True):
        st.session_state["sample"] = open("sample_code/bad_example.py").read()
    if st.button("Load clean example", use_container_width=True):
        st.session_state["sample"] = open("sample_code/good_example.py").read()
    st.markdown('</div>', unsafe_allow_html=True)

if "sample" in st.session_state and not code:
    code = st.session_state["sample"]
    st.markdown('<div class="section-label" style="margin-top:20px;">Loaded Fixture</div>', unsafe_allow_html=True)
    st.code(code, language="python")

run = st.button("Analyze Pull Request", type="primary", disabled=not code.strip(), use_container_width=False)

# ----------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------

if run:
    with st.spinner("Running Security, Correctness, and Maintainability judges..."):
        try:
            results = run_all_judges(code, requirement)
            consensus = compute_consensus(results)
            save_evaluation(code, results, consensus)
        except RuntimeError as e:
            st.error(str(e))
            st.stop()

    verdict = consensus["overall_verdict"]
    m = VERDICT_META[verdict]

    st.markdown('<div class="section-label" style="margin-top:36px;">Merge Decision</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="verdict-banner" style="background:{m['bg']};border-color:{m['border']};">
        <div class="verdict-left">
            <div class="verdict-icon" style="background:{m['bg']};color:{m['color']};border:1px solid {m['border']};">
                {"&#10003;" if verdict == "PASS" else ("&#33;" if verdict == "WARN" else "&#10005;")}
            </div>
            <div>
                <div class="verdict-title">Overall Result</div>
                <div class="verdict-value" style="color:{m['color']};">{verdict} MERGE</div>
            </div>
        </div>
        <div class="verdict-score">
            <div class="verdict-score-num" style="color:{m['color']};">{consensus['overall_score']}<span style="font-size:15px;color:var(--muted);font-weight:600;">/100</span></div>
            <div class="verdict-score-label">RISK SCORE</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if consensus["blocking_judges"]:
        st.markdown(
            f'<div class="flag-row">{badge_html("BLOCK")}'
            f'<span>Blocked by <b>{", ".join(j.title() for j in consensus["blocking_judges"])}</b> judge(s)</span></div>',
            unsafe_allow_html=True,
        )
    elif consensus["warning_judges"]:
        st.markdown(
            f'<div class="flag-row">{badge_html("WARN")}'
            f'<span>Flagged by <b>{", ".join(j.title() for j in consensus["warning_judges"])}</b> judge(s)</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="flag-row">{badge_html("PASS")}'
            f'<span>All judges cleared this change</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-label" style="margin-top:8px;">Judge Breakdown</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for col, result in zip(cols, results):
        with col:
            v = result["verdict"]
            vm = VERDICT_META[v]
            conf = result.get("confidence", "medium")
            icon = JUDGE_ICONS.get(result["judge"], "&#8226;")

            issues_html = ""
            if result["issues"]:
                issues_html = '<div class="judge-issues-label">Issues Found</div>'
                for issue in result["issues"]:
                    issues_html += f'<div class="judge-issue">{issue}</div>'

            st.markdown(f"""
            <div class="judge-card">
                <div class="judge-header">
                    <div class="judge-name">
                        <div class="judge-icon-wrap">{icon}</div>
                        {result['judge'].title()}
                    </div>
                    {badge_html(v)}
                </div>
                <div class="judge-meta">
                    <span class="judge-score">{result['score']}/100</span>
                    <span class="judge-confidence">{conf} confidence</span>
                </div>
                <div class="judge-explanation">{result['explanation']}</div>
                {issues_html}
            </div>
            """, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# History
# ----------------------------------------------------------------------

st.write("")
st.write("")
with st.expander("Evaluation History", expanded=False):
    history = get_history()
    if not history:
        st.markdown('<div class="sb-text">No evaluations logged yet. Run a judge above to start building history.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="sb-text" style="margin-bottom:10px;">Showing last {len(history)} evaluations.</div>', unsafe_allow_html=True)
        rows_html = ""
        for h in history:
            b = badge_html(h["overall_verdict"], extra_style="min-width:52px;text-align:center;")
            rows_html += (
                f'<div class="history-row">{b}'
                f'<span class="history-time">{h["timestamp"]}</span>'
                f'<span class="history-preview">{h["code_preview"]}</span>'
                f'<span class="history-score">{h["overall_score"]}/100</span></div>'
            )
        st.markdown(f'<div class="panel" style="padding:6px 16px;">{rows_html}</div>', unsafe_allow_html=True)
        st.write("")
        if st.button("Clear history", type="secondary"):
            clear_history()
            st.rerun()