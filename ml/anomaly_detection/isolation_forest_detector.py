"""
Unsupervised Isolation Forest Anomaly Detector for STP Multi-Sensor Correlation
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "saved_models"))

class MultiSensorIsolationForest:
    """
    Unsupervised multi-variate anomaly detector identifying non-linear correlation breakdowns across sensors.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.path.join(MODEL_DIR, "isolation_forest.pkl")
        self.scaler_path = os.path.join(MODEL_DIR, "iforest_scaler.pkl")
        self.model = None
        self.scaler = None
        self.feature_names = [
            "Treated pH",
            "Treated TDS (mg/L)",
            "Treated Turbidity (NTU)",
            "Formula_DO",
            "Turb_TDS_Interaction"
        ]
        self._load()

    def _load(self):
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)

    def predict_anomaly(self, feature_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Predicts whether the multi-sensor vector is an anomaly using the trained Isolation Forest.
        """
        if self.model is None or self.scaler is None:
            return {
                "is_ml_anomaly": False,
                "anomaly_score": 0.0,
                "confidence": "MODEL_NOT_LOADED"
            }
            
        # Build feature vector
        vector = []
        for feat in self.feature_names:
            vector.append(feature_dict.get(feat, 0.0))
            
        x_raw = np.array([vector])
        x_scaled = self.scaler.transform(x_raw)
        
        # Isolation Forest prediction: 1 = Normal, -1 = Anomaly
        pred = self.model.predict(x_scaled)[0]
        # score_samples: more negative = more abnormal, around 0 is boundary
        raw_score = float(self.model.score_samples(x_scaled)[0])
        
        # Normalize anomaly score to [0.0, 1.0] (0 = completely normal, 1 = severe anomaly)
        # raw_score is typically between -0.8 and -0.3
        norm_anomaly_score = float(np.clip(1.0 - ((raw_score + 0.7) / 0.4), 0.0, 1.0))
        is_anomaly = pred == -1
        
        return {
            "is_ml_anomaly": bool(is_anomaly),
            "anomaly_score": round(norm_anomaly_score, 3),
            "raw_decision_score": round(raw_score, 4),
            "classification": "ANOMALY" if is_anomaly else "NORMAL"
        }
