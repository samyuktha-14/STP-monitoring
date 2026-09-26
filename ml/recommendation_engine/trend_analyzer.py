"""
Multi-Scale Trend & Drift Analysis Engine for Smart STP Monitor
Calculates rolling slopes, directional trajectories, volatility, and 3-day early degradation projections.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from scipy.stats import linregress


class TrendAnalyzer:
    """
    Analyzes historical sensor time-series windows to detect drift, volatility, and future degradation risk.
    """

    # Parameter threshold definitions for early warning lookaheads
    WARNING_THRESHOLDS = {
        "pH": {"min": 6.5, "max": 8.5, "ideal": 7.0},
        "Turbidity": {"warning": 5.0, "critical": 10.0, "ideal": 1.0},
        "TDS": {"warning": 1000.0, "critical": 1500.0, "ideal": 400.0},
        "DO": {"critical_low": 1.5, "warning_low": 2.0, "ideal": 3.0}
    }

    def analyze_parameter_trend(
        self,
        values: List[float],
        param_name: str,
        time_step_days: float = 1.0
    ) -> Dict[str, Any]:
        """
        Analyzes trend trajectory for a single parameter over a given historical window (e.g. 7 days).
        """
        if len(values) < 2:
            return {
                "parameter": param_name,
                "direction": "STABLE",
                "trend_icon": "➔",
                "slope_per_day": 0.0,
                "pct_change_window": 0.0,
                "volatility_cv_pct": 0.0,
                "early_warning": None,
                "projected_3day_value": round(float(values[-1]), 2) if len(values) == 1 else 0.0
            }

        y = np.array(values, dtype=float)
        x = np.arange(len(y)) * time_step_days

        # Linear regression slope (drift rate per day)
        res = linregress(x, y)
        slope = float(res.slope)
        r_value = float(res.rvalue)

        current_val = float(y[-1])
        start_val = float(y[0])
        pct_change = ((current_val - start_val) / (start_val if abs(start_val) > 1e-5 else 1.0)) * 100.0

        # Coefficient of Variation (Volatility %)
        mean_val = float(np.mean(y))
        std_val = float(np.std(y))
        cv_pct = (std_val / (mean_val if abs(mean_val) > 1e-5 else 1.0)) * 100.0

        # 3-Day Lookahead Projection (Linear Extrapolation)
        lookahead_days = 3.0
        projected_3day = float(current_val + (slope * lookahead_days))

        # Classify Direction
        # For Turbidity & TDS: Increasing is DEGRADING, Decreasing is IMPROVING
        # For DO: Decreasing below ideal is DEGRADING, Increasing toward ideal is IMPROVING
        # For pH: Moving away from 7.0 is DEGRADING, Moving toward 7.0 is IMPROVING
        direction = "STABLE"
        trend_icon = "[STEADY]"
        early_warning = None

        if param_name == "Turbidity":
            if slope > 0.15:
                direction = "DEGRADING"
                trend_icon = "[RISING]"
                if projected_3day > self.WARNING_THRESHOLDS["Turbidity"]["warning"]:
                    early_warning = f"Warning: Turbidity is trending upward (+{slope:.2f} NTU/day). Projected to reach {projected_3day:.1f} NTU in 3 days."
            elif slope < -0.15:
                direction = "IMPROVING"
                trend_icon = "[CLARIFYING]"

        elif param_name == "DO":
            if slope < -0.10 and current_val < 2.5:
                direction = "DEGRADING"
                trend_icon = "[DEPLETING]"
                if projected_3day < self.WARNING_THRESHOLDS["DO"]["warning_low"]:
                    early_warning = f"Critical Alert: Dissolved Oxygen is dropping ({slope:.2f} mg/L/day). Aeration basin failure risk in ~3 days ({projected_3day:.2f} mg/L)."
            elif slope > 0.10:
                direction = "IMPROVING"
                trend_icon = "[AERATING]"

        elif param_name == "TDS":
            if slope > 15.0:
                direction = "DEGRADING"
                trend_icon = "[SALINITY_RISING]"
                if projected_3day > self.WARNING_THRESHOLDS["TDS"]["warning"]:
                    early_warning = f"Notice: TDS rising rapidly (+{slope:.1f} mg/L/day). Check water softener regeneration cycles."
            elif slope < -15.0:
                direction = "IMPROVING"
                trend_icon = "[DILUTING]"

        elif param_name == "pH":
            dev_now = abs(current_val - 7.0)
            dev_start = abs(start_val - 7.0)
            if dev_now > dev_start + 0.10:
                direction = "DEGRADING"
                trend_icon = "[DRIFTING_FROM_NEUTRAL]"
            elif dev_now < dev_start - 0.10:
                direction = "IMPROVING"
                trend_icon = "[STABILIZING_TO_NEUTRAL]"

        return {
            "parameter": param_name,
            "current_value": round(current_val, 2),
            "start_window_value": round(start_val, 2),
            "direction": direction,
            "trend_icon": trend_icon,
            "slope_per_day": round(slope, 3),
            "pct_change_window": round(pct_change, 1),
            "volatility_cv_pct": round(cv_pct, 1),
            "r_squared": round(r_value ** 2, 3),
            "projected_3day_value": round(projected_3day, 2),
            "early_warning": early_warning
        }

    def analyze_multi_parameter_window(
        self,
        history_df: pd.DataFrame,
        window_size: int = 7
    ) -> Dict[str, Any]:
        """
        Runs trend trajectory analysis across all primary parameters over the given window of rows.
        """
        recent = history_df.tail(window_size)
        results = {}

        mapping = {
            "pH": "Treated pH",
            "TDS": "Treated TDS (mg/L)",
            "Turbidity": "Treated Turbidity (NTU)",
            "DO": "Treated DO (mg/L)" if "Treated DO (mg/L)" in recent.columns else None
        }

        warnings = []

        for param_key, col_name in mapping.items():
            if col_name and col_name in recent.columns:
                vals = recent[col_name].dropna().tolist()
                t_res = self.analyze_parameter_trend(vals, param_key)
                results[param_key] = t_res
                if t_res["early_warning"]:
                    warnings.append(t_res["early_warning"])

        return {
            "window_days": len(recent),
            "parameter_trends": results,
            "active_early_warnings": warnings,
            "has_degradation_trend": any(r["direction"] == "DEGRADING" for r in results.values())
        }
