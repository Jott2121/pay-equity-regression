# Compensation Equity Analysis

Regression-based pay equity audit — the methodology used by major comp consulting firms (Mercer, WTW, Aon) for annual pay reviews. Identifies pay variation associated with gender or race **after** controlling for legitimate drivers (level, function, location, tenure, experience, performance, management status).

**Built by a former Fortune 500 talent acquisition leader applying statistical methods to one of HR's highest-stakes problems.**

### 🚀 [Live demo: compensation-equity-jotterson.streamlit.app](https://compensation-equity-jotterson.streamlit.app/)

Configure the simulated workforce live and watch the audit recover the injected pay gap in real time.

![Raw vs adjusted gender gap](docs/raw_vs_adjusted_gap.png)

---

## Why this matters

A headline statistic like *"women are paid 18% less than men"* is almost always reported as an unadjusted median gap. That number mixes together:

- **Explainable drivers** — different role mix, different tenure, different experience levels.
- **Unexplainable residuals** — pay variation that doesn't track any legitimate driver.

Only the residual is the lever HR and comp teams can actually act on. A pay equity audit isolates it.

**Business stakes:**

- **Legal exposure.** Pay discrimination litigation averages $2–20M in settlements. Proactive audit + remediation is a fraction of that.
- **Regulatory.** EU Pay Transparency Directive (in force 2026), UK Equality Act, California SB-1162, NYC Pay Transparency Law — all require pay equity disclosures or evidence.
- **Retention.** Underpaid employees leave at higher rates, and the knowledge spreads (Glassdoor, levels.fyi).

---

## Simulated workforce schema

Each synthetic employee has:

| Category | Fields |
|---|---|
| **Demographics** | gender (Female / Male / Non-binary), race (5 categories including URM flag), is_people_manager |
| **Organization** | level (1 through 7, IC1 to Director+), function (Engineering / Product / Sales / Marketing / Operations / HR / Finance), location (SF / NY / Seattle / Austin / Denver / Remote) |
| **Experience** | years_experience, years_at_company, performance_rating (1-5) |
| **Compensation** | salary (base, USD), bonus, total_comp |

The simulator (`src/simulate.py`) generates salaries using legitimate drivers only — level band, location multiplier, function premium, performance adjustment, tenure effect, manager premium, plus a small random noise component. Injected gender and URM gap multipliers are applied *after* the legitimate salary is computed. That means the gap is known ground truth: the audit's job is to recover it.

---

## Methodology

A standard two-stage regression approach.

### Stage 1 — Model log(salary) on legitimate drivers

```
log(salary) ~ C(level) + C(function) + C(location)
            + years_at_company + years_experience
            + C(performance_rating) + is_people_manager
```

The log transform is used because compensation effects are multiplicative. A 10% level-over-level premium is 10% whether the employee is L2 or L7; linear regression on raw dollars would force the model to fit the same premium at both ends, distorting the estimates. Log-scale residuals are also directly interpretable as approximate percentage differences from predicted pay.

Residuals of this model are the portion of each employee's log-salary that is *not* explained by the legitimate drivers. If the drivers are well-specified, these residuals should look like random noise centered at zero.

### Stage 2 — Test if residuals vary by protected class

```
residual ~ is_female          # gender gap
residual ~ is_urm             # race gap (URM vs non-URM)
```

A statistically significant non-zero coefficient on the protected-class indicator means pay variation that the legitimate-driver model cannot explain is correlated with gender or race. That is the unexplained gap.

### Why simulation makes this a valid demonstration

Because the injected gap is known ground truth, we can verify the methodology rather than just asserting it. Running the audit with a 5% gender gap and 3% URM gap injected should recover approximately those numbers within tight confidence intervals. Running it with zero injected gap should return a statistically non-significant coefficient. Both sanity checks pass (see below).

### Recovered gaps (on simulated data with known ground truth)

Injected gaps: 5% gender, 3% URM race.

```
Legitimate-driver model R² = 0.991

--- Gender (Female vs Male) ---
  Unexplained gap:        +5.12%
  95% CI:                 [+4.78%, +5.46%]
  p-value:                < 0.001
  Employees below parity: 791
  Remediation cost:       $6,494,879

--- Race (URM vs non-URM) ---
  Unexplained gap:        +2.57%
  95% CI:                 [+2.13%, +3.01%]
  p-value:                < 0.001
```

Recovered gaps match the injected values within tight confidence intervals — the methodology works.

### Null-effect sanity check

Set the injected gaps to zero, rerun the audit, and the recovered gender gap drops to approximately `+0.12%` with `p = 0.48` — not statistically distinguishable from zero. This is the check that separates real methodology from something that would produce a "finding" even in a pristine workforce.

---

## What the visualizations show

### Raw vs adjusted

![Raw vs adjusted](docs/raw_vs_adjusted_gap.png)

The raw median gap overstates the actionable gap because it mixes role mix with pay discrimination. The adjusted gap is what matters.

### Residual distribution by gender

![Residual distribution](docs/residual_distribution.png)

The Female residual distribution is shifted left of zero — individually small, but consistent enough that it's statistically unmistakable across thousands of employees.

### Where the gap concentrates

![Gap by level](docs/gap_by_level.png)

Almost every level shows an unexplained gap in the same direction, which is the signature of a systemic effect rather than noise from a single outlier team.

---

## Why simulated data?

Real workforce compensation data is essentially never public. Public pay datasets (BLS, federal payroll) lack the demographic + level + function granularity needed to demonstrate an audit.

Simulation has a meaningful advantage for a portfolio demo: **we know the ground truth**. If the methodology works, it should recover the injected gap within its confidence interval — and it does (5.12% recovered vs 5.00% injected).

The simulator (`src/simulate.py`) is calibrated against:

- Level salary bands from Radford / Levels.fyi / BLS SOC 15-2051 (2024)
- Geographic comp multipliers from public tech comp reports
- Function premiums consistent with 2024 Mercer comp data
- Performance-based pay variance typical of structured merit programs

All relationships are tunable via the `GapConfig` dataclass. Set gap to zero and the audit confirms no unexplained variance — a sanity check for the methodology itself.

---

## What's in this repo

| File | Purpose |
|---|---|
| `src/simulate.py` | Generates a realistic synthetic workforce with injected pay gaps. |
| `src/audit.py` | The two-stage regression audit + formatted report. |
| `src/visualize.py` | Regenerates all README figures. |
| `notebooks/01_equity_audit.ipynb` | Full analyst-style walkthrough with HR interpretation. |
| `docs/` | Generated visualizations referenced in this README. |

---

## Interactive dashboard

A multi-page Streamlit app ships with the repo. [Try the live version](https://compensation-equity-jotterson.streamlit.app/) or run it locally.

### Home page

Live configuration of the simulated workforce and audit result.

- **Sidebar controls**: workforce size (500 to 10,000 employees), injected gender gap percent, injected URM gap percent, random seed
- **KPI strip**: workforce size, raw median gender gap (unadjusted), adjusted gender gap (after controls), model R-squared
- **Full audit report** displayed in a text panel with all estimates, confidence intervals, p-values, and remediation cost
- **Comparison bar chart**: raw median gap vs adjusted gap — the "before vs after controlling for legitimate drivers" visualization

### Gap Explorer

Drill into where the gap concentrates across the organization.

- Three tabs: gap by level, gap by function, gap by location
- Each tab shows a bar chart of percentage-point gap (Male residual minus Female residual) plus a detail table with per-segment residuals, sample sizes, and a red-blue diverging heatmap
- **Residual distribution histogram** by gender — shows the systematic leftward shift in the Female distribution that is the visual signature of an unexplained gap
- CSV export of full residual detail for downstream analysis in Excel, Tableau, or Power BI

### Remediation Planner

Converts the statistical finding into a budget-ready remediation plan.

- **Threshold slider**: only include employees whose residual is below some percentage of predicted pay (typically 2 percent)
- **Budget cap input**: maximum remediation spend
- **Group prioritization**: Female only, Female plus URM, or all below-parity employees
- **KPIs**: count of employees below threshold, total shortfall, count the budget covers, funded cost
- **Cumulative cost curve**: shows the classic remediation economics where the top ~20% of employees by shortfall typically account for ~50% of total cost
- **Sorted shortfall table**: employee-level detail with predicted pay, actual pay, shortfall, cumulative cost, and a `funded` flag indicating who gets covered under the current budget
- CSV export of the full remediation list

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

**Tableau / Power BI users:** generate Tableau-ready CSVs:
```bash
python -m src.export_tableau  # writes tableau/workforce_with_residuals.csv + tableau/gap_by_segment.csv
```
Then follow [docs/TABLEAU.md](docs/TABLEAU.md) for the recipe to build five dashboard views.

## Run the core audit scripts

```bash
python -m src.audit         # runs audit, prints report
python -m src.visualize     # regenerates the visualizations
jupyter lab notebooks/01_equity_audit.ipynb
```

---

## What a serious HR reviewer will push back on

I've flagged these myself inside the notebook, but they deserve their own section because they're the conversations any real audit actually lives and dies on:

1. **"Legitimate drivers" is a judgment call.** Using *level* as a control masks any discrimination that manifests through *leveling*. If women are systematically under-leveled, the gender gap partially hides inside `C(level)`. A complete audit adds a second-order analysis: promotion velocity and leveling decisions by demographic group.

2. **Small subgroup sizes.** With 2,500 employees we can say something about the Female/Male gap overall. We *cannot* reliably detect a Black Women gap if there are only ~60 Black women in the sample — the confidence intervals would be too wide. Intersectional analyses need larger populations or industry benchmarks.

3. **Correlation ≠ causation.** A statistically significant gap is evidence of *something*. Discrimination is one possibility; another is unmeasured confounders (market pay shifts in specific roles, lateral hiring below band, transfer dynamics). The audit surfaces the residual; it doesn't name the cause.

4. **The remediation dollar figure is an upper bound.** Real remediation applies thresholds (e.g. only gaps >2%), phased budgets, and manager input. The quoted number is the naive "close every shortfall completely" estimate.

---

## About

Built by **Jeff Otterson** — talent acquisition leader with Fortune 500 experience at Amazon and Oracle. Building a portfolio of people analytics projects applying modern statistical methods and ML to the operational problems I've seen firsthand.

- **Companion project**: [hr-attrition-predictor](https://github.com/Jott2121/hr-attrition-predictor)
- **MeritForge AI**: [meritforgeai.com](https://www.meritforgeai.com) — free AI career tools

MIT licensed.
