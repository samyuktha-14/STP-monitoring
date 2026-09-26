"""
Water Quality Index (WQI) Calculator for Treated Sewage Effluent
Uses the Weighted Arithmetic Index Method adapted for STP effluent quality.
"""

from typing import Dict, Any, List


class WQICalculator:
    """
    Computes a standardized 0-100 Water Quality Index (WQI) score:
    - 90 - 100: EXCELLENT (Premium treated effluent)
    - 75 - 89 : GOOD (Compliant for all standard reuse)
    - 50 - 74 : MODERATE / FAIR (Restricted non-contact reuse)
    - 25 - 49 : POOR (Sub-standard, needs re-filtration)
    - 0  - 24 : VERY POOR / SEPTIC (Unsafe for any reuse)
    """

    def __init__(self):
        # Parameters, ideal values, standard permissible limits, and relative importance weights (sum = 1.0)
        self.standards = {
            "pH": {
                "ideal": 7.0,
                "standard": 8.5,
                "min_standard": 6.5,
                "weight": 0.20
            },
            "DO": {
                "ideal": 6.0,
                "standard": 2.0,
                "weight": 0.25
            },
            "Turbidity": {
                "ideal": 0.5,
                "standard": 5.0,
                "weight": 0.20
            },
            "TDS": {
                "ideal": 250.0,
                "standard": 800.0,
                "weight": 0.15
            },
            "BOD": {
                "ideal": 5.0,
                "standard": 10.0,
                "weight": 0.10
            },
            "COD": {
                "ideal": 20.0,
                "standard": 50.0,
                "weight": 0.10
            }
        }

    def compute_sub_indices(self, readings: Dict[str, float]) -> Dict[str, float]:
        """
        Computes sub-index quality rating (q_i) from 0 to 100 for each parameter.
        Higher is better (100 = ideal, 0 = severe violation).
        """
        sub_indices = {}

        # 1. pH Sub-index
        if "pH" in readings:
            ph = readings["pH"]
            if 6.5 <= ph <= 8.5:
                # Perfect around 7.0
                dev = abs(ph - 7.0)
                q_ph = max(0.0, 100.0 - (dev / 1.5) * 40.0)
            elif ph < 6.5:
                q_ph = max(0.0, 60.0 - ((6.5 - ph) / 1.5) * 60.0)
            else:
                q_ph = max(0.0, 60.0 - ((ph - 8.5) / 1.5) * 60.0)
            sub_indices["pH"] = round(q_ph, 1)

        # 2. DO Sub-index (Higher DO is better, ideal >= 5.0)
        if "DO" in readings:
            do_val = readings["DO"]
            if do_val >= 5.0:
                q_do = 100.0
            elif do_val >= 2.0:
                q_do = 60.0 + ((do_val - 2.0) / 3.0) * 40.0
            elif do_val >= 1.0:
                q_do = 20.0 + ((do_val - 1.0) / 1.0) * 40.0
            else:
                q_do = max(0.0, do_val * 20.0)
            sub_indices["DO"] = round(q_do, 1)

        # 3. Turbidity Sub-index (Lower is better)
        if "Turbidity" in readings:
            turb = readings["Turbidity"]
            if turb <= 1.0:
                q_turb = 100.0
            elif turb <= 5.0:
                q_turb = 100.0 - ((turb - 1.0) / 4.0) * 30.0
            elif turb <= 10.0:
                q_turb = 70.0 - ((turb - 5.0) / 5.0) * 40.0
            else:
                q_turb = max(0.0, 30.0 - ((turb - 10.0) / 10.0) * 30.0)
            sub_indices["Turbidity"] = round(q_turb, 1)

        # 4. TDS Sub-index (Lower is better)
        if "TDS" in readings:
            tds = readings["TDS"]
            if tds <= 400.0:
                q_tds = 100.0
            elif tds <= 800.0:
                q_tds = 100.0 - ((tds - 400.0) / 400.0) * 30.0
            elif tds <= 1500.0:
                q_tds = 70.0 - ((tds - 800.0) / 700.0) * 40.0
            else:
                q_tds = max(0.0, 30.0 - ((tds - 1500.0) / 600.0) * 30.0)
            sub_indices["TDS"] = round(q_tds, 1)

        # 5. BOD Sub-index (Lower is better)
        if "BOD" in readings:
            bod = readings["BOD"]
            if bod <= 5.0:
                q_bod = 100.0
            elif bod <= 10.0:
                q_bod = 100.0 - ((bod - 5.0) / 5.0) * 30.0
            elif bod <= 20.0:
                q_bod = 70.0 - ((bod - 10.0) / 10.0) * 40.0
            else:
                q_bod = max(0.0, 30.0 - ((bod - 20.0) / 10.0) * 30.0)
            sub_indices["BOD"] = round(q_bod, 1)

        # 6. COD Sub-index (Lower is better)
        if "COD" in readings:
            cod = readings["COD"]
            if cod <= 25.0:
                q_cod = 100.0
            elif cod <= 50.0:
                q_cod = 100.0 - ((cod - 25.0) / 25.0) * 30.0
            elif cod <= 100.0:
                q_cod = 70.0 - ((cod - 50.0) / 50.0) * 40.0
            else:
                q_cod = max(0.0, 30.0 - ((cod - 100.0) / 50.0) * 30.0)
            sub_indices["COD"] = round(q_cod, 1)

        return sub_indices

    def calculate_wqi(self, readings: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculates overall WQI score and qualitative grading.
        """
        sub_indices = self.compute_sub_indices(readings)
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for param, q_val in sub_indices.items():
            weight = self.standards[param]["weight"]
            weighted_sum += q_val * weight
            total_weight += weight
            
        final_wqi = round(weighted_sum / total_weight, 1) if total_weight > 0 else 0.0

        if final_wqi >= 90.0:
            category = "EXCELLENT"
            grade = "A"
            description = "High-clarity, thoroughly aerated effluent. Exceeds standard reuse norms."
            color = "#10B981" # Emerald Green
        elif final_wqi >= 75.0:
            category = "GOOD"
            grade = "B"
            description = "Normal compliant treated water. Suitable for all configured non-potable reuse."
            color = "#3B82F6" # Blue
        elif final_wqi >= 50.0:
            category = "MODERATE"
            grade = "C"
            description = "Fair quality. Restricted reuse only (gardening/construction); unsuitable for flushing."
            color = "#F59E0B" # Amber
        elif final_wqi >= 25.0:
            category = "POOR"
            grade = "D"
            description = "Sub-standard quality. Secondary filtration and re-aeration required."
            color = "#EF4444" # Red
        else:
            category = "VERY_POOR"
            grade = "F"
            description = "Severely degraded / septic effluent. Halt discharge immediately."
            color = "#7F1D1D" # Dark Red

        return {
            "wqi_score": final_wqi,
            "grade": grade,
            "category": category,
            "description": description,
            "badge_color": color,
            "sub_indices": sub_indices
        }
