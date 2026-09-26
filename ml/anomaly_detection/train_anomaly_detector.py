"""
Train and Evaluate Multi-Sensor Isolation Forest Anomaly Detector on 4-Year STP Dataset
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ml.soft_sensor.physics_do_estimator import PhysicsDOEstimator

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "treated_water_clean.csv"))
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "saved_models"))
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "experiments", "results"))

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def train_isolation_forest():
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    do_estimator = PhysicsDOEstimator()
    formula_dos = []
    
    for _, row in df.iterrows():
        res = do_estimator.estimate(
            ph=row["Treated pH"],
            tds_mg_l=row["Treated TDS (mg/L)"],
            turbidity_ntu=row["Treated Turbidity (NTU)"],
            temperature_c=25.0
        )
        formula_dos.append(res["do_estimated_mg_l"])
        
    df["Formula_DO"] = formula_dos
    df["Turb_TDS_Interaction"] = (df["Treated Turbidity (NTU)"] * df["Treated TDS (mg/L)"]) / 1000.0
    
    features = [
        "Treated pH",
        "Treated TDS (mg/L)",
        "Treated Turbidity (NTU)",
        "Formula_DO",
        "Turb_TDS_Interaction"
    ]
    
    X = df[features].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train Isolation Forest with contamination=0.035 (reflecting ~3.5% expected operational excursions)
    iso_forest = IsolationForest(
        n_estimators=150,
        contamination=0.035,
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_scaled)
    
    # Save model and scaler
    model_save_path = os.path.join(MODEL_DIR, "isolation_forest.pkl")
    scaler_save_path = os.path.join(MODEL_DIR, "iforest_scaler.pkl")
    
    joblib.dump(iso_forest, model_save_path)
    joblib.dump(scaler, scaler_save_path)
    
    print(f"Saved Isolation Forest to {model_save_path}")
    print(f"Saved Scaler to {scaler_save_path}")
    
    # Run full historical evaluation
    predictions = iso_forest.predict(X_scaled)
    anomaly_indices = np.where(predictions == -1)[0]
    
    print(f"\nTotal Dataset Samples: {len(df)}")
    print(f"Total Detected Multivariate Anomalies: {len(anomaly_indices)} ({len(anomaly_indices)/len(df)*100:.2f}%)")
    
    # Save anomaly detection summary
    summary = {
        "total_samples": len(df),
        "anomalies_detected": int(len(anomaly_indices)),
        "anomaly_rate_pct": round(float(len(anomaly_indices)/len(df)*100), 2),
        "model_type": "IsolationForest (n_estimators=150, contamination=0.035)",
        "features": features,
        "sample_anomaly_dates": df["Date"].iloc[anomaly_indices[:5]].tolist()
    }
    
    summary_path = os.path.join(RESULTS_DIR, "phase3_anomaly_detection_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    print(f"Saved Anomaly Detection summary to {summary_path}")

if __name__ == "__main__":
    train_isolation_forest()
