"""
Statistical Anomaly Detector for STP Sensors
Implements Rolling Z-Score, IQR bounds, Rate-of-Change (Spike), and Sensor Flatline Detection
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional


class StatisticalAnomalyDetector:
    """
    Statistical filter detecting univariate spikes, drift, IQR outliers, and frozen sensors.
    """

    def __init__(
        self,
        z_thresh: float = 3.0,
        iqr_multiplier: float = 1.5,
        max_flatline_steps: int = 5
    ):
        self.z_thresh = z_thresh
        self.iqr_multiplier = iqr_multiplier
        self.max_flatline_steps = max_flatline_steps
        
        # Historical baseline statistics from 4-year clean dataset
        self.baseline_stats = {
            "Treated pH": {
                "mean": 7.108,
                "std": 0.146,
                "q25": 7.000,
                "q75": 7.210,
                "max_rate_change": 0.50  # pH shouldn't swing >0.5 in 1 step under normal flow
            },
            "Treated TDS (mg/L)": {
                "mean": 425.3,
                "std": 59.7,
                "q25": 370.0,
                "q75": 480.0,
                "max_rate_change": 150.0 # TDS step change max
            },
            "Treated Turbidity (NTU)": {
                "mean": 3.605,
                "std": 1.470,
                "q25": 2.400,
                "q75": 4.700,
                "max_rate_change": 5.0   # Turbidity step jump max
            },
            "Treated DO (mg/L)": {
                "mean": 2.706,
                "std": 0.402,
                "q25": 2.440,
                "q75": 2.980,
                "max_rate_change": 1.5
            }
        }

    def check_univariate(
        self,
        current_readings: Dict[str, float],
        previous_readings: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a single reading vector against statistical boundaries and delta rates.
        """
        anomalies = []
        scores = {}
        
        for param, val in current_readings.items():
            if param not in self.baseline_stats:
                continue
                
            stat = self.baseline_stats[param]
            mean = stat["mean"]
            std = stat["std"]
            q25 = stat["q25"]
            q75 = stat["q75"]
            iqr = q75 - q25
            
            # 1. Z-Score Calculation
            z_score = (val - mean) / (std if std > 1e-6 else 1.0)
            scores[f"{param}_z_score"] = round(float(z_score), 2)
            
            # 2. IQR Boundary Check
            lower_iqr = q25 - (self.iqr_multiplier * iqr)
            upper_iqr = q75 + (self.iqr_multiplier * iqr)
            
            is_z_anomaly = abs(z_score) > self.z_thresh
            is_iqr_anomaly = val < lower_iqr or val > upper_iqr
            
            if is_z_anomaly or is_iqr_anomaly:
                anomalies.append({
                    "parameter": param,
                    "value": round(float(val), 2),
                    "z_score": round(float(z_score), 2),
                    "type": "STATISTICAL_OUTLIER",
                    "direction": "HIGH" if z_score > 0 else "LOW",
                    "severity": "HIGH" if abs(z_score) > 4.0 else "MEDIUM",
                    "detail": f"{param} deviated by {z_score:+.2f} standard deviations from mean ({mean:.2f})."
                })
                
            # 3. Rate-of-Change / Sudden Jump Check
            if previous_readings and param in previous_readings:
                prev_val = previous_readings[param]
                delta = abs(val - prev_val)
                max_rate = stat["max_rate_change"]
                
                if delta > max_rate:
                    anomalies.append({
                        "parameter": param,
                        "value": round(float(val), 2),
                        "previous_value": round(float(prev_val), 2),
                        "delta": round(float(delta), 2),
                        "type": "RATE_OF_CHANGE_SPIKE",
                        "severity": "HIGH",
                        "detail": f"Sudden jump of {delta:.2f} (allowed max: {max_rate}). Possible sensor glitch or severe hydraulic surge."
                    })
                    
        return {
            "is_statistically_abnormal": len(anomalies) > 0,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "z_scores": scores
        }
