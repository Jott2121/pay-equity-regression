"""Compensation Equity Audit — interactive dashboard landing.

Streamlit multi-page app:
    Home (this file)              → Executive summary + audit report
    1_🔍_Gap_Explorer.py           → Drill-down: gap by level, function, location
    2_💰_Remediation_Planner.py    → Employee-level shortfall + budget planner
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.simulate import simulate_workforce, GapConfig  # noqa: E402
from src.audit import run_audit, format_report  # noqa: E402

st.set_page_config(
    page_title="Compensation Equity Audit",
    page_icon="⚖️",
    layout="wide",
)


@st.cache_data
def get_workforce(gender_gap: float, race_gap: float, seed: int, n: int) -> pd.DataFrame:
    return simulate_workforce(
        n=n,
        gap=GapConfig(gender_gap_pct=gender_gap, race_gap_pct=race_gap),
        seed=seed,
    )


@st.cache_data
def get_audit(df: pd.DataFrame):
    return run_audit(df)


# --- Sidebar: dataset configuration -----------------------------------------
st.sidebar.header("Workforce parameters")
st.sidebar.caption(
    "Tune the simulated workforce. Real deployment swaps this for an HRIS export."
)
n = st.sidebar.slider("Employees", 500, 10000, 2500, step=500)
gender_gap = st.sidebar.slider("Injected gender gap (%)", 0.0, 15.0, 5.0, step=0.5) / 100
race_gap = st.sidebar.slider("Injected URM gap (%)", 0.0, 15.0, 3.0, step=0.5) / 100
seed = st.sidebar.number_input("Random seed", 1, 9999, 42)

df = get_workforce(gender_gap, race_gap, int(seed), int(n))
result = get_audit(df)

# Stash in session so sub-pages can reuse without recomputing.
st.session_state["workforce_df"] = df
st.session_state["audit_result"] = result
st.session_state["config"] = {
    "n": n,
    "gender_gap": gender_gap,
    "race_gap": race_gap,
    "seed": seed,
}

# --- Main --------------------------------------------------------------------
st.title("⚖️ Compensation Equity Audit")
st.markdown(
    "Regression-based pay equity audit — recover unexplained pay variation "
    "associated with gender or race after controlling for legitimate drivers."
)

# KPI strip
bin_df = df[df["gender"].isin(["Female", "Male"])]
raw_gap = 1 - bin_df.groupby("gender")["salary"].median()["Female"] / bin_df.groupby("gender")["salary"].median()["Male"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Workforce size", f"{len(df):,}")
c2.metric("Raw median gender gap", f"{raw_gap:.1%}", help="Unadjusted — includes role and level mix effects")
c3.metric(
    "Adjusted gender gap",
    f"{result.gender_gap_pct:.2%}",
    help="After controlling for level, function, location, tenure, experience, performance, manager status",
)
c4.metric("Model R²", f"{result.r_squared:.3f}", help="How much of log-salary variance legitimate drivers explain")

st.divider()

# Audit report
with st.expander("📋 Full audit report", expanded=True):
    st.code(format_report(result), language="text")

st.divider()

# Raw vs adjusted bar
st.subheader("Before vs after controlling for legitimate drivers")
comparison_df = pd.DataFrame(
    {
        "View": ["Raw median gap", "Adjusted gap"],
        "Gap (%)": [raw_gap * 100, result.gender_gap_pct * 100],
    }
)
st.bar_chart(comparison_df, x="View", y="Gap (%)", use_container_width=True)
st.caption(
    "The raw gap mixes role-mix and demographic effects. The adjusted gap is "
    "what's left after controlling for the legitimate drivers — that's what "
    "HR can act on."
)

st.divider()
st.markdown(
    """
### Use the other pages to drill in:

- **🔍 Gap Explorer** — where in the org is the gap concentrated? By level, function, location.
- **💰 Remediation Planner** — individual-employee shortfall list + budget what-if.
"""
)
