"""
OLA Health OS - Machine Learning & Predictive Analytics Engine
Trains, validates, and serializes predictive models:
1. ER Inflow & Surge Forecaster (Gradient Boosting Regressor)
2. Inpatient Length of Stay (LoS) Predictor (Random Forest Regressor)
3. 30-Day Readmission Risk Classifier (Gradient Boosting Classifier)
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
)
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

def train_er_inflow_model(adm_df):
    """
    Model 1: ER Inflow & Surge Forecaster
    Predicts hourly patient arrivals and flags surge risk.
    """
    print("\n--- Training Model 1: ER Inflow & Surge Forecaster ---")
    
    # Aggregate admissions by hour
    adm_df["timestamp_dt"] = pd.to_datetime(adm_df["admission_timestamp"])
    hourly = adm_df.set_index("timestamp_dt").resample("2h").agg(
        arrival_count=("admission_id", "count"),
        hour=("hour_of_day", "first"),
        day_of_week=("day_of_week", "first"),
        month=("month", "first"),
        is_weekend=("is_weekend", "first"),
        weather=("weather_condition", lambda x: x.mode()[0] if len(x) > 0 else "Clear / Mild")
    ).reset_index()

    hourly["weather"] = hourly["weather"].fillna("Clear / Mild")
    hourly["hour"] = hourly["timestamp_dt"].dt.hour
    hourly["day_of_week"] = hourly["timestamp_dt"].dt.dayofweek
    hourly["month"] = hourly["timestamp_dt"].dt.month
    hourly["is_weekend"] = hourly["day_of_week"].apply(lambda d: 1 if d in [5, 6] else 0)

    # Lag features
    hourly["lag_2h"] = hourly["arrival_count"].shift(1).fillna(hourly["arrival_count"].mean())
    hourly["lag_4h"] = hourly["arrival_count"].shift(2).fillna(hourly["arrival_count"].mean())
    hourly["rolling_mean_6h"] = hourly["arrival_count"].rolling(window=3, min_periods=1).mean()

    features = ["hour", "day_of_week", "month", "is_weekend", "weather", "lag_2h", "lag_4h", "rolling_mean_6h"]
    X = hourly[features]
    y = hourly["arrival_count"]

    categorical_cols = ["weather"]
    numeric_cols = ["hour", "day_of_week", "month", "is_weekend", "lag_2h", "lag_4h", "rolling_mean_6h"]

    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols)
    ])

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", GradientBoostingRegressor(n_estimators=120, max_depth=4, learning_rate=0.08, random_state=42))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    print(f"ER Inflow Forecaster Metrics: MAE={mae:.3f} patients/2h | RMSE={rmse:.3f} | R²={r2:.3f}")

    # Extract feature importance
    cat_names = model.named_steps["preprocessor"].named_transformers_["cat"].get_feature_names_out(categorical_cols).tolist()
    feature_names = numeric_cols + cat_names
    importances = model.named_steps["regressor"].feature_importances_.tolist()
    feat_imp = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)

    joblib.dump(model, os.path.join(MODELS_DIR, "er_inflow_model.joblib"))
    
    return {
        "model_name": "ER Patient Inflow Forecaster",
        "algorithm": "Gradient Boosting Regressor",
        "metrics": {"mae": round(mae, 3), "rmse": round(rmse, 3), "r2": round(r2, 3)},
        "top_features": [{"feature": k, "importance": round(v, 4)} for k, v in feat_imp[:6]]
    }

def train_los_model(merged_df):
    """
    Model 2: Length of Stay (LoS) & Bed Turnaround Predictor
    Predicts patient hospitalization length in days.
    """
    print("\n--- Training Model 2: Length of Stay (LoS) Predictor ---")
    
    features = [
        "age", "gender", "department", "diagnosis", "esi_score", "arrival_mode",
        "hypertension", "diabetes", "copd", "coronary_artery_disease", "charlson_comorbidity_index",
        "heart_rate", "oxygen_saturation", "systolic_bp", "news2_deterioration_score"
    ]
    target = "length_of_stay_days"

    X = merged_df[features]
    y = merged_df[target]

    categorical_cols = ["gender", "department", "diagnosis", "arrival_mode"]
    numeric_cols = [c for c in features if c not in categorical_cols]

    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols)
    ])

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    print(f"LoS Predictor Metrics: MAE={mae:.2f} days | RMSE={rmse:.2f} days | R²={r2:.3f}")

    cat_names = model.named_steps["preprocessor"].named_transformers_["cat"].get_feature_names_out(categorical_cols).tolist()
    feature_names = numeric_cols + cat_names
    importances = model.named_steps["regressor"].feature_importances_.tolist()
    feat_imp = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)

    joblib.dump(model, os.path.join(MODELS_DIR, "los_model.joblib"))

    return {
        "model_name": "Length of Stay (LoS) Predictor",
        "algorithm": "Random Forest Regressor",
        "metrics": {"mae_days": round(mae, 2), "rmse_days": round(rmse, 2), "r2": round(r2, 3)},
        "top_features": [{"feature": k, "importance": round(v, 4)} for k, v in feat_imp[:6]]
    }

def train_readmission_model(merged_df):
    """
    Model 3: 30-Day Readmission Risk & Clinical Deterioration Classifier
    Predicts probability of patient readmission within 30 days.
    """
    print("\n--- Training Model 3: 30-Day Readmission Risk Classifier ---")

    features = [
        "age", "gender", "department", "diagnosis", "esi_score",
        "hypertension", "diabetes", "copd", "coronary_artery_disease", "charlson_comorbidity_index",
        "heart_rate", "oxygen_saturation", "news2_deterioration_score", "length_of_stay_days"
    ]
    target = "readmitted_30d"

    X = merged_df[features]
    y = merged_df[target]

    categorical_cols = ["gender", "department", "diagnosis"]
    numeric_cols = [c for c in features if c not in categorical_cols]

    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols)
    ])

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", GradientBoostingClassifier(n_estimators=100, max_depth=4, learning_rate=0.08, random_state=42))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    cm = confusion_matrix(y_test, y_pred).tolist()

    print(f"Readmission Risk Classifier: Accuracy={acc*100:.1f}% | ROC-AUC={roc_auc:.3f} | F1={f1:.3f}")

    cat_names = model.named_steps["preprocessor"].named_transformers_["cat"].get_feature_names_out(categorical_cols).tolist()
    feature_names = numeric_cols + cat_names
    importances = model.named_steps["classifier"].feature_importances_.tolist()
    feat_imp = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)

    joblib.dump(model, os.path.join(MODELS_DIR, "readmission_model.joblib"))

    return {
        "model_name": "30-Day Readmission Risk Classifier",
        "algorithm": "Gradient Boosting Classifier",
        "metrics": {
            "accuracy": round(acc, 4),
            "roc_auc": round(roc_auc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": cm
        },
        "top_features": [{"feature": k, "importance": round(v, 4)} for k, v in feat_imp[:6]]
    }

def run_training_pipeline():
    print("=" * 60)
    print(">>> OLA Health OS: Commencing Predictive ML Model Pipeline")
    print("=" * 60)

    adm_df = pd.read_csv(os.path.join(DATA_DIR, "hospital_admissions.csv"))
    pat_df = pd.read_csv(os.path.join(DATA_DIR, "patient_records.csv"))

    # Merge patient demographics into admission logs
    merged_df = adm_df.merge(pat_df, on="patient_id", how="left")

    m1_metrics = train_er_inflow_model(adm_df)
    m2_metrics = train_los_model(merged_df)
    m3_metrics = train_readmission_model(merged_df)

    all_metrics = {
        "trained_at": datetime.now().isoformat(),
        "models": {
            "er_inflow": m1_metrics,
            "length_of_stay": m2_metrics,
            "readmission_risk": m3_metrics
        }
    }

    metrics_path = os.path.join(MODELS_DIR, "model_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)

    print(f"\n[COMPLETE] All ML models serialized to {MODELS_DIR}")
    print(f"[COMPLETE] Model performance metrics cataloged to {metrics_path}")

if __name__ == "__main__":
    run_training_pipeline()
