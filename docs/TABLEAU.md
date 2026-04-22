# Building the Equity Audit Dashboard in Tableau

The Streamlit app (`streamlit run app/streamlit_app.py`) is the primary interactive dashboard. For Tableau users, generate the data with `python -m src.export_tableau` and build these five views.

## Generated CSVs

| File | Rows | Purpose |
|---|---|---|
| `tableau/workforce_with_residuals.csv` | 2,500 | Per-employee: pay, residual, predicted pay, shortfall, demographic group |
| `tableau/gap_by_segment.csv` | ~25 | Pre-aggregated gap_pp by level / function / location |

## Five dashboard views

### 1. Raw vs adjusted gap (headline KPI card)
- **From** `gap_by_segment.csv`
- Two calculated fields: raw median gap vs adjusted gap
- A single dual-bar comparing the two — the "before vs after controls" story.

### 2. Gap by level (bar chart)
- **From** `gap_by_segment.csv` filtered to `segment_type = "level"`
- **Rows:** `segment`
- **Columns:** `gap_pp`
- **Color:** diverging red-blue colormap around zero
- Reference line at overall gap.

### 3. Residual distribution by gender (histogram)
- **From** `workforce_with_residuals.csv`
- **Columns:** `residual_pct` (binned, 1pp bins)
- **Rows:** Record count
- **Color:** `gender`
- **Reference line:** at 0 (the "no-gap" line)
- Visual smoking gun: the Female distribution sits clearly left of zero.

### 4. Demographic scatter: shortfall vs salary
- **From** `workforce_with_residuals.csv` filtered to `gender = "Female" AND residual < 0`
- **Columns:** `salary`
- **Rows:** `shortfall`
- **Color:** `is_urm`
- **Size:** `level`
- Shows where individual dollar-impact concentrates.

### 5. Cumulative cost curve (remediation budget)
- **From** `workforce_with_residuals.csv` filtered to negative residuals
- Sort by `shortfall` descending
- **Columns:** Index (rank)
- **Rows:** Running sum of `shortfall`
- Answers "how many employees can I afford to remediate at this budget?"

## Filters

- `level` (range)
- `function` (multi-select)
- `location` (multi-select)
- `gender` (radio)
- `is_urm` (true/false)

## Dashboard-level notes

- **Gap_pp is a signed percentage point.** Positive = Male residual higher. Negative = Female residual higher (rare but real in some segments).
- **"Legitimate drivers" is a business call.** The residuals are computed after controlling for level, function, location, tenure, experience, performance rating, and manager status. Any changes to that control set will change the residuals — document this assumption on the dashboard.
- **Sample size caveats:** filter out segments with fewer than ~30 employees before drawing conclusions. CI widens too much for reliable inference below that.
