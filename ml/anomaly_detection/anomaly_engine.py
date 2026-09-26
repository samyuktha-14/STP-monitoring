"""
Unified STP Multi-Layer Anomaly Detection & Root-Cause Diagnosis Engine
Combines:
- Layer 1: CPCB Regulatory Rule Checker
- Layer 2: Dynamic Statistical Z-Score & Rate-of-Change Filter
- Layer 3: Unsupervised Isolation Forest Multi-Sensor Model
- Layer 4: Physical Root-Cause Attribution & Operator Action Recommendation
"""

import os
import sys
from typing import Dict, Any, List, Optional

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ml.anomaly_detection.cpcb_rules import CPCBRuleChecker
from ml.anomaly_detection.statistical_detector import StatisticalAnomalyDetector
from ml.anomaly_detection.isolation_forest_detector import MultiSensorIsolationForest
from ml.soft_sensor.physics_do_estimator import PhysicsDOEstimator


class STPAnomalyEngine:
    """
    Production-grade multi-layer anomaly engine for Sewage Treatment Plants.
    """

    def __init__(self):
        self.cpcb_checker = CPCBRuleChecker()
        self.stat_detector = StatisticalAnomalyDetector()
        self.ml_detector = MultiSensorIsolationForest()
        self.do_estimator = PhysicsDOEstimator()

    def diagnose(
        self,
        ph: float,
        tds_mg_l: float,
        turbidity_ntu: float,
        temperature_c: float = 25.0,
        previous_readings: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive multi-layer anomaly diagnostic on incoming sensor readings.
        """
        # Step 0: Compute Formula DO & engineered interaction
        do_res = self.do_estimator.estimate(
            ph=ph,
            tds_mg_l=tds_mg_l,
            turbidity_ntu=turbidity_ntu,
            temperature_c=temperature_c
        )
        do_val = do_res["do_estimated_mg_l"]
        
        sensor_dict = {
            "Treated pH": float(ph),
            "Treated TDS (mg/L)": float(tds_mg_l),
            "Treated Turbidity (NTU)": float(turbidity_ntu),
            "Treated DO (mg/L)": float(do_val),
            "Formula_DO": float(do_val),
            "Turb_TDS_Interaction": float((turbidity_ntu * tds_mg_l) / 1000.0)
        }

        # Layer 1: CPCB Regulatory Filter
        cpcb_res = self.cpcb_checker.check_compliance(sensor_dict)

        # Layer 2: Statistical Anomaly Filter
        stat_res = self.stat_detector.check_univariate(sensor_dict, previous_readings)

        # Layer 3: Unsupervised ML Isolation Forest
        ml_res = self.ml_detector.predict_anomaly(sensor_dict)

        # Layer 4: Root-Cause Attribution & Anomaly Classification
        is_abnormal = (
            not cpcb_res["is_compliant"] or
            stat_res["is_statistically_abnormal"] or
            ml_res["is_ml_anomaly"]
        )

        anomaly_type = "NORMAL"
        severity = "NORMAL"
        root_cause = "Water quality parameters are within normal operational limits."
        action_recommendation = "Maintain standard aeration, clarifier recycling (RAS), and continuous filtration."

        if is_abnormal:
            # Diagnose specific process failure patterns
            turbidity = sensor_dict["Treated Turbidity (NTU)"]
            tds = sensor_dict["Treated TDS (mg/L)"]
            
            # Pattern A: Aeration Failure / Septic Conditions (Low DO, acidic drift)
            if do_val < 1.8 and ph < 6.8:
                anomaly_type = "PROCESS_UPSET"
                severity = "CRITICAL"
                root_cause = "Aeration Tank Failure / Septic Odor Risk (Low DO + Acidic Drop)"
                action_recommendation = "1. Check air blowers and diffusers immediately. 2. Increase dissolved oxygen delivery to aeration basin."
            
            # Pattern B: Clarifier Sludge Washout / Filter Breakthrough (High Turbidity + elevated solids)
            elif turbidity > 6.0:
                anomaly_type = "PROCESS_UPSET"
                severity = "CRITICAL" if turbidity > 10.0 else "WARNING"
                root_cause = f"Secondary Clarifier Sludge Carryover / Filter Breakthrough (Turbidity: {turbidity:.1f} NTU)"
                action_recommendation = "1. Inspect clarifier sludge blanket level. 2. Backwash sand/carbon filters. 3. Adjust RAS (Return Activated Sludge) recycle rate."

            # Pattern C: High Salinity Shock Load (Excessive TDS)
            elif tds > 550.0:
                anomaly_type = "PROCESS_UPSET"
                severity = "WARNING" if tds < 800 else "CRITICAL"
                root_cause = f"Inlet Salinity / High TDS Shock Load ({tds:.0f} mg/L)"
                action_recommendation = "1. Check raw sewage inlet for chemical dumping or water softener regeneration discharge. 2. Divert to equalization tank if TDS > 1500."

            # Pattern D: Isolated Single-Sensor Glitch / Spike
            elif stat_res["is_statistically_abnormal"] and len(stat_res["anomalies"]) == 1:
                single_anomaly = stat_res["anomalies"][0]
                anomaly_type = "SENSOR_FAULT"
                severity = "WARNING"
                root_cause = f"Isolated Sensor Anomaly on {single_anomaly['parameter']} ({single_anomaly['detail']})"
                action_recommendation = f"Inspect, clean, and recalibrate the {single_anomaly['parameter']} physical sensor probe."

            # Pattern E: General Regulatory Compliance Breach
            elif not cpcb_res["is_compliant"]:
                anomaly_type = "REGULATORY_BREACH"
                severity = "CRITICAL"
                root_cause = f"CPCB Statutory Limit Violation: {', '.join([v['message'] for v in cpcb_res['violations']])}"
                action_recommendation = "Halt treated effluent discharge to public reuse immediately; route water back to equalization basin."
            
            else:
                anomaly_type = "UNUSUAL_PROCESS_DEVIATION"
                severity = "LOW"
                root_cause = "Subtle multi-sensor multivariate deviation detected by Isolation Forest."
                action_recommendation = "Monitor plant parameters for continued drift over next 2 operational cycles."

        return {
            "is_anomaly": is_abnormal,
            "overall_status": severity,
            "anomaly_type": anomaly_type,
            "severity_level": severity,
            "root_cause_diagnosis": root_cause,
            "actionable_recommendation": action_recommendation,
            "layer_results": {
                "cpcb_regulatory": cpcb_res,
                "statistical_univariate": stat_res,
                "isolation_forest_ml": ml_res
            },
            "sensor_readings": {
                "ph": round(ph, 2),
                "tds_mg_l": round(tds_mg_l, 1),
                "turbidity_ntu": round(turbidity_ntu, 2),
                "estimated_do_mg_l": round(do_val, 2)
            }
        }
