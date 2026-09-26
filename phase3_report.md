# Phase 3 Report — Multi-Layer Anomaly Detection Engine
### Smart STP Monitor · Real-Time Plant Diagnostics & CPCB Compliance
*Date: 2026-09-26*

---

## 1. Executive Summary

Phase 3 implements a **4-Layer Anomaly Detection & Diagnostic Engine** designed specifically for municipal and apartment Sewage Treatment Plants (STP). The engine ingests real-time sensor streams (`pH`, `TDS`, `Turbidity`) and soft-sensor estimates (`DO`), differentiating between **Sensor Glitches**, **Biological Process Upsets**, and **Regulatory Breaches**.

```
  Live Sensor Streams (pH, TDS, Turbidity) + Soft Sensor DO
                          │
  ┌───────────────────────┴───────────────────────┐
  ▼                                               ▼
[Layer 1: CPCB Statutory Rules]       [Layer 2: Statistical Dynamic Filter]
 (Strict Indian Discharge Limits)      (Z-Score, IQR, Rate-of-Change, Flatline)
  │                                               │
  └───────────────────────┬───────────────────────┘
                          ▼
             [Layer 3: Isolation Forest ML]
              (Unsupervised 5D Correlation)
                          │
                          ▼
        [Layer 4: Root-Cause & Action Engine]
         • SENSOR_FAULT vs PROCESS_UPSET vs REGULATORY_BREACH
         • Step-by-Step Operator Action Checklist
```

---

## 2. Multi-Layer Detection Architecture

### 🛡️ Layer 1: CPCB Statutory Compliance Filter
Instantly checks effluent parameters against **Central Pollution Control Board (CPCB)** disposal norms:
- **pH:** Safe ($6.5 - 8.5$), Critical ($< 6.0$ or $> 9.0$)
- **Turbidity:** Optimal ($\le 5.0\text{ NTU}$), Warning ($5.0 - 10.0\text{ NTU}$), Breach ($> 10.0\text{ NTU}$)
- **TDS:** Optimal ($\le 800\text{ mg/L}$), Warning ($800 - 1500\text{ mg/L}$), Legal Ceiling ($> 2100\text{ mg/L}$)
- **DO:** Minimum ($\ge 2.0\text{ mg/L}$), Anaerobic Danger ($< 1.0\text{ mg/L}$)

### 📊 Layer 2: Dynamic Statistical Filter
- **Z-Score Filter ($|Z| > 3.0\sigma$):** Detects statistical excursions relative to the 4-year plant baseline.
- **IQR Outlier Filter ($1.5 \times \text{IQR}$):** Non-parametric boundary tracking.
- **Rate-of-Change (Spike) Detector:** Flags impossible physical rate-of-change (e.g. $\Delta\text{pH} > 0.5$ in 1 step).
- **Sensor Flatline / Stuck Detector:** Detects frozen sensor lines.

### 🌲 Layer 3: Unsupervised Machine Learning (Isolation Forest)
- **Architecture:** 150 Isolation Trees with $3.5\%$ expected contamination.
- **Feature Vector:** `[Treated pH, Treated TDS, Treated Turbidity, Formula_DO, Turb_TDS_Interaction]`.
- **Function:** Detects multi-sensor non-linear breakdowns where individual parameters appear within limits, but their joint combination indicates process drift.

### 🔍 Layer 4: Root-Cause Attribution & Operator Guidance
Differentiates between:
1. `SENSOR_FAULT`: Isolated single-sensor jump with unaffected companion sensors.
2. `PROCESS_UPSET`: Coherent multi-parameter shifts (e.g., *Clarifier Sludge Washout*, *Aeration Tank Failure*, *Salinity Shock Load*).
3. `REGULATORY_BREACH`: Direct statutory threshold violation.

---

## 3. Scenario Validation & Test Results

| # | Operational Scenario | Injected Conditions | Engine Status | Anomaly Classification | Root Cause Diagnosis | Operator Action Required |
|---|---|---|---|---|---|---|
| **1** | **Normal Plant Operation** | $\text{pH}=7.12, \text{TDS}=420, \text{Turb}=3.2$ | `NORMAL` | `NORMAL` | Normal water quality | Standard routine operation |
| **2** | **Clarifier Sludge Carryover** | $\text{pH}=7.08, \text{TDS}=430, \text{Turb}=8.5$ | `WARNING` | `PROCESS_UPSET` | Secondary clarifier sludge blanket carryover / filter breakthrough | 1. Check sludge blanket level.<br>2. Backwash sand/carbon filters.<br>3. Adjust RAS recycle pump. |
| **3** | **Salinity Shock Load** | $\text{pH}=7.15, \text{TDS}=680, \text{Turb}=3.8$ | `WARNING` | `PROCESS_UPSET` | Raw sewage salinity / softener chemical discharge | 1. Check inlet for chemical dumping.<br>2. Divert to equalization basin. |
| **4** | **CPCB Discharge Breach** | $\text{pH}=9.20, \text{TDS}=2250, \text{Turb}=15.0$| `CRITICAL` | `PROCESS_UPSET` | CPCB statutory discharge limit violated | Halt treated water reuse immediately; route back to equalization tank. |
| **5** | **Rate-of-Change Jump** | $\Delta\text{pH} = +0.70$ in 1 step | `LOW` | `UNUSUAL_PROCESS_DEVIATION` | Sudden rate-of-change jump | Inspect and recalibrate pH sensor. |

---

## 4. Codebase Components & Artifacts

- [`ml/anomaly_detection/cpcb_rules.py`](file:///d:/STP%20monitoring/ml/anomaly_detection/cpcb_rules.py) — Statutory CPCB rule engine.
- [`ml/anomaly_detection/statistical_detector.py`](file:///d:/STP%20monitoring/ml/anomaly_detection/statistical_detector.py) — Z-Score, IQR, and rate-of-change filter.
- [`ml/anomaly_detection/isolation_forest_detector.py`](file:///d:/STP%20monitoring/ml/anomaly_detection/isolation_forest_detector.py) — Trained multi-sensor Isolation Forest detector.
- [`ml/anomaly_detection/anomaly_engine.py`](file:///d:/STP%20monitoring/ml/anomaly_detection/anomaly_engine.py) — Production diagnostic engine.
- [`ml/anomaly_detection/train_anomaly_detector.py`](file:///d:/STP%20monitoring/ml/anomaly_detection/train_anomaly_detector.py) — Isolation Forest training pipeline.
- [`experiments/test_anomaly_scenarios.py`](file:///d:/STP%20monitoring/experiments/test_anomaly_scenarios.py) — Verification test suite.
