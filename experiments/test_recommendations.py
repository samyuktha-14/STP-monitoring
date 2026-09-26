"""
Verification Test Suite for Phase 5 Recommendation & Trend Analysis Engine
"""

import os
import sys
import json
import pandas as pd

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.recommendation_engine.operator_advisor import STPOperatorAdvisor

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed", "treated_water_clean.csv"))
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "results"))

def main():
    advisor = STPOperatorAdvisor()
    df = pd.read_csv(DATA_PATH)
    
    # 7-day historical window from clean dataset
    recent_history = df.tail(7).copy()

    test_scenarios = {
        "1. Normal Plant Operation": {
            "current_ph": 7.12,
            "current_tds": 420.0,
            "current_turbidity": 3.2,
            "history_df": recent_history
        },
        "2. Clarifier Sludge Carryover & Rising Turbidity": {
            "current_ph": 7.05,
            "current_tds": 440.0,
            "current_turbidity": 7.8,
            "history_df": pd.DataFrame({
                "Treated pH": [7.10, 7.11, 7.09, 7.08, 7.07, 7.06, 7.05],
                "Treated TDS (mg/L)": [420, 422, 425, 430, 432, 438, 440],
                "Treated Turbidity (NTU)": [2.8, 3.2, 3.9, 4.8, 5.7, 6.8, 7.8],
                "Treated DO (mg/L)": [2.8, 2.7, 2.7, 2.6, 2.6, 2.5, 2.5]
            })
        },
        "3. Aeration Basin Failure / Septic Odor Risk": {
            "current_ph": 6.45,
            "current_tds": 510.0,
            "current_turbidity": 5.5,
            "history_df": pd.DataFrame({
                "Treated pH": [7.10, 7.00, 6.90, 6.75, 6.60, 6.50, 6.45],
                "Treated TDS (mg/L)": [420, 430, 450, 470, 490, 500, 510],
                "Treated Turbidity (NTU)": [3.0, 3.3, 3.8, 4.2, 4.8, 5.1, 5.5],
                "Treated DO (mg/L)": [2.8, 2.4, 2.0, 1.7, 1.5, 1.3, 1.1]
            })
        },
        "4. High TDS / Softener Salinity Shock": {
            "current_ph": 7.20,
            "current_tds": 780.0,
            "current_turbidity": 3.6,
            "history_df": recent_history
        }
    }

    all_scenario_results = {}

    print("===============================================================")
    print("      PHASE 5: OPERATOR RECOMMENDATIONS & TREND ANALYSIS       ")
    print("===============================================================")

    for name, inputs in test_scenarios.items():
        res = advisor.generate_full_advisory(**inputs)
        all_scenario_results[name] = res

        print(f"\n[*] SCENARIO: {name}")
        print("-" * 60)
        print(f"Operational Health : {res['plant_health_summary']['operational_status']}")
        print(f"Headline Banner    : {res['plant_health_summary']['headline']}")
        print(f"WQI Score & Grade  : {res['plant_health_summary']['wqi_score']} (Grade {res['plant_health_summary']['wqi_grade']})")
        print(f"Affected Machinery : {', '.join(res['affected_equipment_units'])}")
        
        # Priority 1 actions
        p1 = res['prioritized_action_checklist']['priority_1_immediate']
        if p1:
            print(f"[P1] Priority 1 (Immediate): {p1[0]['action']}")
            print(f"     Target: {p1[0]['target']}")
            
        # Priority 2 actions
        p2 = res['prioritized_action_checklist']['priority_2_short_term']
        if p2:
            print(f"[P2] Priority 2 (Process): {p2[0]['action']}")

        # Trends
        trends = res['trend_analysis'].get('parameter_trends', {})
        if 'Turbidity' in trends:
            t = trends['Turbidity']
            print(f"[TREND] Turbidity Trend : {t['direction']} {t['trend_icon']} (Slope: {t['slope_per_day']:+.2f} NTU/day, 3-day proj: {t['projected_3day_value']:.1f} NTU)")

    # Save scenario results
    out_file = os.path.join(RESULTS_DIR, "phase5_recommendations_summary.json")
    with open(out_file, "w") as f:
        json.dump(all_scenario_results, f, indent=2)
    print(f"\nSaved Phase 5 scenario evaluation results to {out_file}")

if __name__ == "__main__":
    main()
