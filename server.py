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
from ml.soft_sensor.tss_estimator import estimate_tss, TurbidityTSSEstimator, SCIENTIFIC_LIMITATION_DISCLAIMER

APP_DIR = os.path.abspath(os.path.dirname(__file__))
UI_DIR = os.path.join(APP_DIR, "ui")
DATA_PATH = os.path.join(APP_DIR, "data", "processed", "treated_water_clean.csv")

app = Flask(__name__, static_folder="ui")

# In-memory latest reading cache (ESP32 runtime / sensor buffer)
latest_reading_store = {
    "pH": 7.10,
    "TDS": 425.0,
    "turbidity": 3.5,
    "temperature_c": 25.0,
    "tss_estimated": 9.24,
    "tss_source": "turbidity_formula",
    "tss_metadata": {
        "unit": "mg/L",
        "formula": "TSS = 1.15 * Turbidity + 5.22",
        "is_estimated": True,
        "description": SCIENTIFIC_LIMITATION_DISCLAIMER
    },
    "sensor_status": {
        "pH": "MEASURED",
        "TDS": "MEASURED",
        "turbidity": "MEASURED",
        "TSS": "ESTIMATED"
    }
}

# Optional MongoDB Client integration (if configured)
mongo_client = None
mongo_col = None
try:
    from pymongo import MongoClient
    mongo_uri = os.environ.get("MONGO_URI")
    if mongo_uri:
        mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        mongo_db = mongo_client.get_database(os.environ.get("MONGO_DB", "stp_monitoring"))
        mongo_col = mongo_db.get_collection("sensor_readings")
except Exception as e:
    # MongoDB is optional; fallback to in-memory store cleanly
    pass

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

@app.route("/api/estimate/tss", methods=["GET", "POST"])
def api_estimate_tss():
    """
    Direct endpoint for real-time Turbidity -> TSS estimation.
    Accepts GET query param ?turbidity=... or POST JSON body {"turbidity": ...}.
    """
    raw_turbidity = None
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        raw_turbidity = data.get("turbidity")
    else:
        raw_turbidity = request.args.get("turbidity")
        
    result = estimate_tss(raw_turbidity)
    return jsonify(result)

@app.route("/api/readings/latest", methods=["GET"])
def get_latest_readings():
    """
    Returns the latest sensor readings including measured values and estimated TSS.
    """
    return jsonify(latest_reading_store)

@app.route("/api/readings", methods=["POST"])
def ingest_sensor_reading():
    """
    ESP32 Ingestion Endpoint:
    Accepts live sensor payload: pH, TDS, Turbidity
    Calculates Estimated TSS via validated formula and updates live storage.
    """
    global latest_reading_store
    try:
        data = request.get_json() or {}
        raw_ph = data.get("pH", data.get("ph"))
        raw_tds = data.get("TDS", data.get("tds"))
        raw_turb = data.get("turbidity", data.get("Turbidity"))
        raw_temp = data.get("temp", data.get("temperature_c", 25.0))

        # Validate inputs
        ph = float(raw_ph) if raw_ph is not None else 7.1
        tds = float(raw_tds) if raw_tds is not None else 425.0
        temp = float(raw_temp) if raw_temp is not None else 25.0
        
        # Calculate real-time TSS estimate from turbidity
        tss_calc = estimate_tss(raw_turb)
        
        record = {
            "pH": ph,
            "TDS": tds,
            "turbidity": tss_calc["turbidity"],
            "temperature_c": temp,
            "tss_estimated": tss_calc["tss"],
            "tss_display": tss_calc["tss_display"],
            "tss_source": tss_calc["tss_source"],
            "tss_status": tss_calc["status"],
            "tss_reason": tss_calc.get("reason", ""),
            "tss_metadata": {
                "unit": tss_calc["tss_unit"],
                "formula": tss_calc["formula"],
                "is_estimated": True,
                "description": tss_calc["description"]
            },
            "sensor_status": {
                "pH": "MEASURED",
                "TDS": "MEASURED",
                "turbidity": "MEASURED",
                "TSS": "ESTIMATED"
            },
            "sensor_provenance": {
                "pH": "MEASURED",
                "TDS": "MEASURED",
                "turbidity": "MEASURED",
                "TSS": "ESTIMATED"
            }
        }
        
        # Update in-memory latest cache
        latest_reading_store = record
        
        # Optional MongoDB storage if active
        if mongo_col is not None:
            try:
                mongo_col.insert_one(dict(record))
            except Exception as me:
                print(f"MongoDB insert error (non-fatal): {me}")

        return jsonify({
            "status": "success",
            "message": "Sensor reading processed and TSS estimated",
            "reading": record
        })
    except Exception as e:
        print(f"Error in /api/readings: {e}")
        return jsonify({"error": str(e)}), 400

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

        # Attach explicit TSS estimation metadata
        tss_meta = estimate_tss(turbidity)
        advisory["tss_estimation_details"] = tss_meta

        return jsonify(advisory)
    except Exception as e:
        print(f"Error in /api/diagnose: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ONLINE",
        "system": "Smart STP Monitor",
        "phases_active": ["Phase 1 (EDA)", "Phase 2 (Soft Sensor)", "Phase 3 (Anomaly)", "Phase 4 (WQI)", "Phase 5 (Recommendations)"],
        "tss_feature": {
            "mode": "VALIDATED_EMPIRICAL_FORMULA",
            "formula": "TSS = 1.15 * Turbidity + 5.22",
            "source": "estimated_from_turbidity",
            "description": SCIENTIFIC_LIMITATION_DISCLAIMER
        }
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
