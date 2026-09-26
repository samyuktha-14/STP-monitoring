"""
Comprehensive Hyperparameter Tuning and Model Comparison for ML Soft Sensors (BOD, COD, TSS)
Input features include Live Sensors (pH, TDS, Turbidity) + Formula-computed DO + Engineered Physics Features.
DO uses ONLY the Benson-Krause Physics Formula.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy.stats import pearsonr

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ml.soft_sensor.physics_do_estimator import PhysicsDOEstimator, calculate_do_saturation

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "treated_water_clean.csv"))
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "saved_models"))
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "experiments", "results"))
COMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "experiments", "model_comparison"))

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(COMP_DIR, exist_ok=True)

TARGETS = {
    "BOD": "Treated BOD (mg/L)",
    "COD": "Treated COD (mg/L)",
    "TSS": "Treated TSS (mg/L)"
}

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Formula DO and physics-informed domain features.
    """
    do_estimator = PhysicsDOEstimator()
    
    formula_dos = []
    do_sats = []
    
    for _, row in df.iterrows():
        res = do_estimator.estimate(
            ph=row["Treated pH"],
            tds_mg_l=row["Treated TDS (mg/L)"],
            turbidity_ntu=row["Treated Turbidity (NTU)"],
            temperature_c=25.0
        )
        formula_dos.append(res["do_estimated_mg_l"])
        do_sats.append(res["do_saturation_mg_l"])
        
    df_feat = pd.DataFrame(index=df.index)
    df_feat["Treated_pH"] = df["Treated pH"]
    df_feat["Treated_TDS"] = df["Treated TDS (mg/L)"]
    df_feat["Treated_Turbidity"] = df["Treated Turbidity (NTU)"]
    df_feat["Formula_DO"] = formula_dos
    df_feat["DO_Deficit"] = np.array(do_sats) - np.array(formula_dos)
    df_feat["pH_Deviation"] = np.abs(df["Treated pH"] - 7.0)
    df_feat["Turb_TDS_Interaction"] = (df["Treated Turbidity (NTU)"] * df["Treated TDS (mg/L)"]) / 1000.0
    
    return df_feat

def run_tuning_and_comparison():
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    print("Engineering features (Live Sensors + Formula DO + Domain Interactions)...")
    X_df = prepare_features(df)
    feature_names = list(X_df.columns)
    print(f"Features: {feature_names}")
    
    n = len(df)
    train_size = int(n * 0.8)
    
    X_train_raw = X_df.iloc[:train_size].values
    X_test_raw = X_df.iloc[train_size:].values
    
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_test = scaler.transform(X_test_raw)
    
    # Save the feature scaler and feature names
    joblib.dump(scaler, os.path.join(OUTPUT_DIR, "ml_feature_scaler.pkl"))
    with open(os.path.join(OUTPUT_DIR, "ml_feature_names.json"), "w") as f:
        json.dump(feature_names, f, indent=2)
        
    tscv = TimeSeriesSplit(n_splits=5)
    
    # Model Candidate Grids
    model_grids = {
        "Linear Regression": (
            LinearRegression(),
            {}
        ),
        "Ridge Regression": (
            Ridge(),
            {"alpha": [0.01, 0.1, 1.0, 10.0, 50.0, 100.0]}
        ),
        "ElasticNet": (
            ElasticNet(random_state=42, max_iter=2000),
            {"alpha": [0.01, 0.1, 1.0, 10.0], "l1_ratio": [0.2, 0.5, 0.8]}
        ),
        "Support Vector Regressor (SVR)": (
            SVR(),
            {"C": [0.5, 1.0, 5.0, 10.0], "epsilon": [0.01, 0.1, 0.2], "gamma": ["scale", "auto"]}
        ),
        "Random Forest Regressor": (
            RandomForestRegressor(random_state=42),
            {
                "n_estimators": [50, 100, 200],
                "max_depth": [3, 5, 8, None],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [2, 4, 8]
            }
        ),
        "Gradient Boosting Regressor": (
            GradientBoostingRegressor(random_state=42),
            {
                "n_estimators": [50, 100, 150],
                "learning_rate": [0.01, 0.03, 0.05, 0.1],
                "max_depth": [2, 3, 4],
                "subsample": [0.8, 1.0]
            }
        ),
        "XGBoost Regressor": (
            XGBRegressor(random_state=42, n_jobs=1, verbosity=0),
            {
                "n_estimators": [50, 100, 150],
                "learning_rate": [0.01, 0.03, 0.05, 0.1],
                "max_depth": [2, 3, 4],
                "subsample": [0.8, 1.0],
                "reg_alpha": [0.0, 0.1, 1.0],
                "reg_lambda": [1.0, 5.0]
            }
        ),
        "Multi-Layer Perceptron (MLP)": (
            MLPRegressor(random_state=42, max_iter=1000, early_stopping=True),
            {
                "hidden_layer_sizes": [(32,), (64, 32), (32, 16)],
                "alpha": [0.001, 0.01, 0.1],
                "learning_rate_init": [0.005, 0.01]
            }
        )
    }
    
    all_comparison_rows = []
    best_models_dict = {}
    
    # Initialize deployment registry
    deployment_registry = {
        "DO": {
            "model_name": "PhysicsDOEstimator (Benson-Krause Saturation & Physicochemical Transfer)",
            "target_col": "Treated DO (mg/L)",
            "status": "DEPLOYED",
            "method": "ENGINEERING_FORMULA",
            "formula": "DO_sat(T, TDS, P) * Phi_aeration * (1 - alpha*Turb/10) * (1 - beta*|pH-7.0|)",
            "inputs_required": ["Treated pH", "Treated TDS (mg/L)", "Treated Turbidity (NTU)"],
            "test_mae": 0.3364,
            "test_rmse": 0.4214,
            "physical_bounds_compliance": "100.0%",
            "reason": "Formula-only DO soft sensor deployed per engineering specification."
        }
    }
    
    for target_name, target_col in TARGETS.items():
        print(f"\n=======================================================")
        print(f"   HYPERPARAMETER TUNING TARGET: {target_name} ({target_col})")
        print(f"=======================================================")
        
        y_train = df[target_col].iloc[:train_size].values
        y_test = df[target_col].iloc[train_size:].values
        
        # Mean Baseline
        y_train_mean = np.mean(y_train)
        base_test_pred = np.full_like(y_test, y_train_mean)
        base_mae = mean_absolute_error(y_test, base_test_pred)
        base_rmse = np.sqrt(mean_squared_error(y_test, base_test_pred))
        base_r2 = r2_score(y_test, base_test_pred)
        base_mape = np.mean(np.abs((y_test - base_test_pred) / y_test)) * 100.0
        
        all_comparison_rows.append({
            "Target": target_name,
            "Model": "Baseline (Training Mean)",
            "Tuned_Parameters": "N/A",
            "Train_MAE": round(float(mean_absolute_error(y_train, np.full_like(y_train, y_train_mean))), 4),
            "Test_MAE": round(float(base_mae), 4),
            "Test_RMSE": round(float(base_rmse), 4),
            "Test_MAPE_%": round(float(base_mape), 2),
            "Test_R2": round(float(base_r2), 4),
            "MAE_Improvement_%": 0.0,
            "Overfit_Gap (Train R2 - Test R2)": 0.0,
            "Rank": 99
        })
        
        target_results = []
        
        for model_name, (estimator, grid_params) in model_grids.items():
            print(f"  Tuning {model_name}...")
            if grid_params:
                grid = GridSearchCV(
                    estimator,
                    grid_params,
                    cv=tscv,
                    scoring="neg_mean_absolute_error",
                    n_jobs=-1
                )
                grid.fit(X_train, y_train)
                best_est = grid.best_estimator_
                best_params_str = str(grid.best_params_)
            else:
                best_est = estimator
                best_est.fit(X_train, y_train)
                best_params_str = "Default"
                
            train_preds = best_est.predict(X_train)
            test_preds = best_est.predict(X_test)
            
            tr_mae = mean_absolute_error(y_train, train_preds)
            tr_r2 = r2_score(y_train, train_preds)
            
            te_mae = mean_absolute_error(y_test, test_preds)
            te_rmse = np.sqrt(mean_squared_error(y_test, test_preds))
            te_r2 = r2_score(y_test, test_preds)
            te_mape = np.mean(np.abs((y_test - test_preds) / y_test)) * 100.0
            
            mae_imp = ((base_mae - te_mae) / base_mae) * 100.0
            overfit_gap = tr_r2 - te_r2
            
            row_dict = {
                "Target": target_name,
                "Model": model_name,
                "Tuned_Parameters": best_params_str,
                "Train_MAE": round(float(tr_mae), 4),
                "Test_MAE": round(float(te_mae), 4),
                "Test_RMSE": round(float(te_rmse), 4),
                "Test_MAPE_%": round(float(te_mape), 2),
                "Test_R2": round(float(te_r2), 4),
                "MAE_Improvement_%": round(float(mae_imp), 2),
                "Overfit_Gap (Train R2 - Test R2)": round(float(overfit_gap), 4),
                "estimator_obj": best_est
            }
            target_results.append(row_dict)
            
        # Rank models by Test MAE
        target_results.sort(key=lambda x: x["Test_MAE"])
        for rank_idx, r in enumerate(target_results, 1):
            r["Rank"] = rank_idx
            all_comparison_rows.append({k: v for k, v in r.items() if k != "estimator_obj"})
            
        # Best model for this target
        best_entry = target_results[0]
        best_model_name = best_entry["Model"]
        best_est_obj = best_entry["estimator_obj"]
        
        # Save the best model
        model_save_path = os.path.join(OUTPUT_DIR, f"{target_name.lower()}_best_model.pkl")
        joblib.dump(best_est_obj, model_save_path)
        print(f"  --> Best Model for {target_name}: {best_model_name} (Test MAE: {best_entry['Test_MAE']}, Improvement: {best_entry['MAE_Improvement_%']}%)")
        
        deployment_registry[target_name] = {
            "best_model_name": best_model_name,
            "target_col": target_col,
            "status": "DEPLOYED_ML_MODEL",
            "method": "TUNED_MACHINE_LEARNING",
            "tuned_hyperparameters": best_entry["Tuned_Parameters"],
            "features_used": feature_names,
            "test_mae": best_entry["Test_MAE"],
            "test_rmse": best_entry["Test_RMSE"],
            "test_mape_pct": best_entry["Test_MAPE_%"],
            "test_r2": best_entry["Test_R2"],
            "mae_improvement_over_baseline_pct": best_entry["MAE_Improvement_%"],
            "model_path": f"ml/soft_sensor/saved_models/{target_name.lower()}_best_model.pkl"
        }
        
    # Save comparison dataframe
    comp_df = pd.DataFrame(all_comparison_rows)
    comp_csv_path = os.path.join(COMP_DIR, "phase2_comparison_table.csv")
    comp_df.to_csv(comp_csv_path, index=False)
    
    results_comp_csv = os.path.join(RESULTS_DIR, "model_hyperparameter_comparison.csv")
    comp_df.to_csv(results_comp_csv, index=False)
    
    # Save deployment registry
    with open(os.path.join(RESULTS_DIR, "deployment_registry.json"), "w") as f:
        json.dump(deployment_registry, f, indent=2)
        
    print(f"\nHyperparameter tuning & comparison complete! Saved tables to {comp_csv_path}")

if __name__ == "__main__":
    run_tuning_and_comparison()
