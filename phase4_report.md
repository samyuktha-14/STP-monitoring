# Phase 4 Report — Water Quality Index (WQI) & Reuse Suitability Engine
### Smart STP Monitor · Effluent Grading & Multi-Purpose Reuse Compliance
*Date: 2026-09-26*

---

## 1. Executive Summary

Phase 4 implements a **Weighted Arithmetic Water Quality Index (WQI)** calculator and a **Multi-Purpose Reuse Suitability Engine** based on **Central Pollution Control Board (CPCB)** and **Ministry of Housing and Urban Affairs (MoHUA)** non-potable reuse standards.

```
       Live Sensor Inputs (pH, TDS, Turbidity) + Soft Sensor DO / ML Estimates
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
     [Weighted Arithmetic WQI Engine]             [Reuse Suitability Engine]
     • Parameter Sub-indices (q_i)                 • 5 Distinct Reuse Purposes
     • Overall 0-100 Score                         • Specific Failure Attribution
     • Grade (A, B, C, D, F) & Color Badge         • Actionable Reuse Guidance
```

---

## 2. Water Quality Index (WQI) Formulation

The WQI is calculated using the **Weighted Arithmetic Index Method** adapted for domestic STP treated effluent:

$$WQI = \frac{\sum_{i=1}^{n} w_i \cdot q_i}{\sum_{i=1}^{n} w_i}$$

Where $w_i$ is the unit weight and $q_i$ is the sub-index quality rating ($0 - 100$):

| Parameter | Unit | Ideal Value | Standard Limit | Weight ($w_i$) | Environmental Role |
|---|---|---|---|---|---|
| **DO** | mg/L | $6.0$ | $\ge 2.0$ | **0.25** | Biological aerobic health & freshness |
| **pH** | pH | $7.0$ | $6.5 - 8.5$ | **0.20** | Chemical balance & non-corrosiveness |
| **Turbidity** | NTU | $0.5$ | $\le 5.0$ | **0.20** | Clarity, aesthetics, and particulate load |
| **TDS** | mg/L | $250.0$ | $\le 800.0$ | **0.15** | Salinity & scaling potential |
| **BOD** | mg/L | $5.0$ | $\le 10.0$ | **0.10** | Organic waste degradation state |
| **COD** | mg/L | $20.0$ | $\le 50.0$ | **0.10** | Total chemically oxidizable matter |

### WQI Grading Scale
- **90 – 100 (Grade A - EXCELLENT):** High-clarity, thoroughly aerated effluent.
- **75 – 89 (Grade B - GOOD):** Standard compliant treated water. Suitable for landscaping & utilities.
- **50 – 74 (Grade C - MODERATE):** Restricted reuse (dust control/construction only).
- **25 – 49 (Grade D - POOR):** Sub-standard quality. Secondary filtration & aeration required.
- **0 – 24 (Grade F - VERY POOR / SEPTIC):** Severe process breakdown. Halt discharge immediately.

---

## 3. Multi-Category Reuse Suitability Matrix

The engine checks water quality against 5 distinct applications:

| Reuse Purpose | Key Criteria Required | Typical Use Case |
|---|---|---|
| **Toilet Flushing** | $\text{pH: } 6.5-8.5, \text{Turb} \le 2.0, \text{BOD} \le 10, \text{TSS} \le 10$ | Indoor dual-plumbing flushing |
| **Gardening & Landscaping**| $\text{pH: } 6.5-8.5, \text{Turb} \le 5.0, \text{TDS} \le 1500, \text{BOD} \le 20$ | Apartment lawns, parks, green belts |
| **HVAC Cooling Towers** | $\text{pH: } 7.0-8.2, \text{Turb} \le 2.0, \text{TDS} \le 800, \text{BOD} \le 10$ | Chiller & industrial cooling makeup |
| **Construction & Dust Suppression**| $\text{pH: } 6.0-9.0, \text{Turb} \le 15.0, \text{TDS} \le 2000, \text{BOD} \le 30$ | Concrete curing & dust control |
| **Environmental Discharge** | CPCB Schedule VI statutory limits | Surface drain / lake disposal |

---

## 4. Historical Dataset & Scenario Validation

### 📊 4-Year Historical Dataset Evaluation (1,461 Daily Records)
- **Mean Historical WQI:** **$79.52 / 100$** *(Grade B - GOOD)*
- **WQI Grade Distribution:**
  - **Grade B (Good):** **1,390 days (95.1%)**
  - **Grade C (Moderate):** **71 days (4.9%)**
  - **Grade D / F (Poor/Septic):** **0 days (0.0%)**
- **Reuse Suitability Rate:**
  - **Gardening & Landscape Irrigation:** **82.8% of operational days**
  - **Construction & Dust Suppression:** **100.0% of operational days**
  - **Toilet Flushing:** Restricted without tertiary ultrafiltration (BOD averages ~13 mg/L vs <10 mg/L dual-plumbing standard).

### 🧪 Real-Time Operational Scenarios Tested
| Scenario | Injected Condition | WQI Score & Grade | Primary Recommendation |
|---|---|---|---|
| **Optimal Effluent** | $\text{pH}=7.15, \text{TDS}=380, \text{Turb}=1.2$ | **83.8 (Grade B)** | *Suitable for Landscape Irrigation, Gardening & Construction* |
| **Typical Normal Day** | $\text{pH}=7.10, \text{TDS}=425, \text{Turb}=3.5$ | **80.2 (Grade B)** | *Suitable for Landscape Irrigation & Gardening* |
| **Clarifier Carryover**| $\text{pH}=7.05, \text{TDS}=440, \text{Turb}=7.8$ | **73.1 (Grade C)** | *Restricted Construction & Dust Control Only* |
| **Acidic Septic Drop** | $\text{pH}=6.30, \text{TDS}=520, \text{Turb}=8.0$ | **62.6 (Grade C)** | *Restricted Industrial Use Only (Re-aeration required)* |
| **Chemical Shock Load**| $\text{pH}=8.80, \text{TDS}=1650, \text{Turb}=12.0$| **47.1 (Grade D)** | *Unsuitable — Reroute to equalization tank* |

---

## 5. Deployed Codebase Modules

- [`ml/water_quality_index/wqi_calculator.py`](file:///d:/STP%20monitoring/ml/water_quality_index/wqi_calculator.py) — Weighted Arithmetic WQI scoring engine.
- [`ml/water_quality_index/reuse_engine.py`](file:///d:/STP%20monitoring/ml/water_quality_index/reuse_engine.py) — Multi-purpose reuse suitability matrix evaluator.
- [`ml/water_quality_index/wqi_service.py`](file:///d:/STP%20monitoring/ml/water_quality_index/wqi_service.py) — End-to-end integration service.
- [`experiments/evaluate_wqi_and_reuse.py`](file:///d:/STP%20monitoring/experiments/evaluate_wqi_and_reuse.py) — Evaluation test suite.
- [`experiments/results/phase4_wqi_reuse_summary.json`](file:///d:/STP%20monitoring/experiments/results/phase4_wqi_reuse_summary.json) — Statistical evaluation results.
