"""
Smart STP Monitor — Lightweight Local Web Server
Binds Flask / Python backend modules directly to the Vanilla HTML/CSS UI.
"""

import os
import sys
import json
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ml.recommendation_engine.operator_advisor import STPOperatorAdvisor

APP_DIR = os.path.abspath(os.path.dirname(__file__))
UI_DIR = os.path.join(APP_DIR, "ui")
DATA_PATH = os.path.join(APP_DIR, "data", "processed", "treated_water_clean.csv")

app = Flask(__name__, static_folder="ui")

# Load historical 7-day window once for trend analysis
history_df = None
if os.path.exists(DATA_PATH):
    try:
        raw_df = pd.read_csv(DATA_PATH)
        history_df = raw_df.tail(7).copy()
        print(f"Loaded {len(history_df)} days of historical context from {DATA_PATH}")
    except Exception as e:
        print(f"Warning loading data: {e}")

# Initialize Operator Advisor
advisor = STPOperatorAdvisor()

@app.route("/")
def index():
    return send_from_directory(UI_DIR, "index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(UI_DIR, filename)

@app.route("/api/diagnose", methods=["POST"])
def diagnose():
    try:
        data = request.get_json() or {}
        ph = float(data.get("ph", 7.10))
        turbidity = float(data.get("turbidity", 3.5))
        tds = float(data.get("tds", 425.0))
        temp = float(data.get("temp", 25.0))

        advisory = advisor.generate_full_advisory(
            current_ph=ph,
            current_tds=tds,
            current_turbidity=turbidity,
            temperature_c=temp,
            history_df=history_df
        )

        return jsonify(advisory)
    except Exception as e:
        print(f"Error in /api/diagnose: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ONLINE",
        "system": "Smart STP Monitor",
        "phases_active": ["Phase 1 (EDA)", "Phase 2 (Soft Sensor)", "Phase 3 (Anomaly)", "Phase 4 (WQI)", "Phase 5 (Recommendations)"]
    })

def main():
    port = 5000
    print("=" * 60)
    print("  [*] Smart STP Monitor Web Application Running")
    print(f"  [*] Open URL in Browser: http://localhost:{port}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    main()
