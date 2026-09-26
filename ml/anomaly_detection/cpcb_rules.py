"""
CPCB (Central Pollution Control Board) Regulatory Thresholds & Quality Scoring for STP Treated Water
"""

from typing import Dict, Any, List

# CPCB Treated Effluent Standards (for disposal into water bodies & reuse)
CPCB_LIMITS = {
    "Treated pH": {
        "min": 6.5,
        "max": 8.5,
        "critical_min": 6.0,
        "critical_max": 9.0,
        "unit": "pH",
        "name": "pH"
    },
    "Treated Turbidity (NTU)": {
        "optimal_max": 5.0,
        "warning_max": 10.0,
        "critical_max": 20.0,
        "unit": "NTU",
        "name": "Turbidity"
    },
    "Treated TDS (mg/L)": {
        "optimal_max": 800.0,
        "warning_max": 1500.0,
        "critical_max": 2100.0,
        "unit": "mg/L",
        "name": "Total Dissolved Solids"
    },
    "Treated DO (mg/L)": {
        "optimal_min": 2.0,
        "warning_min": 1.5,
        "critical_min": 1.0,
        "unit": "mg/L",
        "name": "Dissolved Oxygen"
    },
    "Treated TSS (mg/L)": {
        "optimal_max": 10.0,
        "warning_max": 20.0,
        "critical_max": 30.0,
        "unit": "mg/L",
        "name": "Total Suspended Solids"
    },
    "Treated BOD (mg/L)": {
        "optimal_max": 10.0,
        "warning_max": 20.0,
        "critical_max": 30.0,
        "unit": "mg/L",
        "name": "Biochemical Oxygen Demand"
    },
    "Treated COD (mg/L)": {
        "optimal_max": 50.0,
        "warning_max": 100.0,
        "critical_max": 150.0,
        "unit": "mg/L",
        "name": "Chemical Oxygen Demand"
    }
}


class CPCBRuleChecker:
    """
    Checks real-time and soft-sensor readings against statutory Indian CPCB STP discharge limits.
    """

    @staticmethod
    def check_compliance(readings: Dict[str, float]) -> Dict[str, Any]:
        violations = []
        warnings = []
        passed = []
        
        # Check pH
        if "Treated pH" in readings:
            val = readings["Treated pH"]
            if val < CPCB_LIMITS["Treated pH"]["critical_min"] or val > CPCB_LIMITS["Treated pH"]["critical_max"]:
                violations.append({
                    "parameter": "pH",
                    "value": val,
                    "limit": "6.5 - 8.5",
                    "severity": "CRITICAL",
                    "message": f"Critical pH violation ({val:.2f}). Discharge illegal."
                })
            elif val < CPCB_LIMITS["Treated pH"]["min"] or val > CPCB_LIMITS["Treated pH"]["max"]:
                warnings.append({
                    "parameter": "pH",
                    "value": val,
                    "limit": "6.5 - 8.5",
                    "severity": "WARNING",
                    "message": f"pH slightly out of standard range ({val:.2f})."
                })
            else:
                passed.append("pH")

        # Check Turbidity
        if "Treated Turbidity (NTU)" in readings:
            val = readings["Treated Turbidity (NTU)"]
            if val > CPCB_LIMITS["Treated Turbidity (NTU)"]["warning_max"]:
                violations.append({
                    "parameter": "Turbidity",
                    "value": val,
                    "limit": "≤ 10.0 NTU (CPCB Standard)",
                    "severity": "CRITICAL" if val > CPCB_LIMITS["Treated Turbidity (NTU)"]["critical_max"] else "WARNING",
                    "message": f"Turbidity elevated ({val:.2f} NTU). Suspended matter / clarifier issue."
                })
            else:
                passed.append("Turbidity")

        # Check TDS
        if "Treated TDS (mg/L)" in readings:
            val = readings["Treated TDS (mg/L)"]
            if val > CPCB_LIMITS["Treated TDS (mg/L)"]["critical_max"]:
                violations.append({
                    "parameter": "TDS",
                    "value": val,
                    "limit": "≤ 2100 mg/L (Discharge Ceiling)",
                    "severity": "CRITICAL",
                    "message": f"TDS exceeded statutory maximum ({val:.0f} mg/L)."
                })
            elif val > CPCB_LIMITS["Treated TDS (mg/L)"]["warning_max"]:
                warnings.append({
                    "parameter": "TDS",
                    "value": val,
                    "limit": "≤ 1500 mg/L (Reuse Guide)",
                    "severity": "WARNING",
                    "message": f"High salinity / TDS ({val:.0f} mg/L)."
                })
            else:
                passed.append("TDS")

        # Check DO
        if "Treated DO (mg/L)" in readings:
            val = readings["Treated DO (mg/L)"]
            if val < CPCB_LIMITS["Treated DO (mg/L)"]["critical_min"]:
                violations.append({
                    "parameter": "DO",
                    "value": val,
                    "limit": "≥ 2.0 mg/L",
                    "severity": "CRITICAL",
                    "message": f"Anaerobic / Septic state detected! DO critically low ({val:.2f} mg/L)."
                })
            elif val < CPCB_LIMITS["Treated DO (mg/L)"]["optimal_min"]:
                warnings.append({
                    "parameter": "DO",
                    "value": val,
                    "limit": "≥ 2.0 mg/L",
                    "severity": "WARNING",
                    "message": f"Sub-optimal DO ({val:.2f} mg/L). Check blower / aerator speed."
                })
            else:
                passed.append("DO")

        is_fully_compliant = len(violations) == 0
        overall_status = "COMPLIANT" if is_fully_compliant and len(warnings) == 0 else ("WARNING" if is_fully_compliant else "NON_COMPLIANT")
        
        return {
            "overall_cpcb_status": overall_status,
            "is_compliant": is_fully_compliant,
            "violations": violations,
            "warnings": warnings,
            "passed_parameters": passed,
            "total_breaches": len(violations) + len(warnings)
        }
