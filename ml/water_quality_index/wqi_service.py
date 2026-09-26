"""
Integrated Water Quality Index & Reuse Assessment Service for Smart STP Monitor
"""

from typing import Dict, Any, Optional
from ml.water_quality_index.wqi_calculator import WQICalculator
from ml.water_quality_index.reuse_engine import ReuseSuitabilityEngine
from ml.soft_sensor.soft_sensor_predictor import STPSoftSensorPredictor


class STPWaterQualityService:
    """
    End-to-End Service:
    Live Sensor Inputs -> Soft Sensor Estimations -> WQI Scoring -> Reuse Suitability Matrix
    """

    def __init__(self):
        self.soft_predictor = STPSoftSensorPredictor()
        self.wqi_calculator = WQICalculator()
        self.reuse_engine = ReuseSuitabilityEngine()

    def evaluate_water(
        self,
        ph: float,
        tds_mg_l: float,
        turbidity_ntu: float,
        temperature_c: float = 25.0
    ) -> Dict[str, Any]:
        """
        Comprehensive water quality evaluation for live dashboard / mobile client.
        """
        # Step 1: Soft Sensor Predictions (DO via Formula, BOD/COD/TSS via Tuned ML)
        soft_results = self.soft_predictor.predict(
            ph=ph,
            tds_mg_l=tds_mg_l,
            turbidity_ntu=turbidity_ntu,
            temperature_c=temperature_c
        )

        estimates = soft_results["estimates"]
        do_val = estimates["DO"]["value_mg_l"]
        tss_val = estimates["TSS"]["value_mg_l"]
        bod_val = estimates["BOD"]["value_mg_l"]
        cod_val = estimates["COD"]["value_mg_l"]

        # Flatten parameter dictionary for WQI and Reuse engines
        eval_readings = {
            "pH": float(ph),
            "TDS": float(tds_mg_l),
            "Turbidity": float(turbidity_ntu),
            "DO": float(do_val),
            "TSS": float(tss_val),
            "BOD": float(bod_val),
            "COD": float(cod_val)
        }

        # Step 2: Compute WQI Score & Sub-indices
        wqi_result = self.wqi_calculator.calculate_wqi(eval_readings)

        # Step 3: Compute Reuse Suitability Matrix
        reuse_result = self.reuse_engine.evaluate_reuse(eval_readings)

        return {
            "sensor_inputs": soft_results["inputs"],
            "soft_sensor_estimates": estimates,
            "wqi_summary": wqi_result,
            "reuse_suitability": reuse_result
        }
