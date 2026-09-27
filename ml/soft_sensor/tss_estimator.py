"""
Turbidity-to-TSS Empirical Estimation Module for Smart STP Monitor

Scientific Note / Limitation:
Estimated TSS derived from the validated turbidity–TSS relationship for this STP dataset.
This formula does not universally predict TSS for every sewage treatment plant
and is not a direct laboratory measurement.
"""

import math
from typing import Dict, Any, Optional, Union

# Validated empirical coefficients from project analysis
# Model formulation: TSS (mg/L) = a * Turbidity (NTU) + b
DEFAULT_TSS_SLOPE_A: float = 1.15
DEFAULT_TSS_INTERCEPT_B: float = 5.22
SCIENTIFIC_LIMITATION_DISCLAIMER: str = (
    "Estimated TSS derived from the validated turbidity–TSS relationship for this STP dataset."
)


class TurbidityTSSEstimator:
    """
    Real-time Turbidity -> TSS Empirical Estimator.
    Computes estimated Total Suspended Solids (TSS) from optical nephelometric turbidity (NTU).
    """

    def __init__(self, a: float = DEFAULT_TSS_SLOPE_A, b: float = DEFAULT_TSS_INTERCEPT_B):
        self.a = float(a)
        self.b = float(b)
        self.formula_str = f"TSS = {self.a:.2f} * Turbidity + {self.b:.2f}"
        self.disclaimer = SCIENTIFIC_LIMITATION_DISCLAIMER

    def estimate(self, turbidity: Any) -> Dict[str, Any]:
        """
        Estimates TSS from turbidity reading.

        Validation rules:
        - Must be convertible to a finite float.
        - Negative values are invalid (turbidity >= 0.0 NTU).
        - Missing (None), null, empty string, or non-numeric inputs are rejected.
        """
        # 1. Check for None / missing
        if turbidity is None:
            return {
                "turbidity": None,
                "turbidity_unit": "NTU",
                "tss": None,
                "tss_display": "Unavailable",
                "tss_unit": "mg/L",
                "tss_source": "estimated_from_turbidity",
                "status": "unavailable",
                "reason": "Turbidity reading unavailable",
                "formula": self.formula_str,
                "is_estimated": True,
                "description": self.disclaimer
            }

        # 2. Type conversion & finite check
        try:
            turb_val = float(turbidity)
            if math.isnan(turb_val) or math.isinf(turb_val):
                return {
                    "turbidity": None,
                    "turbidity_unit": "NTU",
                    "tss": None,
                    "tss_display": "Unavailable",
                    "tss_unit": "mg/L",
                    "tss_source": "estimated_from_turbidity",
                    "status": "unavailable",
                    "reason": "Turbidity value is non-finite (NaN or Inf)",
                    "formula": self.formula_str,
                    "is_estimated": True,
                    "description": self.disclaimer
                }
        except (ValueError, TypeError):
            return {
                "turbidity": None,
                "turbidity_unit": "NTU",
                "tss": None,
                "tss_display": "Unavailable",
                "tss_unit": "mg/L",
                "tss_source": "estimated_from_turbidity",
                "status": "unavailable",
                "reason": f"Non-numeric turbidity input: {repr(turbidity)}",
                "formula": self.formula_str,
                "is_estimated": True,
                "description": self.disclaimer
            }

        # 3. Reject negative turbidity
        if turb_val < 0.0:
            return {
                "turbidity": round(turb_val, 2),
                "turbidity_unit": "NTU",
                "tss": None,
                "tss_display": "Unavailable",
                "tss_unit": "mg/L",
                "tss_source": "estimated_from_turbidity",
                "status": "unavailable",
                "reason": f"Negative turbidity is physically invalid ({turb_val} NTU)",
                "formula": self.formula_str,
                "is_estimated": True,
                "description": self.disclaimer
            }

        # 4. Apply validated empirical formula
        try:
            tss_val = self.a * turb_val + self.b
            tss_rounded = round(tss_val, 2)
            return {
                "turbidity": round(turb_val, 2),
                "turbidity_unit": "NTU",
                "tss": tss_rounded,
                "tss_display": f"{tss_rounded:.1f}",
                "tss_unit": "mg/L",
                "tss_source": "estimated_from_turbidity",
                "status": "valid",
                "formula": self.formula_str,
                "is_estimated": True,
                "description": self.disclaimer
            }
        except Exception as e:
            return {
                "turbidity": round(turb_val, 2),
                "turbidity_unit": "NTU",
                "tss": None,
                "tss_display": "Unavailable",
                "tss_unit": "mg/L",
                "tss_source": "estimated_from_turbidity",
                "status": "unavailable",
                "reason": f"Calculation error: {str(e)}",
                "formula": self.formula_str,
                "is_estimated": True,
                "description": self.disclaimer
            }


# Singleton estimator instance for easy function import
_default_estimator = TurbidityTSSEstimator()


def estimate_tss(turbidity: Any) -> Dict[str, Any]:
    """
    Clean reusable function to estimate TSS from turbidity.

    Accepts:
        turbidity: raw numeric or convertible reading in NTU

    Returns:
        dict with estimated TSS, metadata, and status
    """
    return _default_estimator.estimate(turbidity)
