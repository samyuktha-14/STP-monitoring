"""
Verification and Scenario Testing of Multi-Layer STP Anomaly Engine
"""

import os
import sys
import json

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.anomaly_detection.anomaly_engine import STPAnomalyEngine

def main():
    engine = STPAnomalyEngine()

    scenarios = {
        "1. Normal Plant Operation": {
            "ph": 7.12,
            "tds_mg_l": 420.0,
            "turbidity_ntu": 3.2
        },
        "2. Clarifier Sludge Carryover (High Turbidity)": {
            "ph": 7.08,
            "tds_mg_l": 430.0,
            "turbidity_ntu": 8.5
        },
        "3. High Salinity / TDS Shock Load": {
            "ph": 7.15,
            "tds_mg_l": 680.0,
            "turbidity_ntu": 3.8
        },
        "4. CPCB Statutory Discharge Breach (Severe)": {
            "ph": 9.20,
            "tds_mg_l": 2250.0,
            "turbidity_ntu": 15.0
        },
        "5. Sudden Rate-of-Change Sensor Spike": {
            "ph": 7.80,
            "tds_mg_l": 425.0,
            "turbidity_ntu": 3.4,
            "previous_readings": {"Treated pH": 7.10, "Treated TDS (mg/L)": 420.0, "Treated Turbidity (NTU)": 3.3}
        }
    }

    results = {}
    for name, params in scenarios.items():
        res = engine.diagnose(**params)
        results[name] = res
        print("=" * 60)
        print(f"SCENARIO: {name}")
        print("=" * 60)
        print(f"Overall Status   : {res['overall_status']}")
        print(f"Anomaly Type     : {res['anomaly_type']}")
        print(f"Root Cause       : {res['root_cause_diagnosis']}")
        print(f"Action Required  : {res['actionable_recommendation']}")
        print(f"CPCB Compliant   : {res['layer_results']['cpcb_regulatory']['is_compliant']}")
        print(f"ML Anomaly Score : {res['layer_results']['isolation_forest_ml']['anomaly_score']}")
        print()

    # Save scenario test results
    out_path = os.path.join(os.path.dirname(__file__), "results", "phase3_scenario_tests.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved scenario test results to {out_path}")

if __name__ == "__main__":
    main()
