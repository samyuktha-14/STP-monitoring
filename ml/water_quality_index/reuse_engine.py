"""
STP Treated Effluent Reuse Suitability Engine
Evaluates compliance across 5 specific non-potable reuse categories.
"""

from typing import Dict, Any, List


class ReuseSuitabilityEngine:
    """
    Evaluates treated water against Indian CPCB, MoHUA (Ministry of Housing and Urban Affairs),
    and international non-potable water reuse standards.
    """

    REUSE_CRITERIA = {
        "Toilet Flushing": {
            "description": "Dual-plumbing indoor toilet and urinal flushing (high human exposure)",
            "rules": {
                "pH": (6.5, 8.5),
                "Turbidity": 2.0,      # Max 2.0 NTU (Aesthetics & odor prevention)
                "DO": 2.0,             # Min 2.0 mg/L
                "TDS": 1000.0,         # Max 1000 mg/L
                "BOD": 10.0,           # Max 10 mg/L
                "COD": 50.0            # Max 50 mg/L
            }
        },
        "Gardening & Landscaping": {
            "description": "Apartment lawns, public parks, green belts, and landscape irrigation",
            "rules": {
                "pH": (6.5, 8.5),
                "Turbidity": 5.0,      # Max 5.0 NTU
                "DO": 1.5,             # Min 1.5 mg/L
                "TDS": 1500.0,         # Max 1500 mg/L (Prevent plant salinity stress)
                "BOD": 20.0,           # Max 20 mg/L
                "COD": 100.0           # Max 100 mg/L
            }
        },
        "HVAC Cooling Towers": {
            "description": "Industrial/Commercial HVAC chillers and cooling tower make-up water",
            "rules": {
                "pH": (7.0, 8.2),      # Tight pH control (Prevent scale & corrosion)
                "Turbidity": 2.0,      # Max 2.0 NTU
                "DO": 2.0,             # Min 2.0 mg/L
                "TDS": 800.0,          # Max 800 mg/L (Prevent heat exchanger scaling)
                "BOD": 10.0,           # Max 10 mg/L
                "COD": 50.0            # Max 50 mg/L
            }
        },
        "Construction & Dust Control": {
            "description": "Concrete batching, curing, and road dust suppression",
            "rules": {
                "pH": (6.0, 9.0),
                "Turbidity": 15.0,     # Max 15.0 NTU
                "DO": 1.0,             # Min 1.0 mg/L
                "TDS": 2000.0,         # Max 2000 mg/L
                "BOD": 30.0,           # Max 30 mg/L
                "COD": 150.0           # Max 150 mg/L
            }
        },
        "Environmental Discharge": {
            "description": "Disposal into municipal drains, lakes, or inland surface water (CPCB Schedule VI)",
            "rules": {
                "pH": (6.5, 8.5),
                "Turbidity": 10.0,     # Max 10.0 NTU
                "DO": 2.0,             # Min 2.0 mg/L
                "TDS": 2100.0,         # Max 2100 mg/L statutory limit
                "BOD": 10.0,           # Max 10 mg/L (or 20 mg/L standard)
                "COD": 50.0            # Max 50 mg/L (or 100 mg/L standard)
            }
        }
    }

    def evaluate_reuse(self, readings: Dict[str, float]) -> Dict[str, Any]:
        """
        Evaluates water readings against all 5 reuse applications.
        """
        suitability_results = {}
        suitable_count = 0

        for purpose, config in self.REUSE_CRITERIA.items():
            rules = config["rules"]
            reasons_for_rejection = []

            # pH check
            if "pH" in readings:
                ph = readings["pH"]
                min_ph, max_ph = rules["pH"]
                if ph < min_ph or ph > max_ph:
                    reasons_for_rejection.append(f"pH ({ph:.2f}) outside required range [{min_ph} - {max_ph}]")

            # Turbidity check
            if "Turbidity" in readings:
                turb = readings["Turbidity"]
                if turb > rules["Turbidity"]:
                    reasons_for_rejection.append(f"Turbidity ({turb:.1f} NTU) exceeds max allowed ({rules['Turbidity']} NTU)")

            # DO check
            if "DO" in readings:
                do_val = readings["DO"]
                if do_val < rules["DO"]:
                    reasons_for_rejection.append(f"DO ({do_val:.2f} mg/L) below minimum ({rules['DO']} mg/L)")

            # TDS check
            if "TDS" in readings:
                tds = readings["TDS"]
                if tds > rules["TDS"]:
                    reasons_for_rejection.append(f"TDS ({tds:.0f} mg/L) exceeds max allowed ({rules['TDS']} mg/L)")

            # BOD check
            if "BOD" in readings:
                bod = readings["BOD"]
                if bod > rules["BOD"]:
                    reasons_for_rejection.append(f"BOD ({bod:.1f} mg/L) exceeds max limit ({rules['BOD']} mg/L)")

            # COD check
            if "COD" in readings:
                cod = readings["COD"]
                if cod > rules["COD"]:
                    reasons_for_rejection.append(f"COD ({cod:.1f} mg/L) exceeds max limit ({rules['COD']} mg/L)")

            is_suitable = len(reasons_for_rejection) == 0
            if is_suitable:
                suitable_count += 1

            suitability_results[purpose] = {
                "suitable": is_suitable,
                "status_badge": "SUITABLE" if is_suitable else "UNSUITABLE",
                "description": config["description"],
                "rejection_reasons": reasons_for_rejection
            }

        # Best primary recommendation
        if suitability_results["Toilet Flushing"]["suitable"]:
            best_recommendation = "Safe for Full Reuse: Indoor Toilet Flushing, Gardening, & Utilities"
        elif suitability_results["Gardening & Landscaping"]["suitable"]:
            best_recommendation = "Suitable for Landscape Irrigation, Gardening, & Construction (Not for Flushing)"
        elif suitability_results["Construction & Dust Control"]["suitable"]:
            best_recommendation = "Restricted Industrial / Construction & Dust Suppression Only"
        elif suitability_results["Environmental Discharge"]["suitable"]:
            best_recommendation = "Meets CPCB Surface Water Discharge Norms (Reuse Unadvised)"
        else:
            best_recommendation = "Unsafe for Reuse or Discharge — Reroute to Equalization Tank"

        return {
            "total_suitable_purposes": suitable_count,
            "overall_recommendation": best_recommendation,
            "purpose_details": suitability_results
        }
