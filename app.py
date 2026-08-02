import streamlit as st
from dotenv import load_dotenv
from judge import run_all_judges, compute_consensus

load_dotenv()

st.set_page_config(page_title="MergeGuardian", page_icon="🛡️", layout="wide")

VERDICT_COLOR = {"PASS": "green", "WARN": "orange", "BLOCK": "red"}
VERDICT_EMOJI = {"PASS": "✅", "WARN": "⚠️", "BLOCK": "⛔"}

st.title("🛡️ MergeGuardian")
st.caption("An AI Pull Request Firewall — LLM judges decide whether a PR is safe to merge, not just how it scores.")

with st.sidebar:
    st.header("About")
    st.write(
        "MergeGuardian runs three independent LLM judges (Security, "
        "Correctness, Maintainability) over a code change and produces a "
        "merge decision, not just a score."
    )
    st.write("**Policy:** any judge issuing BLOCK vetoes the merge, "
             "regardless of the other two scores.")

col1, col2 = st.columns([2, 1])

with col1:
    requirement = st.text_input(
        "Original requirement (optional, improves the Correctness judge)",
        placeholder="e.g. Add a login endpoint that authenticates a user by email and password",
    )
    code = st.text_area(
        "Paste the code / diff to review",
        height=350,
        placeholder="Paste a function, file, or diff here...",
    )

with col2:
    st.write("**Try a sample:**")
    if st.button("Load risky example (SQL injection)"):
        st.session_state["sample"] = open("sample_code/bad_example.py").read()
    if st.button("Load clean example"):
        st.session_state["sample"] = open("sample_code/good_example.py").read()

if "sample" in st.session_state and not code:
    code = st.session_state["sample"]
    st.text_area("Loaded sample:", value=code, height=200, disabled=True)

run = st.button("🔍 Run Judges", type="primary", disabled=not code.strip())

if run:
    with st.spinner("Three judges are reviewing the code..."):
        try:
            results = run_all_judges(code, requirement)
            consensus = compute_consensus(results)
        except RuntimeError as e:
            st.error(str(e))
            st.stop()

    verdict = consensus["overall_verdict"]
    color = VERDICT_COLOR[verdict]
    emoji = VERDICT_EMOJI[verdict]

    st.markdown("---")
    st.markdown(f"## {emoji} Overall: :{color}[{verdict} MERGE]")
    st.progress(consensus["overall_score"] / 100)
    st.write(f"**Risk score:** {consensus['overall_score']}/100")

    if consensus["blocking_judges"]:
        st.error(f"Blocked by: {', '.join(consensus['blocking_judges'])} judge(s)")
    elif consensus["warning_judges"]:
        st.warning(f"Flagged by: {', '.join(consensus['warning_judges'])} judge(s)")

    st.markdown("### Judge breakdown")
    cols = st.columns(3)
    for col, result in zip(cols, results):
        with col:
            v = result["verdict"]
            conf = result.get("confidence", "medium")
            st.markdown(f"**{result['judge'].title()} Judge** {VERDICT_EMOJI[v]}")
            st.markdown(f":{VERDICT_COLOR[v]}[{v}] — {result['score']}/100 &nbsp; "
                        f"`confidence: {conf}`")
            st.write(result["explanation"])
            if result["issues"]:
                st.markdown("**Issues:**")
                for issue in result["issues"]:
                    st.markdown(f"- {issue}")