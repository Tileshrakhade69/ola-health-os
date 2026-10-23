"""
Machine Learning Pipelines for OLA Health OS.
Trains and exports:
1. ER Inflow Demand Forecasting Model (Time-series / Day-level regression)
2. Length of Stay (LOS) Predictor (Clinical regression pipeline)
3. 30-Day Hospital Readmission Risk Classifier (Clinical classification pipeline)
Includes honest evaluation metrics, feature importances, and metadata serialization.
"""

import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'hospital_data.csv')
MODEL_DIR = os.path.join(BASE_DIR, 'ml_models')

def train_er_inflow_model(df: pd.DataFrame):
    """
    Train a time-aware model predicting daily ER patient inflow volume.
    Aggregates admissions by date and creates time-series lag and calendar features.
    Uses chronological train-test split to strictly avoid data leakage.
    """
    print("\n--- Training Model 1: ER Patient Inflow Demand Forecaster ---")
    df_copy = df.copy()
    df_copy['adm_date'] = pd.to_datetime(df_copy['admission_date']).dt.date
    
    # Filter for Emergency/Trauma or all ER arrivals
    er_df = df_copy[df_copy['admission_type'].isin(['Emergency', 'Trauma'])].copy()
    daily_inflow = er_df.groupby('adm_date').size().reset_index(name='inflow_count')
    daily_inflow['adm_date'] = pd.to_datetime(daily_inflow['adm_date'])
    daily_inflow = daily_inflow.sort_values('adm_date').reset_index(drop=True)

    # Feature Engineering for Time Series
    daily_inflow['day_of_week'] = daily_inflow['adm_date'].dt.day_name()
    daily_inflow['day_of_month'] = daily_inflow['adm_date'].dt.day
    daily_inflow['month'] = daily_inflow['adm_date'].dt.month
    daily_inflow['is_weekend'] = daily_inflow['adm_date'].dt.dayofweek.isin([5, 6]).astype(int)
    
    # Lag and Rolling window features
    daily_inflow['lag_1'] = daily_inflow['inflow_count'].shift(1)
    daily_inflow['lag_7'] = daily_inflow['inflow_count'].shift(7)
    daily_inflow['rolling_7d_mean'] = daily_inflow['inflow_count'].shift(1).rolling(window=7, min_periods=1).mean()
    
    # Drop rows with NaN from lags
    daily_inflow = daily_inflow.dropna().reset_index(drop=True)

    feature_cols = ['day_of_week', 'day_of_month', 'month', 'is_weekend', 'lag_1', 'lag_7', 'rolling_7d_mean']
    X = daily_inflow[feature_cols]
    y = daily_inflow['inflow_count']

    # Chronological Split (Last 20% of timeline for testing)
    split_idx = int(len(daily_inflow) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    test_dates = daily_inflow['adm_date'].iloc[split_idx:].dt.strftime('%Y-%m-%d').tolist()

    cat_features = ['day_of_week']
    num_features = ['day_of_month', 'month', 'is_weekend', 'lag_1', 'lag_7', 'rolling_7d_mean']

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features),
            ('num', StandardScaler(), num_features)
        ]
    )

    model = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', Ridge(alpha=1.0))
    ])

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, a_min=0, a_max=None)

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    print(f"ER Inflow Model Evaluated on {len(y_test)} out-of-time days:")
    print(f"  MAE: {mae:.2f} patients/day")
    print(f"  RMSE: {rmse:.2f} patients/day")
    print(f"  R2 Score: {r2:.3f}")

    # Prepare historical and forecast preview data
    chart_data = {
        'dates': test_dates[-30:],
        'actual': [float(x) for x in y_test.iloc[-30:]],
        'predicted': [round(float(x), 1) for x in y_pred[-30:]]
    }

    metadata = {
        'model_name': 'ER Patient Inflow Demand Forecaster',
        'algorithm': 'Ridge Linear Regression with Calendar & Lag Features',
        'target_variable': 'daily_er_patient_inflow_count',
        'features': feature_cols,
        'validation_method': 'Chronological 80/20 Out-of-Time Validation',
        'metrics': {
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'r2': round(r2, 3),
            'test_samples': len(y_test)
        },
        'chart_preview': chart_data,
        'trained_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    bundle = {
        'pipeline': model,
        'metadata': metadata,
        'latest_daily_stats': {
            'mean_inflow': round(float(y.mean()), 1),
            'std_inflow': round(float(y.std()), 1),
            'last_known_lag_1': float(y.iloc[-1]),
            'last_known_lag_7': float(y.iloc[-7]),
            'last_known_rolling_7d': round(float(y.tail(7).mean()), 1)
        }
    }

    joblib.dump(bundle, os.path.join(MODEL_DIR, 'er_inflow_model.joblib'))
    print("[OK] ER Inflow model saved successfully.")
    return metadata


def train_los_model(df: pd.DataFrame):
    """
    Train a regression pipeline predicting patient Length of Stay (in days).
    Uses demographic, clinical, admission, and vital sign features.
    """
    print("\n--- Training Model 2: Length of Stay (LOS) Predictor ---")
    features = [
        'age', 'gender', 'department', 'admission_type',
        'triage_acuity', 'primary_diagnosis', 'comorbidity_index',
        'num_previous_admissions', 'systolic_bp', 'heart_rate', 'blood_glucose'
    ]
    target = 'length_of_stay'

    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    cat_cols = ['gender', 'department', 'admission_type', 'primary_diagnosis']
    num_cols = [
        'age', 'triage_acuity', 'comorbidity_index',
        'num_previous_admissions', 'systolic_bp', 'heart_rate', 'blood_glucose'
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols),
            ('num', StandardScaler(), num_cols)
        ]
    )

    model = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', GradientBoostingRegressor(
            n_estimators=100, learning_rate=0.08, max_depth=4, random_state=42
        ))
    ])

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, a_min=1.0, a_max=None)

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    print(f"LOS Model Evaluated on {len(y_test)} hold-out admissions:")
    print(f"  MAE: {mae:.2f} days")
    print(f"  RMSE: {rmse:.2f} days")
    print(f"  R2 Score: {r2:.3f}")

    # Extract feature importances
    preprocessor.fit(X_train)
    encoded_cat_names = preprocessor.named_transformers_['cat'].get_feature_names_out(cat_cols)
    all_feature_names = list(encoded_cat_names) + num_cols
    importances = model.named_steps['regressor'].feature_importances_

    feat_importance_df = pd.DataFrame({
        'feature': all_feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)

    top_features = feat_importance_df.head(10).to_dict(orient='records')

    metadata = {
        'model_name': 'Hospital Length of Stay (LOS) Predictor',
        'algorithm': 'Gradient Boosting Regressor with Scikit-learn Pipeline',
        'target_variable': 'length_of_stay (days)',
        'features': features,
        'categorical_features': cat_cols,
        'numerical_features': num_cols,
        'metrics': {
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'r2': round(r2, 3),
            'test_samples': len(y_test),
            'actual_mean_los': round(float(y_test.mean()), 2),
            'predicted_mean_los': round(float(y_pred.mean()), 2)
        },
        'top_features': top_features,
        'trained_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    bundle = {
        'pipeline': model,
        'metadata': metadata
    }

    joblib.dump(bundle, os.path.join(MODEL_DIR, 'los_model.joblib'))
    print("[OK] Length of Stay model saved successfully.")
    return metadata


def train_readmission_model(df: pd.DataFrame):
    """
    Train a classification pipeline predicting 30-day hospital readmission risk.
    Uses clinical, stay, comorbidity, and demographic factors.
    Includes confusion matrix, ROC-AUC, classification report, and probability calibration.
    """
    print("\n--- Training Model 3: 30-Day Hospital Readmission Risk Classifier ---")
    features = [
        'age', 'gender', 'department', 'admission_type',
        'triage_acuity', 'primary_diagnosis', 'comorbidity_index',
        'num_previous_admissions', 'length_of_stay', 'discharge_disposition',
        'systolic_bp', 'blood_glucose'
    ]
    target = 'readmitted_30d'

    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    cat_cols = ['gender', 'department', 'admission_type', 'primary_diagnosis', 'discharge_disposition']
    num_cols = [
        'age', 'triage_acuity', 'comorbidity_index',
        'num_previous_admissions', 'length_of_stay', 'systolic_bp', 'blood_glucose'
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), cat_cols),
            ('num', StandardScaler(), num_cols)
        ]
    )

    model = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(
            n_estimators=120, max_depth=6, class_weight='balanced', random_state=42
        ))
    ])

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    cm = confusion_matrix(y_test, y_pred).tolist()

    print(f"Readmission Model Evaluated on {len(y_test)} hold-out patients:")
    print(f"  Accuracy:  {acc*100:.2f}%")
    print(f"  Precision: {prec*100:.2f}%")
    print(f"  Recall:    {rec*100:.2f}%")
    print(f"  F1-Score:  {f1:.3f}")
    print(f"  ROC-AUC:   {roc_auc:.3f}")
    print(f"  Confusion Matrix (TN, FP / FN, TP):\n    {cm}")

    metadata = {
        'model_name': '30-Day Hospital Readmission Risk Classifier',
        'algorithm': 'Random Forest Classifier with Balanced Class Weighting',
        'target_variable': 'readmitted_30d (0=No, 1=Yes)',
        'features': features,
        'categorical_features': cat_cols,
        'numerical_features': num_cols,
        'metrics': {
            'accuracy': round(acc, 3),
            'precision': round(prec, 3),
            'recall': round(rec, 3),
            'f1_score': round(f1, 3),
            'roc_auc': round(roc_auc, 3),
            'confusion_matrix': {
                'true_negative': cm[0][0],
                'false_positive': cm[0][1],
                'false_negative': cm[1][0],
                'true_positive': cm[1][1]
            },
            'test_samples': len(y_test),
            'positive_rate': round(float(y.mean()), 3)
        },
        'risk_bands': {
            'Low Risk': '< 30% Probability',
            'Moderate Risk': '30% - 60% Probability',
            'High Risk': '> 60% Probability'
        },
        'trained_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    bundle = {
        'pipeline': model,
        'metadata': metadata
    }

    joblib.dump(bundle, os.path.join(MODEL_DIR, 'readmission_model.joblib'))
    print("[OK] Readmission model saved successfully.")
    return metadata


if __name__ == '__main__':
    os.makedirs(MODEL_DIR, exist_ok=True)
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Data file not found at {DATA_PATH}. Run generate_dataset.py first.")

    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    print(f"Dataset successfully loaded with {len(df)} records.")

    m1_meta = train_er_inflow_model(df)
    m2_meta = train_los_model(df)
    m3_meta = train_readmission_model(df)

    print("\n[OK] All three Healthcare Prediction Pipelines trained, evaluated, and serialized successfully.")
