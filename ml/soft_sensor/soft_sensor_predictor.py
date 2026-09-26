"""
Unified Soft Sensor Predictor for Smart STP Monitor
Uses:
- DO: Formula Only (Benson-Krause & Physicochemical Aeration Balance)
- BOD, COD, TSS: Tuned Machine Learning Models
"""

import os
import sys
import json
import joblib
import numpy as np
from typing import Dict, Any, Optional

from ml.soft_sensor.physics_do_estimator import PhysicsDOEstimator

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "saved_models"))

class STPSoftSensorPredictor:
    """
    Production Predictor for Smart STP Monitor:
    - DO calculated strictly via First-Principles Physical Formula.
    - BOD, COD, TSS estimated via tuned ML models taking Live Sensors + Formula DO.
    """
    
    def __init__(self):
        self.do_estimator = PhysicsDOEstimator()
        
        # Load scaler and models
        scaler_path = os.path.join(MODEL_DIR, "ml_feature_scaler.pkl")
        self.scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None
        
        self.models = {}
        for target in ["bod", "cod", "tss"]:
            model_path = os.path.join(MODEL_DIR, f"{target}_best_model.pkl")
            if os.path.exists(model_path):
                self.models[target.upper()] = joblib.load(model_path)

    def predict(
        self,
        ph: float,
        tds_mg_l: float,
        turbidity_ntu: float,
        temperature_c: float = 25.0
    ) -> Dict[str, Any]:
        # 1. DO via FORMULA ONLY
        do_res = self.do_estimator.estimate(
            ph=ph,
            tds_mg_l=tds_mg_l,
            turbidity_ntu=turbidity_ntu,
            temperature_c=temperature_c
        )
        do_val = do_res["do_estimated_mg_l"]
        do_sat = do_res["do_saturation_mg_l"]
        
        # 2. Build feature vector for ML models
        # Features: [Treated_pH, Treated_TDS, Treated_Turbidity, Formula_DO, DO_Deficit, pH_Deviation, Turb_TDS_Interaction]
        do_deficit = max(0.0, do_sat - do_val)
        ph_dev = abs(ph - 7.0)
        turb_tds_inter = (turbidity_ntu * tds_mg_l) / 1000.0
        
        raw_features = np.array([[ph, tds_mg_l, turbidity_ntu, do_val, do_deficit, ph_dev, turb_tds_inter]])
        
        if self.scaler is not None:
            scaled_features = self.scaler.transform(raw_features)
        else:
            scaled_features = raw_features
            
        estimates = {
            "DO": {
                "value_mg_l": do_val,
                "saturation_pct": do_res["saturation_pct"],
                "saturation_limit_mg_l": do_sat,
                "model_type": "ENGINEERING_FORMULA_ONLY",
                "formula": "Benson-Krause Saturation & Physicochemical Transfer Model",
                "status": do_res["status"]
            }
        }
        
        # 3. Predict BOD, COD, TSS via tuned ML models
        for target in ["TSS", "BOD", "COD"]:
            if target in self.models:
                pred_val = float(self.models[target].predict(scaled_features)[0])
                # Ensure non-negative bounds
                pred_val = max(0.1, round(pred_val, 2))
                estimates[target] = {
                    "value_mg_l": pred_val,
                    "unit": "mg/L",
                    "model_type": f"TUNED_ML_{type(self.models[target]).__name__}",
                    "method": "Supervised ML (Tuned on Live Sensors + Formula DO)"
                }
                
        return {
            "inputs": {
                "ph": round(float(ph), 2),
                "tds_mg_l": round(float(tds_mg_l), 1),
                "turbidity_ntu": round(float(turbidity_ntu), 2),
                "temperature_c": round(float(temperature_c), 1)
            },
            "estimates": estimates
        }
