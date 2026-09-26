"""
Physics-Informed / Engineering Formula DO Soft Sensor for Smart STP Monitor
Standard Methods / Benson-Krause Saturation & Physicochemical Transfer Model
"""

import math
import numpy as np
import pandas as pd
from typing import Dict, Any, Union, Optional
from scipy.optimize import minimize
import json
import os


def calculate_do_saturation(
    temperature_c: float = 25.0,
    tds_mg_l: float = 425.0,
    pressure_kpa: float = 101.325
) -> float:
    """
    Computes theoretical dissolved oxygen saturation (DO_sat in mg/L) in water
    using the Benson-Krause / APHA Standard Methods formulation with salinity & pressure corrections.
    """
    t_k = temperature_c + 273.15
    
    # Benson-Krause formula for pure water DO saturation at 1 atm (mg/L)
    # ln(DO) = -139.34411 + 1.575701e5/T - 6.642308e7/T^2 + 1.243800e10/T^3 - 8.621949e11/T^4
    ln_do_pure = (
        -139.34411
        + (1.575701e5 / t_k)
        - (6.642308e7 / (t_k ** 2))
        + (1.243800e10 / (t_k ** 3))
        - (8.621949e11 / (t_k ** 4))
    )
    do_pure = math.exp(ln_do_pure)
    
    # Salinity correction factor (TDS in g/L approx. salinity)
    salinity_g_kg = max(0.0, tds_mg_l / 1000.0)
    salinity_factor = math.exp(
        -salinity_g_kg * (0.017674 - (10.754 / t_k) + (2140.7 / (t_k ** 2)))
    )
    
    # Atmospheric pressure correction factor
    pressure_factor = max(0.5, pressure_kpa / 101.325)
    
    do_sat = do_pure * salinity_factor * pressure_factor
    return max(0.1, do_sat)


class PhysicsDOEstimator:
    """
    Standard Engineering Formula Soft Sensor for Dissolved Oxygen in STP treated water.
    
    Physical Formulation:
      DO_est = DO_sat(T, TDS, P) * Phi_aeration * (1 - alpha * Turbidity / Turb_ref) * (1 - beta * |pH - 7.0|)
    
    Where:
      - DO_sat: Maximum equilibrium saturation (Benson-Krause model)
      - Phi_aeration: Treated-tank aeration efficiency / equilibrium fraction (0.25 - 0.45)
      - alpha: Turbidity/particulate organic oxygen-depletion sensitivity
      - beta: pH-dependent biological respiration correction
    """
    
    def __init__(
        self,
        phi_aeration: float = 0.334,
        alpha_turb: float = 0.082,
        beta_ph: float = 0.045,
        turb_ref: float = 10.0,
        default_temp_c: float = 25.0
    ):
        self.phi_aeration = phi_aeration
        self.alpha_turb = alpha_turb
        self.beta_ph = beta_ph
        self.turb_ref = turb_ref
        self.default_temp_c = default_temp_c
        self.is_calibrated = True

    def estimate(
        self,
        ph: float,
        tds_mg_l: float,
        turbidity_ntu: float,
        temperature_c: Optional[float] = None,
        pressure_kpa: float = 101.325
    ) -> Dict[str, Any]:
        """
        Estimate DO from live sensor readings with strict thermodynamic bounding.
        """
        temp = temperature_c if temperature_c is not None else self.default_temp_c
        do_sat = calculate_do_saturation(temp, tds_mg_l, pressure_kpa)
        
        # Environmental corrections
        turb_norm = max(0.0, turbidity_ntu / self.turb_ref)
        turb_factor = max(0.5, 1.0 - (self.alpha_turb * turb_norm))
        
        ph_dev = abs(ph - 7.0)
        ph_factor = max(0.8, 1.0 - (self.beta_ph * ph_dev))
        
        # Unbounded physics estimate
        raw_estimate = do_sat * self.phi_aeration * turb_factor * ph_factor
        
        # Physical boundary clamping: cannot be negative, cannot exceed saturation limit
        do_final = float(np.clip(raw_estimate, 0.1, do_sat))
        saturation_pct = (do_final / do_sat) * 100.0
        
        # Status classification based on STP norms (ideal 2.0 - 4.0 mg/L in effluent)
        if do_final < 1.5:
            status = "CRITICAL_LOW_DO"
            quality = "Poor Aeration / High Residual Organics"
        elif do_final < 2.0:
            status = "LOW_DO"
            quality = "Sub-optimal Aeration"
        elif do_final <= 4.0:
            status = "OPTIMAL_DO"
            quality = "Normal Treated Effluent"
        else:
            status = "HIGH_DO"
            quality = "Super-aerated / Low Organic Load"
            
        return {
            "do_estimated_mg_l": round(do_final, 2),
            "do_saturation_mg_l": round(do_sat, 2),
            "saturation_pct": round(saturation_pct, 1),
            "formula": "Benson-Krause Equilibrium & Physicochemical Aeration Balance",
            "method": "ENGINEERING_FORMULA_SOFT_SENSOR",
            "status": status,
            "quality_assessment": quality,
            "inputs_used": {
                "ph": float(ph),
                "tds_mg_l": float(tds_mg_l),
                "turbidity_ntu": float(turbidity_ntu),
                "assumed_temp_c": float(temp)
            }
        }

    def calibrate(self, df: pd.DataFrame, train_split: float = 0.8) -> Dict[str, float]:
        """
        Calibrate formula parameters (Phi_aeration, alpha_turb, beta_ph) on historical STP training data.
        """
        split_idx = int(len(df) * train_split)
        train_df = df.iloc[:split_idx].copy()
        
        y_true = train_df["Treated DO (mg/L)"].values
        ph_vals = train_df["Treated pH"].values
        tds_vals = train_df["Treated TDS (mg/L)"].values
        turb_vals = train_df["Treated Turbidity (NTU)"].values
        
        # Compute DO sat for all training rows
        do_sats = np.array([
            calculate_do_saturation(self.default_temp_c, tds, 101.325)
            for tds in tds_vals
        ])
        
        def loss_fn(params):
            phi, alpha, beta = params
            turb_factors = np.maximum(0.5, 1.0 - (alpha * (turb_vals / self.turb_ref)))
            ph_factors = np.maximum(0.8, 1.0 - (beta * np.abs(ph_vals - 7.0)))
            preds = do_sats * phi * turb_factors * ph_factors
            preds = np.clip(preds, 0.1, do_sats)
            return np.mean((preds - y_true) ** 2)
        
        # Initial guess & physical bounds
        init_params = [0.33, 0.05, 0.05]
        bounds = [(0.20, 0.50), (0.0, 0.30), (0.0, 0.20)]
        
        res = minimize(loss_fn, init_params, method="L-BFGS-B", bounds=bounds)
        if res.success:
            self.phi_aeration = float(res.x[0])
            self.alpha_turb = float(res.x[1])
            self.beta_ph = float(res.x[2])
            
        return {
            "phi_aeration": round(self.phi_aeration, 4),
            "alpha_turb": round(self.alpha_turb, 4),
            "beta_ph": round(self.beta_ph, 4)
        }

    def evaluate(self, df: pd.DataFrame, test_split: float = 0.2) -> Dict[str, Any]:
        """
        Evaluates formula accuracy and physical validity on the test dataset.
        """
        split_idx = int(len(df) * (1.0 - test_split))
        test_df = df.iloc[split_idx:].copy()
        
        y_true = test_df["Treated DO (mg/L)"].values
        preds = []
        bounds_respected = []
        
        for _, row in test_df.iterrows():
            res = self.estimate(
                ph=row["Treated pH"],
                tds_mg_l=row["Treated TDS (mg/L)"],
                turbidity_ntu=row["Treated Turbidity (NTU)"],
                temperature_c=self.default_temp_c
            )
            val = res["do_estimated_mg_l"]
            sat = res["do_saturation_mg_l"]
            preds.append(val)
            bounds_respected.append(0.0 <= val <= sat)
            
        preds = np.array(preds)
        mae = float(np.mean(np.abs(preds - y_true)))
        rmse = float(np.sqrt(np.mean((preds - y_true) ** 2)))
        mape = float(np.mean(np.abs((preds - y_true) / y_true)) * 100.0)
        
        return {
            "test_samples": len(test_df),
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "mape_pct": round(mape, 2),
            "physical_bounds_compliance_pct": round(float(np.mean(bounds_respected)) * 100.0, 1),
            "formula_parameters": {
                "phi_aeration": self.phi_aeration,
                "alpha_turb": self.alpha_turb,
                "beta_ph": self.beta_ph
            }
        }
