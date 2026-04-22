"""Export Tableau-ready CSVs for the compensation equity audit.

Run:
    python -m src.export_tableau

Produces two CSVs:
    tableau/workforce_with_residuals.csv  — employee-level, with the model's
                                             pay residual per person
    tableau/gap_by_segment.csv             — pre-aggregated gap by level /
                                             function / location, ready for
                                             bar charts
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.simulate import simulate_workforce, GapConfig
from src.audit import run_audit

ROOT = Path(__file__).resolve().parents[1]
TABLEAU_DIR = ROOT / "tableau"
TABLEAU_DIR.mkdir(exist_ok=True)


def export(gender_gap: float = 0.05, race_gap: float = 0.03) -> None:
    df = simulate_workforce(gap=GapConfig(gender_gap_pct=gender_gap, race_gap_pct=race_gap))
    result = run_audit(df)
    df = df.copy()
    df["residual"] = result.residuals
    df["residual_pct"] = df["residual"] * 100
    df["predicted_salary"] = df["salary"] * np.exp(-df["residual"])
    df["shortfall"] = (df["predicted_salary"] - df["salary"]).round(0)
    df["is_urm"] = df["race"].isin(["Black", "Hispanic", "Other/Multi"])
    df["demographic_group"] = df.apply(
        lambda r: f"{r['gender']} / {'URM' if r['is_urm'] else 'non-URM'}", axis=1
    )

    workforce_out = TABLEAU_DIR / "workforce_with_residuals.csv"
    df.to_csv(workforce_out, index=False)
    print(f"Wrote {len(df):,} rows to {workforce_out}")

    # Pre-aggregated segment-level gap table
    bin_df = df[df["gender"].isin(["Female", "Male"])]
    rows: list[dict] = []
    for segment_col in ["level", "function", "location"]:
        agg = bin_df.groupby([segment_col, "gender"])["residual"].agg(["mean", "count"]).unstack()
        mean_f = agg[("mean", "Female")]
        mean_m = agg[("mean", "Male")]
        n_f = agg[("count", "Female")]
        n_m = agg[("count", "Male")]
        for seg, gf, gm, nf_i, nm_i in zip(mean_f.index, mean_f.values, mean_m.values, n_f.values, n_m.values):
            rows.append(
                {
                    "segment_type": segment_col,
                    "segment": str(seg),
                    "residual_female": float(gf),
                    "residual_male": float(gm),
                    "gap_pp": float((gm - gf) * 100),
                    "n_female": int(nf_i),
                    "n_male": int(nm_i),
                }
            )
    seg_df = pd.DataFrame(rows)
    seg_out = TABLEAU_DIR / "gap_by_segment.csv"
    seg_df.to_csv(seg_out, index=False)
    print(f"Wrote {len(seg_df)} rows to {seg_out}")


if __name__ == "__main__":
    export()
