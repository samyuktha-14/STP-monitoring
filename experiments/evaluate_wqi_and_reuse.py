"""
Evaluation of WQI and Reuse Suitability Engine across 4-Year Dataset and Edge Scenarios
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.water_quality_index.wqi_service import STPWaterQualityService

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed", "treated_water_clean.csv"))
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "results"))

def main():
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    service = STPWaterQualityService()
    
    wqi_scores = []
    wqi_grades = []
    toilet_suitable = []
    gardening_suitable = []
    cooling_suitable = []
    construction_suitable = []
    discharge_suitable = []
    
    print("Evaluating WQI and Reuse Suitability across 1,461 historical days...")
    for _, row in df.iterrows():
        res = service.evaluate_water(
            ph=row["Treated pH"],
            tds_mg_l=row["Treated TDS (mg/L)"],
            turbidity_ntu=row["Treated Turbidity (NTU)"]
        )
        wqi = res["wqi_summary"]["wqi_score"]
        grade = res["wqi_summary"]["grade"]
        reuse = res["reuse_suitability"]["purpose_details"]
        
        wqi_scores.append(wqi)
        wqi_grades.append(grade)
        toilet_suitable.append(reuse["Toilet Flushing"]["suitable"])
        gardening_suitable.append(reuse["Gardening & Landscaping"]["suitable"])
        cooling_suitable.append(reuse["HVAC Cooling Towers"]["suitable"])
        construction_suitable.append(reuse["Construction & Dust Control"]["suitable"])
        discharge_suitable.append(reuse["Environmental Discharge"]["suitable"])
        
    wqi_scores = np.array(wqi_scores)
    
    # Grade breakdown
    unique_grades, grade_counts = np.unique(wqi_grades, return_counts=True)
    grade_distribution = {g: int(c) for g, c in zip(unique_grades, grade_counts)}
    
    summary = {
        "dataset_total_days": len(df),
        "mean_wqi_score": round(float(np.mean(wqi_scores)), 2),
        "min_wqi_score": round(float(np.min(wqi_scores)), 2),
        "max_wqi_score": round(float(np.max(wqi_scores)), 2),
        "wqi_grade_distribution": grade_distribution,
        "reuse_suitability_percentages": {
            "Toilet Flushing": round(float(np.mean(toilet_suitable) * 100), 1),
            "Gardening & Landscaping": round(float(np.mean(gardening_suitable) * 100), 1),
            "HVAC Cooling Towers": round(float(np.mean(cooling_suitable) * 100), 1),
            "Construction & Dust Control": round(float(np.mean(construction_suitable) * 100), 1),
            "Environmental Discharge": round(float(np.mean(discharge_suitable) * 100), 1)
        }
    }
    
    print("\n=======================================================")
    print("       WQI & REUSE SUITABILITY HISTORICAL SUMMARY      ")
    print("=======================================================")
    print(json.dumps(summary, indent=2))
    
    # Save results
    out_file = os.path.join(RESULTS_DIR, "phase4_wqi_reuse_summary.json")
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved historical evaluation summary to {out_file}")

    # Test distinct operational scenarios
    print("\n=======================================================")
    print("           REAL-TIME OPERATIONAL SCENARIO TESTS        ")
    print("=======================================================")
    scenarios = {
        "Optimal Effluent": {"ph": 7.15, "tds_mg_l": 380, "turbidity_ntu": 1.2},
        "Typical Normal Day": {"ph": 7.10, "tds_mg_l": 425, "turbidity_ntu": 3.5},
        "Elevated Turbidity (Clarifier Issue)": {"ph": 7.05, "tds_mg_l": 440, "turbidity_ntu": 7.8},
        "Acidic Septic Drop": {"ph": 6.30, "tds_mg_l": 520, "turbidity_ntu": 8.0},
        "Severe High TDS / Chemical": {"ph": 8.80, "tds_mg_l": 1650, "turbidity_ntu": 12.0}
    }
    
    for name, params in scenarios.items():
        res = service.evaluate_water(**params)
        print(f"\n--- Scenario: {name} ---")
        print(f"Inputs: pH={params['ph']}, TDS={params['tds_mg_l']}, Turb={params['turbidity_ntu']}")
        print(f"WQI Score: {res['wqi_summary']['wqi_score']} (Grade {res['wqi_summary']['grade']} - {res['wqi_summary']['category']})")
        print(f"Overall Recommendation: {res['reuse_suitability']['overall_recommendation']}")
        print(f"Flushing: {res['reuse_suitability']['purpose_details']['Toilet Flushing']['status_badge']}")
        print(f"Gardening: {res['reuse_suitability']['purpose_details']['Gardening & Landscaping']['status_badge']}")

if __name__ == "__main__":
    main()
