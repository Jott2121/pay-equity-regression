"""Employee-level shortfall list + budget-aware remediation planner."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

st.set_page_config(page_title="Remediation Planner", page_icon="💰", layout="wide")

if "workforce_df" not in st.session_state:
    st.warning("👋 Open the main page first to configure the workforce.")
    st.stop()

df = st.session_state["workforce_df"].copy()
result = st.session_state["audit_result"]
df["residual"] = result.residuals
df["predicted_salary"] = df["salary"] * np.exp(-df["residual"])
df["shortfall"] = (df["predicted_salary"] - df["salary"]).round(0)

st.title("💰 Remediation Planner")
st.caption(
    "Employee-level shortfall list for Female employees whose pay sits below "
    "the legitimate-driver model's prediction. Adjust thresholds to see how "
    "budget scales."
)

# --- Knobs -------------------------------------------------------------------
col_a, col_b, col_c = st.columns(3)
with col_a:
    threshold = st.slider(
        "Minimum shortfall threshold (%)",
        0.0,
        10.0,
        2.0,
        step=0.5,
        help="Only flag employees whose residual is below this % of predicted pay.",
    )
with col_b:
    budget_cap = st.number_input(
        "Max budget (USD)",
        min_value=0,
        max_value=50_000_000,
        value=5_000_000,
        step=250_000,
        help="Prioritize largest shortfalls until budget is exhausted.",
    )
with col_c:
    group_filter = st.selectbox(
        "Prioritize group",
        ["Female only", "Female + URM", "All below-parity employees"],
    )

# --- Filter -----------------------------------------------------------------
below = df[df["residual"] < -(threshold / 100)].copy()
if group_filter == "Female only":
    below = below[below["gender"] == "Female"]
elif group_filter == "Female + URM":
    below = below[(below["gender"] == "Female") | (below["race"].isin(["Black", "Hispanic", "Other/Multi"]))]

below = below.sort_values("shortfall", ascending=False)

# --- Budget allocation ------------------------------------------------------
below["cumulative_cost"] = below["shortfall"].cumsum()
below["funded"] = below["cumulative_cost"] <= budget_cap

# --- KPIs -------------------------------------------------------------------
total_below = len(below)
total_shortfall = int(below["shortfall"].sum())
n_funded = int(below["funded"].sum())
cost_funded = int(below.loc[below["funded"], "shortfall"].sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Employees below threshold", f"{total_below:,}")
c2.metric("Total shortfall", f"${total_shortfall:,}")
c3.metric("Budget covers", f"{n_funded:,} employees", f"{n_funded / max(total_below, 1):.0%}")
c4.metric("Funded cost", f"${cost_funded:,}", f"of ${budget_cap:,} budget")

st.divider()

# --- Plot -------------------------------------------------------------------
st.subheader("Cumulative cost vs number of employees funded")
cost_curve = below[["cumulative_cost"]].reset_index(drop=True)
cost_curve.index = cost_curve.index + 1
cost_curve.index.name = "Employees (ranked by shortfall, largest first)"
st.line_chart(cost_curve, use_container_width=True)
st.caption(
    "Classic remediation economics: the top ~20% of employees by shortfall "
    "typically represent ~50% of total cost."
)

st.divider()

# --- Table ------------------------------------------------------------------
st.subheader("Shortfall list")
st.caption(
    "Sorted by shortfall size, descending. The `funded` column marks who gets "
    "covered under the current budget."
)
display = below[
    [
        "employee_id",
        "gender",
        "race",
        "level",
        "function",
        "location",
        "performance_rating",
        "salary",
        "predicted_salary",
        "shortfall",
        "cumulative_cost",
        "funded",
    ]
].head(200)

st.dataframe(
    display.style.format(
        {
            "salary": "${:,.0f}",
            "predicted_salary": "${:,.0f}",
            "shortfall": "${:,.0f}",
            "cumulative_cost": "${:,.0f}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    label="⬇️ Download full remediation list (CSV)",
    data=below.to_csv(index=False).encode("utf-8"),
    file_name="remediation_plan.csv",
    mime="text/csv",
)
