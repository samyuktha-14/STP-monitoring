"""
Unified Production Operator Advisor Service
Combines Real-time Sensors, Soft Sensors, Anomaly Diagnosis, Trend Analytics, and Actionable Recommendations.
"""

import pandas as pd
from typing import Dict, Any, List, Optional

from ml.soft_sensor.soft_sensor_predictor import STPSoftSensorPredictor
from ml.anomaly_detection.anomaly_engine import STPAnomalyEngine
from ml.water_quality_index.wqi_service import STPWaterQualityService
from ml.recommendation_engine.trend_analyzer import TrendAnalyzer
from ml.recommendation_engine.expert_rules import STPExpertRules


class STPOperatorAdvisor:
    """
    Complete operational insight and recommendation service for STP operators and managers.
    """

    def __init__(self):
        self.soft_predictor = STPSoftSensorPredictor()
        self.anomaly_engine = STPAnomalyEngine()
        self.wqi_service = STPWaterQualityService()
        self.trend_analyzer = TrendAnalyzer()
        self.expert_rules = STPExpertRules()

    def generate_full_advisory(
        self,
        current_ph: float,
        current_tds: float,
        current_turbidity: float,
        temperature_c: float = 25.0,
        history_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Produces full operational dashboard payload:
        Live Status -> Trend Direction -> Soft Sensor Estimates -> WQI & Reuse -> Prioritized Action Checklist
        """
        # 1. Soft Sensor Predictions
        soft_res = self.soft_predictor.predict(
            ph=current_ph,
            tds_mg_l=current_tds,
            turbidity_ntu=current_turbidity,
            temperature_c=temperature_c
        )
        estimates = soft_res["estimates"]

        # Flatten current reading dictionary
        readings_dict = {
            "pH": current_ph,
            "TDS": current_tds,
            "Turbidity": current_turbidity,
            "DO": estimates["DO"]["value_mg_l"],
            "TSS": estimates["TSS"]["value_mg_l"],
            "BOD": estimates["BOD"]["value_mg_l"],
            "COD": estimates["COD"]["value_mg_l"]
        }

        # 2. Anomaly Engine Diagnosis
        anomaly_res = self.anomaly_engine.diagnose(
            ph=current_ph,
            tds_mg_l=current_tds,
            turbidity_ntu=current_turbidity,
            temperature_c=temperature_c
        )

        # 3. WQI & Reuse Suitability
        wqi_res = self.wqi_service.evaluate_water(
            ph=current_ph,
            tds_mg_l=current_tds,
            turbidity_ntu=current_turbidity,
            temperature_c=temperature_c
        )

        # 4. Multi-Scale Trend & Drift Analysis
        if history_df is not None and len(history_df) >= 3:
            trend_res = self.trend_analyzer.analyze_multi_parameter_window(history_df, window_size=7)
        else:
            trend_res = {
                "window_days": 1,
                "parameter_trends": {},
                "active_early_warnings": [],
                "has_degradation_trend": False
            }

        # 5. Expert Action Checklist Generation
        recommendation_res = self.expert_rules.evaluate_plant_condition(
            readings=readings_dict,
            trend_data=trend_res,
            anomaly_data=anomaly_res
        )

        return {
            "plant_health_summary": {
                "operational_status": recommendation_res["overall_status"],
                "status_color": recommendation_res["status_color"],
                "headline": recommendation_res["headline_summary"],
                "wqi_score": wqi_res["wqi_summary"]["wqi_score"],
                "wqi_grade": wqi_res["wqi_summary"]["grade"],
                "anomaly_type": anomaly_res["anomaly_type"]
            },
            "live_and_estimated_parameters": readings_dict,
            "trend_analysis": trend_res,
            "reuse_recommendation": wqi_res["reuse_suitability"]["overall_recommendation"],
            "prioritized_action_checklist": recommendation_res["action_checklist"],
            "affected_equipment_units": recommendation_res["affected_equipment_units"],
            "root_cause_diagnosis": anomaly_res["root_cause_diagnosis"]
        }
