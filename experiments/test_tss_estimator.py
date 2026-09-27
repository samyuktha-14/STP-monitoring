"""
Unit & Integration Tests for Turbidity -> TSS Estimation Feature
Smart STP Monitor
"""

import os
import sys
import unittest
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.soft_sensor.tss_estimator import (
    TurbidityTSSEstimator,
    estimate_tss,
    DEFAULT_TSS_SLOPE_A,
    DEFAULT_TSS_INTERCEPT_B,
    SCIENTIFIC_LIMITATION_DISCLAIMER
)
from ml.soft_sensor.soft_sensor_predictor import STPSoftSensorPredictor
from server import app


class TestTurbidityTSSEstimator(unittest.TestCase):
    """
    Unit tests for Turbidity -> TSS estimation module.
    """

    def setUp(self):
        self.estimator = TurbidityTSSEstimator()
        self.a = DEFAULT_TSS_SLOPE_A      # 1.15
        self.b = DEFAULT_TSS_INTERCEPT_B  # 5.22

    def test_1_normal_turbidity_value(self):
        """Test with typical treated water turbidity readings (e.g., 4.8 NTU and 3.5 NTU)."""
        # Test 4.8 NTU: 1.15 * 4.8 + 5.22 = 5.52 + 5.22 = 10.74 mg/L
        res_4_8 = self.estimator.estimate(4.8)
        self.assertEqual(res_4_8["status"], "valid")
        self.assertEqual(res_4_8["turbidity"], 4.8)
        self.assertEqual(res_4_8["turbidity_unit"], "NTU")
        self.assertAlmostEqual(res_4_8["tss"], 10.74, places=2)
        self.assertEqual(res_4_8["tss_unit"], "mg/L")
        self.assertEqual(res_4_8["tss_source"], "estimated_from_turbidity")
        self.assertTrue(res_4_8["is_estimated"])
        self.assertIn("Estimated TSS derived from", res_4_8["description"])

        # Test 3.5 NTU: 1.15 * 3.5 + 5.22 = 4.025 + 5.22 = 9.245 -> 9.24 / 9.25 mg/L
        res_3_5 = estimate_tss(3.5)
        self.assertEqual(res_3_5["status"], "valid")
        self.assertAlmostEqual(res_3_5["tss"], round(1.15 * 3.5 + 5.22, 2), places=2)

    def test_2_zero_turbidity(self):
        """Test zero turbidity (0.0 NTU baseline)."""
        # 1.15 * 0.0 + 5.22 = 5.22 mg/L
        res_zero = self.estimator.estimate(0.0)
        self.assertEqual(res_zero["status"], "valid")
        self.assertEqual(res_zero["turbidity"], 0.0)
        self.assertAlmostEqual(res_zero["tss"], 5.22, places=2)
        self.assertEqual(res_zero["tss_source"], "estimated_from_turbidity")

    def test_3_missing_or_none_value(self):
        """Test missing / None / null input."""
        res_none = self.estimator.estimate(None)
        self.assertEqual(res_none["status"], "unavailable")
        self.assertIsNone(res_none["tss"])
        self.assertEqual(res_none["tss_display"], "Unavailable")
        self.assertEqual(res_none["reason"], "Turbidity reading unavailable")
        self.assertEqual(res_none["tss_source"], "estimated_from_turbidity")

    def test_4_negative_turbidity(self):
        """Test physically impossible negative turbidity (e.g. -2.5 NTU)."""
        res_neg = self.estimator.estimate(-2.5)
        self.assertEqual(res_neg["status"], "unavailable")
        self.assertIsNone(res_neg["tss"])
        self.assertEqual(res_neg["tss_display"], "Unavailable")
        self.assertIn("Negative turbidity is physically invalid", res_neg["reason"])

    def test_5_non_numeric_and_invalid_inputs(self):
        """Test non-numeric strings, lists, dictionaries, NaN."""
        for invalid_input in ["invalid_str", "abc", [1, 2], {"turb": 5}, float("nan")]:
            res = self.estimator.estimate(invalid_input)
            self.assertEqual(res["status"], "unavailable", f"Failed for input: {invalid_input}")
            self.assertIsNone(res["tss"], f"Expected None TSS for: {invalid_input}")
            self.assertEqual(res["tss_display"], "Unavailable")


class TestFlaskAPIIntegration(unittest.TestCase):
    """
    End-to-end integration tests for complete flow:
    ESP32 / Sensor Input -> Flask API -> Turbidity -> TSS Formula -> Estimated TSS -> API Response
    """

    def setUp(self):
        self.client = app.test_client()

    def test_direct_tss_estimate_endpoint_get(self):
        """Test GET /api/estimate/tss?turbidity=4.8"""
        response = self.client.get("/api/estimate/tss?turbidity=4.8")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["turbidity"], 4.8)
        self.assertAlmostEqual(data["tss"], 10.74, places=2)
        self.assertEqual(data["tss_source"], "estimated_from_turbidity")
        self.assertTrue(data["is_estimated"])

    def test_direct_tss_estimate_endpoint_post(self):
        """Test POST /api/estimate/tss with JSON payload"""
        response = self.client.post("/api/estimate/tss", json={"turbidity": 2.0})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # 1.15 * 2.0 + 5.22 = 7.52 mg/L
        self.assertAlmostEqual(data["tss"], 7.52, places=2)
        self.assertEqual(data["status"], "valid")

    def test_direct_tss_estimate_missing_handling(self):
        """Test GET /api/estimate/tss with missing / empty param"""
        response = self.client.get("/api/estimate/tss")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "unavailable")
        self.assertIsNone(data["tss"])
        self.assertEqual(data["reason"], "Turbidity reading unavailable")

    def test_esp32_sensor_ingestion_endpoint(self):
        """
        Test ESP32 sensor reading ingestion:
        POST /api/readings -> pH, TDS, Turbidity -> Calculates Estimated TSS and updates storage
        """
        payload = {
            "pH": 7.30,
            "TDS": 450.0,
            "turbidity": 4.0,
            "temp": 26.0
        }
        response = self.client.post("/api/readings", json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        reading = data["reading"]
        self.assertEqual(reading["pH"], 7.30)
        self.assertEqual(reading["TDS"], 450.0)
        self.assertEqual(reading["turbidity"], 4.0)
        # 1.15 * 4.0 + 5.22 = 9.82 mg/L
        self.assertAlmostEqual(reading["tss_estimated"], 9.82, places=2)
        self.assertEqual(reading["tss_source"], "estimated_from_turbidity")
        self.assertEqual(reading["sensor_provenance"]["TSS"], "ESTIMATED")
        self.assertEqual(reading["sensor_provenance"]["turbidity"], "MEASURED")

    def test_latest_readings_endpoint(self):
        """Test GET /api/readings/latest returns latest live reading with TSS estimate"""
        response = self.client.get("/api/readings/latest")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("tss_estimated", data)
        self.assertIn("tss_source", data)
        self.assertIn("sensor_status", data)

    def test_full_diagnose_pipeline(self):
        """Test POST /api/diagnose includes correctly estimated TSS and metadata"""
        payload = {
            "ph": 7.15,
            "turbidity": 4.8,
            "tds": 410.0,
            "temp": 25.0
        }
        response = self.client.post("/api/diagnose", json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify live & estimated parameters
        live_params = data["live_and_estimated_parameters"]
        self.assertAlmostEqual(live_params["TSS"], 10.74, places=2)
        
        # Verify detailed TSS estimation metadata attached
        tss_meta = data["tss_estimation_details"]
        self.assertEqual(tss_meta["turbidity"], 4.8)
        self.assertEqual(tss_meta["tss_source"], "estimated_from_turbidity")
        self.assertTrue(tss_meta["is_estimated"])


if __name__ == "__main__":
    unittest.main()
