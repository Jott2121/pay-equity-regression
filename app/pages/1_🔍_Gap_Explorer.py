"""Drill into where the pay gap concentrates — level, function, location."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

st.set_page_config(page_title="Gap Explorer", page_icon="🔍", layout="wide")

if "workforce_df" not in st.session_state:
    st.warning("👋 Open the main page first to configure the workforce.")
    st.stop()

df = st.session_state["workforce_df"].copy()
result = st.session_state["audit_result"]
df["residual"] = result.residuals

st.title("🔍 Where does the gap concentrate?")
st.caption(
    "A single headline gap number hides important heterogeneity. These "
    "views show *which* segments are driving the residual, so any "
    "remediation plan targets the right places."
)

# --- Aggregation helper ------------------------------------------------------
def summarize(data: pd.DataFrame, group_col: str) -> pd.DataFrame:
    bin_df = data[data["gender"].isin(["Female", "Male"])]
    out = bin_df.groupby([group_col, "gender"])["residual"].agg(["mean", "count"]).unstack()
    mean_f = out[("mean", "Female")]
    mean_m = out[("mean", "Male")]
    n_f = out[("count", "Female")]
    n_m = out[("count", "Male")]
    return pd.DataFrame(
        {
            "n_female": n_f.astype(int),
            "n_male": n_m.astype(int),
            "residual_female": mean_f,
            "residual_male": mean_m,
            "gap_pp": (mean_m - mean_f) * 100,
        }
    ).sort_values("gap_pp", ascending=False)


tab1, tab2, tab3 = st.tabs(["By Level", "By Function", "By Location"])

with tab1:
    st.subheader("Unexplained gap by level (Male − Female, %)")
    summary = summarize(df, "level")
    st.bar_chart(summary["gap_pp"], use_container_width=True)
    st.dataframe(
        summary.style.format(
            {
                "residual_female": "{:+.3f}",
                "residual_male": "{:+.3f}",
                "gap_pp": "{:+.2f}",
            }
        ).background_gradient(subset=["gap_pp"], cmap="RdBu_r"),
        use_container_width=True,
    )
    st.caption(
        "If the gap varies dramatically by level (e.g. widest at senior levels), "
        "that often signals below-band hiring or promotion-decision effects."
    )

with tab2:
    st.subheader("Unexplained gap by function (Male − Female, %)")
    summary = summarize(df, "function")
    st.bar_chart(summary["gap_pp"], use_container_width=True)
    st.dataframe(
        summary.style.format(
            {
                "residual_female": "{:+.3f}",
                "residual_male": "{:+.3f}",
                "gap_pp": "{:+.2f}",
            }
        ).background_gradient(subset=["gap_pp"], cmap="RdBu_r"),
        use_container_width=True,
    )

with tab3:
    st.subheader("Unexplained gap by location (Male − Female, %)")
    summary = summarize(df, "location")
    st.bar_chart(summary["gap_pp"], use_container_width=True)
    st.dataframe(
        summary.style.format(
            {
                "residual_female": "{:+.3f}",
                "residual_male": "{:+.3f}",
                "gap_pp": "{:+.2f}",
            }
        ).background_gradient(subset=["gap_pp"], cmap="RdBu_r"),
        use_container_width=True,
    )

st.divider()

# --- Residual distribution --------------------------------------------------
st.subheader("Residual distribution by gender")
st.caption(
    "Model residuals = pay variation not explained by legitimate drivers. "
    "A systematic leftward shift for one gender = unexplained gap."
)
res_data = df[df["gender"].isin(["Female", "Male"])].copy()
res_data["residual_pct"] = res_data["residual"] * 100

# Streamlit doesn't have a native KDE; bin manually and plot.
bins = np.linspace(-20, 20, 41)
hist = (
    res_data.groupby("gender")["residual_pct"]
    .apply(lambda s: pd.cut(s, bins).value_counts().sort_index())
    .unstack(0)
    .fillna(0)
)
hist.index = [f"{b.left:+.0f} to {b.right:+.0f}" for b in hist.index]
st.bar_chart(hist, use_container_width=True)
st.caption("Histogram of residuals (% of predicted salary) by gender.")

# Export
st.download_button(
    label="⬇️ Download full residual detail (CSV)",
    data=df[
        [
            "employee_id",
            "gender",
            "race",
            "level",
            "function",
            "location",
            "salary",
            "residual",
        ]
    ].to_csv(index=False).encode("utf-8"),
    file_name="equity_residuals.csv",
    mime="text/csv",
)
