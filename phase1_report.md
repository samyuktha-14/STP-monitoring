# Phase 1 Report — Data Pipeline & Exploratory Data Analysis
### Smart STP Monitor · 2026-09-26

---

## 1. Dataset Shape

| Property | Value |
|---|---|
| **Rows** | 1,461 |
| **Columns** | 20 |
| **Frequency** | Daily |
| **Date range** | 2022-09-26 → 2026-09-25 |
| **Duration** | Exactly 4 years (1,461 days) |

---

## 2. Column Names & Data Types

| # | Column | Dtype | Non-Null | Role |
|---|--------|-------|----------|------|
| 1 | Date | datetime64 | 1461 | Index |
| 2 | Inlet Flow (m3/day) | float64 | 1461 | Inlet |
| 3 | Treated Flow (m3/day) | float64 | 1461 | Treated |
| 4 | Inlet pH | float64 | 1461 | Inlet |
| 5 | Inlet TDS (mg/L) | int64 | 1461 | Inlet |
| 6 | Inlet DO (mg/L) | float64 | 1461 | Inlet |
| 7 | Inlet TSS (mg/L) | int64 | 1461 | Inlet |
| 8 | Inlet BOD (mg/L) | int64 | 1461 | Inlet |
| 9 | Inlet COD (mg/L) | int64 | 1461 | Inlet |
| 10 | **Treated pH** | float64 | 1461 | ✅ **LIVE SENSOR** |
| 11 | **Treated TDS (mg/L)** | int64 | 1461 | ✅ **LIVE SENSOR** |
| 12 | Treated DO (mg/L) | float64 | 1461 | 🔬 LAB MEASURED |
| 13 | Treated TSS (mg/L) | float64 | 1461 | 🔬 LAB MEASURED |
| 14 | Treated BOD (mg/L) | float64 | 1461 | 🔬 LAB MEASURED |
| 15 | Treated COD (mg/L) | float64 | 1461 | 🔬 LAB MEASURED |
| 16 | BOD Removal (%) | float64 | 1461 | Derived |
| 17 | COD Removal (%) | float64 | 1461 | Derived |
| 18 | Inlet Turbidity (NTU) | float64 | 1461 | Inlet |
| 19 | **Treated Turbidity (NTU)** | float64 | 1461 | ✅ **LIVE SENSOR** |
| 20 | Turbidity Removal (%) | float64 | 1461 | Derived |

> [!IMPORTANT]
> **LIVE SENSOR** columns (10, 11, 19) are the only physical prototype inputs.
> **LAB MEASURED** columns (12–15) are historical targets for the soft-sensor — never real-time inputs.

---

## 3. Missing Value Report

| Result | Count |
|--------|-------|
| Columns with any missing value | **0** |
| Total missing cells | **0** |

✅ **No missing values anywhere in the dataset.** No imputation required.

---

## 4. Duplicate Report

| Check | Result |
|-------|--------|
| Duplicate dates | **0** |
| Fully duplicate rows | **0** |

✅ **No duplicates of any kind.**

---

## 5. Date Range & Continuity

| Property | Value |
|----------|-------|
| Start date | 2022-09-26 |
| End date | 2026-09-25 |
| Expected rows (daily) | 1,461 |
| Actual rows | 1,461 |
| Date gaps > 1 day | **0** |
| Single-day steps | **1,460** |

✅ **Perfect daily continuity.** No missing dates. No gaps. This is ideal for time-series modelling.

---

## 6. Descriptive Statistics

### 6A — Treated Water (Primary Focus)

| Statistic | pH | TDS (mg/L) | DO (mg/L) | TSS (mg/L) | BOD (mg/L) | COD (mg/L) | Turbidity (NTU) |
|-----------|-----|------------|-----------|------------|------------|------------|-----------------|
| **Count** | 1461 | 1461 | 1461 | 1461 | 1461 | 1461 | 1461 |
| **Mean** | 7.108 | 425.3 | 2.706 | 9.370 | 13.093 | 53.236 | 3.605 |
| **Std** | 0.146 | 59.7 | 0.402 | 2.262 | 2.630 | 7.723 | 1.470 |
| **Min** | 6.800 | 340 | 1.600 | 4.000 | 4.300 | 33.000 | 0.800 |
| **25%** | 7.000 | 370 | 2.440 | 7.800 | 11.300 | 48.000 | 2.400 |
| **Median** | 7.100 | 425 | 2.710 | 9.400 | 13.100 | 53.200 | 3.500 |
| **75%** | 7.210 | 480 | 2.980 | 10.900 | 14.900 | 58.400 | 4.700 |
| **Max** | 7.400 | 520 | 3.700 | 19.600 | 21.100 | 78.000 | 9.400 |

**Interpretation:**
- **pH** is well-controlled (6.8–7.4), typical for treated STP effluent. Very low std (0.15).
- **TDS** ranges 340–520 mg/L. Moderate variability (std ≈ 60 mg/L).
- **DO** is low (1.6–3.7 mg/L). This is characteristic of STP treated water — not potable drinking water.
- **BOD** (mean 13 mg/L) is consistent with secondary treatment standards for non-potable reuse.
- **COD** (mean 53 mg/L) is within expected range for treated effluent.
- **TSS** (mean 9.4 mg/L) is good — typical treated effluent target is < 20–30 mg/L.
- **Turbidity** (mean 3.6 NTU) is excellent for reuse — most guidelines require < 5–10 NTU.

### 6B — Inlet Water Summary

| Parameter | Mean | Std | Min | Max |
|-----------|------|-----|-----|-----|
| Inlet Flow (m³/day) | 89.9 | 5.7 | 74.4 | 105.0 |
| Treated Flow (m³/day) | 87.0 | 5.5 | 72.2 | 102.0 |
| Inlet pH | 7.050 | 0.137 | 6.60 | 7.48 |
| Inlet BOD (mg/L) | 210.9 | 45.9 | 140 | 290 |
| Inlet COD (mg/L) | 415.2 | 69.9 | 300 | 520 |
| Inlet TSS (mg/L) | 149.5 | 16.6 | 98 | 204 |
| Inlet Turbidity (NTU) | 48.5 | 8.0 | 25.3 | 87.5 |

### 6C — Removal Efficiencies

| Parameter | Mean | Std | Min | Max |
|-----------|------|-----|-----|-----|
| BOD Removal | 93.5% | 2.0% | 85.2% | 97.9% |
| COD Removal | 86.8% | 3.0% | 75.0% | 93.7% |
| Turbidity Removal | 92.6% | 2.7% | 86.7% | 98.0% |

✅ **Plant is performing consistently well** — BOD removal consistently above 85%, often above 93%.

---

## 7. Outlier Analysis (IQR 1.5× Fence)

| Column | IQR Lower Fence | IQR Upper Fence | Outliers | % |
|--------|-----------------|-----------------|----------|---|
| Treated pH | 6.68 | 7.52 | 0 | 0.0% |
| Treated TDS (mg/L) | 205 | 645 | 0 | 0.0% |
| Treated DO (mg/L) | 1.63 | 3.79 | **10** | **0.68%** |
| Treated TSS (mg/L) | 3.15 | 15.55 | **5** | **0.34%** |
| Treated BOD (mg/L) | 5.90 | 20.30 | **11** | **0.75%** |
| Treated COD (mg/L) | 32.40 | 74.00 | **7** | **0.48%** |
| Treated Turbidity (NTU) | −1.05 | 8.15 | **4** | **0.27%** |
| Inlet Turbidity (NTU) | 27.80 | 68.60 | **24** | **1.64%** |
| BOD Removal (%) | 88.40 | 98.80 | **23** | **1.57%** |

> [!NOTE]
> All outlier counts are low (< 2% of data). No column has alarming outlier frequency.
> These are **retained** in the dataset — they may represent real STP events (equipment adjustments, seasonal variation, maintenance days). They should not be automatically deleted.

---

## 8. Invalid/Impossible Value Check

All 10 physical bounds were checked:

| Check | Result |
|-------|--------|
| pH outside 0–14 | ✅ None |
| TDS < 0 or > 5000 mg/L | ✅ None |
| DO < 0 or > 20 mg/L | ✅ None |
| TSS < 0 or > 500 mg/L | ✅ None |
| BOD < 0 or > 500 mg/L | ✅ None |
| COD < 0 or > 1000 mg/L | ✅ None |
| Turbidity < 0 or > 200 NTU | ✅ None |
| Removal % outside 0–100 | ✅ None |

✅ **No physically impossible values found.**

---

## 8B. Z-Score Extreme Values (|z| > 3)

| Column | Extreme Points | Dates & Values |
|--------|---------------|----------------|
| Treated pH | 0 | — |
| Treated TDS | 0 | — |
| Treated DO | 0 | — |
| **Treated TSS** | **2** | 2023-06-19: **19.6** mg/L, 2026-05-20: **16.2** mg/L |
| **Treated BOD** | **5** | 2023-09-03: **21.0**, 2023-10-29: **21.1** (high), 2025-01-29: **5.2**, 2025-09-11: **5.2**, 2025-12-15: **4.3** (unusually low) |
| **Treated COD** | **1** | 2023-09-13: **78.0** mg/L |
| **Treated Turbidity** | **5** | Values: 9.4, 8.6, 8.2, 8.1, 9.2 NTU |

**Assessment of extreme points:**
- TSS outliers (19.6, 16.2 mg/L): Elevated but not physically impossible. Likely real treatment variation or measurement timing.
- BOD high outliers (21.0, 21.1 mg/L): Near the IQR upper fence — plausible as real STP variation on unusual load days.
- BOD low outliers (4.3–5.2 mg/L): Unusually low — could reflect very clean influent days or lab measurement variability.
- COD outlier (78.0 mg/L): Single spike in Sep 2023 — notable. Retained; could be real.
- Turbidity outliers (8.1–9.4 NTU): Higher than typical treated water but below any physical impossibility. Retained.

> [!WARNING]
> **All extreme values are retained.** Automatic deletion of unusual values in STP data risks losing real events. These will be handled by the anomaly detection model in Phase 3.

---

## 9. Correlation Analysis

### Pearson Correlation — Treated Water Parameters

|  | pH | TDS | DO | TSS | BOD | COD | Turbidity |
|--|-----|-----|-----|-----|-----|-----|-----------|
| **pH** | 1.000 | 0.023 | −0.063 | 0.005 | −0.015 | −0.017 | −0.021 |
| **TDS** | 0.023 | 1.000 | 0.012 | −0.011 | −0.004 | −0.016 | **0.127** |
| **DO** | −0.063 | 0.012 | 1.000 | 0.027 | 0.006 | −0.004 | −0.033 |
| **TSS** | 0.005 | −0.011 | 0.027 | 1.000 | −0.014 | −0.043 | 0.032 |
| **BOD** | −0.015 | −0.004 | 0.006 | −0.014 | 1.000 | −0.024 | 0.033 |
| **COD** | −0.017 | −0.016 | −0.004 | −0.043 | −0.024 | 1.000 | −0.001 |
| **Turbidity** | −0.021 | **0.127** | −0.033 | 0.032 | 0.033 | −0.001 | 1.000 |

> [!IMPORTANT]
> **Critical finding:** All pairwise Pearson correlations between treated-water parameters are very weak (|r| ≤ 0.13). The strongest observed is TDS↔Turbidity at r = 0.127.
>
> **This is the most important data quality finding for Phase 2.** Weak correlations between the 3 sensor inputs (pH, TDS, Turbidity) and the 4 lab targets (DO, BOD, COD, TSS) suggest that **soft-sensor modelling may be difficult.** The baseline comparison in Phase 2 will be critical to determine whether any ML model meaningfully outperforms the mean prediction.
>
> **Correlation does not imply causation.**

---

## 10. Generated Plots

All plots saved to: `d:\STP monitoring\data\plots\`

![All treated water parameters over time](file:///d:/STP%20monitoring/data/plots/plot1_treated_water_timeseries.png)

![pH time series with 30-day rolling mean](file:///d:/STP%20monitoring/data/plots/plot2_Treated_pH_rolling.png)

![TDS time series with 30-day rolling mean](file:///d:/STP%20monitoring/data/plots/plot2_Treated_TDS_mgL_rolling.png)

![Turbidity time series with 30-day rolling mean](file:///d:/STP%20monitoring/data/plots/plot2_Treated_Turbidity_NTU_rolling.png)

![DO time series with 30-day rolling mean](file:///d:/STP%20monitoring/data/plots/plot2_Treated_DO_mgL_rolling.png)

![BOD time series with 30-day rolling mean](file:///d:/STP%20monitoring/data/plots/plot2_Treated_BOD_mgL_rolling.png)

![COD time series with 30-day rolling mean](file:///d:/STP%20monitoring/data/plots/plot2_Treated_COD_mgL_rolling.png)

![TSS time series with 30-day rolling mean](file:///d:/STP%20monitoring/data/plots/plot2_Treated_TSS_mgL_rolling.png)

![Parameter distributions with KDE](file:///d:/STP%20monitoring/data/plots/plot3_distributions.png)

![Box plots by year](file:///d:/STP%20monitoring/data/plots/plot4_boxplot_by_year.png)

![Pearson correlation heatmap](file:///d:/STP%20monitoring/data/plots/plot5_correlation_heatmap.png)

![Sensor inputs vs lab targets scatter](file:///d:/STP%20monitoring/data/plots/plot6_sensor_vs_lab_scatter.png)

![IQR outlier boxplots](file:///d:/STP%20monitoring/data/plots/plot7_outlier_boxplots.png)

![Monthly mean trends](file:///d:/STP%20monitoring/data/plots/plot8_monthly_mean_trends.png)

---

## 11. Data Quality Issues Discovered

| Issue | Severity | Action Taken |
|-------|----------|--------------|
| Weak sensor↔lab correlations (|r| ≤ 0.13) | ⚠️ Medium | Noted. Will determine ML feasibility in Phase 2. |
| Z-score extremes in TSS (2), BOD (5), COD (1), Turbidity (5) | ⚠️ Low | Retained. Real STP events; flagged for Phase 3 anomaly detection. |
| IQR outliers in DO (10), BOD (11), Turbidity (4) | ⚠️ Low | Retained. Percentage < 1% — not alarming. |
| No missing values | ✅ Good | No action needed. |
| No date gaps | ✅ Good | Perfect daily continuity preserved. |
| No physically impossible values | ✅ Good | Data is physically plausible. |

---

## 12. Cleaned Dataset Location

| File | Path |
|------|------|
| CSV | [treated_water_clean.csv](file:///d:/STP%20monitoring/data/processed/treated_water_clean.csv) |
| Excel | [treated_water_clean.xlsx](file:///d:/STP%20monitoring/data/processed/treated_water_clean.xlsx) |

**No rows were deleted.** All 1,461 rows preserved. The cleaned dataset = original sorted chronologically + validated.

---

## Phase 1 Success Criteria — Checklist

| Criterion | Status |
|-----------|--------|
| Data loads correctly | ✅ |
| Preprocessing is reproducible | ✅ |
| No accidental data leakage | ✅ |
| Chronological ordering preserved | ✅ |
| Cleaned dataset saved | ✅ |
| Visualizations work (14 plots) | ✅ |
| Summary statistics generated | ✅ |
| Missing values checked | ✅ |
| Impossible values checked | ✅ |
| Outlier analysis performed | ✅ |
| Duplicate check performed | ✅ |
| Date continuity verified | ✅ |
| Correlations computed | ✅ |

---

## Exact Next Step — Phase 2 (Awaiting Approval)

**Feature 2: Virtual / Soft Sensor**

```
Inputs (physical prototype):
  Treated pH
  Treated TDS (mg/L)
  Treated Turbidity (NTU)

Targets (lab measurements — to be estimated):
  Treated DO   → evaluate independently
  Treated BOD  → evaluate independently
  Treated COD  → evaluate independently
  Treated TSS  → evaluate independently

Methodology:
  1. Establish mean baseline for each target
  2. Chronological 80/20 train/test split
  3. Compare: Linear Regression, Random Forest, Gradient Boosting, XGBoost
  4. TimeSeriesSplit + GridSearchCV for hyperparameter tuning
  5. Report MAE, RMSE, R² for every model × every target
  6. Apply model acceptance rule (meaningful improvement over baseline required)
  7. Save only accepted models for deployment
```

> [!CAUTION]
> Given the very weak Pearson correlations found in Phase 1 (all |r| ≤ 0.13 between sensors and lab targets), Phase 2 may find that **some or all lab parameters cannot be reliably estimated** from pH, TDS, and Turbidity alone. This is an honest scientific outcome that will be reported transparently.

---

*Phase 1 completed: 2026-09-26 | Script: `d:\STP monitoring\ml\preprocessing\` | Status: ✅ READY FOR PHASE 2*
