"""
Prediction Service for OLA Health OS.
Encapsulates runtime inference, input validation, clinical risk categorization,
and model metadata for all three healthcare prediction modules.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'ml_models')

ER_MODEL_PATH = os.path.join(MODEL_DIR, 'er_inflow_model.joblib')
LOS_MODEL_PATH = os.path.join(MODEL_DIR, 'los_model.joblib')
READMISSION_MODEL_PATH = os.path.join(MODEL_DIR, 'readmission_model.joblib')


class HealthPredictor:
    def __init__(self):
        self._er_bundle = None
        self._los_bundle = None
        self._readmission_bundle = None
        self._load_models()

    def _load_models(self):
        """Lazy load or initialize model pipelines."""
        if os.path.exists(ER_MODEL_PATH):
            self._er_bundle = joblib.load(ER_MODEL_PATH)
        if os.path.exists(LOS_MODEL_PATH):
            self._los_bundle = joblib.load(LOS_MODEL_PATH)
        if os.path.exists(READMISSION_MODEL_PATH):
            self._readmission_bundle = joblib.load(READMISSION_MODEL_PATH)

    def get_all_metadata(self) -> Dict[str, Any]:
        """Return model cards, algorithms, metrics, and limitations for UI/Portfolio display."""
        return {
            'er_inflow': self._er_bundle.get('metadata') if self._er_bundle else None,
            'los': self._los_bundle.get('metadata') if self._los_bundle else None,
            'readmission': self._readmission_bundle.get('metadata') if self._readmission_bundle else None,
            'clinical_disclaimer': (
                "Educational & Analytical Prototype Notice: Predictions are generated "
                "for educational and operational planning demonstrations only. Not intended "
                "for clinical diagnosis, medical decision making, or emergency triage."
            )
        }

    # 1. ER Inflow Prediction
    def predict_er_inflow(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self._er_bundle:
            raise RuntimeError("ER Inflow model is not loaded.")

        # Input extraction & validation
        day_of_week = str(data.get('day_of_week', 'Monday')).capitalize()
        day_of_month = int(data.get('day_of_month', 15))
        month = int(data.get('month', 6))
        is_weekend = 1 if day_of_week in ['Saturday', 'Sunday'] else 0

        latest_stats = self._er_bundle.get('latest_daily_stats', {})
        lag_1 = float(data.get('lag_1', latest_stats.get('last_known_lag_1', 3.0)))
        lag_7 = float(data.get('lag_7', latest_stats.get('last_known_lag_7', 4.0)))
        rolling_7d = float(data.get('rolling_7d_mean', latest_stats.get('last_known_rolling_7d', 3.5)))

        input_df = pd.DataFrame([{
            'day_of_week': day_of_week,
            'day_of_month': max(1, min(31, day_of_month)),
            'month': max(1, min(12, month)),
            'is_weekend': is_weekend,
            'lag_1': max(0.0, lag_1),
            'lag_7': max(0.0, lag_7),
            'rolling_7d_mean': max(0.0, rolling_7d)
        }])

        pipeline = self._er_bundle['pipeline']
        pred_val = float(pipeline.predict(input_df)[0])
        pred_val = max(0.0, round(pred_val, 1))

        # Operational workload level
        mean_inf = latest_stats.get('mean_inflow', 3.5)
        if pred_val > mean_inf * 1.3:
            surge_status = "High Volume Surge Expected"
            surge_level = "warning"
            staffing_rec = "Consider scheduling additional triage nurses and ER on-call residents."
        elif pred_val < mean_inf * 0.7:
            surge_status = "Below Average Volume Expected"
            surge_level = "success"
            staffing_rec = "Standard base staffing is adequate; review elective admission flow."
        else:
            surge_status = "Normal Operational Volume"
            surge_level = "info"
            staffing_rec = "Maintain routine operational staffing levels."

        return {
            'predicted_daily_inflow': pred_val,
            'surge_status': surge_status,
            'surge_level': surge_level,
            'staffing_recommendation': staffing_rec,
            'baseline_mean': mean_inf,
            'inputs_evaluated': input_df.to_dict(orient='records')[0]
        }

    # 2. Length of Stay (LOS) Prediction
    def predict_los(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self._los_bundle:
            raise RuntimeError("LOS model is not loaded.")

        # Extract & validate inputs
        age = int(max(1, min(105, int(data.get('age', 55)))))
        gender = str(data.get('gender', 'Male'))
        department = str(data.get('department', 'General Surgery'))
        admission_type = str(data.get('admission_type', 'Emergency'))
        triage_acuity = int(max(1, min(5, int(data.get('triage_acuity', 3)))))
        primary_diagnosis = str(data.get('primary_diagnosis', 'Pneumonia'))
        comorbidity_index = int(max(0, min(10, int(data.get('comorbidity_index', 2)))))
        num_previous_admissions = int(max(0, min(15, int(data.get('num_previous_admissions', 0)))))
        systolic_bp = int(max(60, min(240, int(data.get('systolic_bp', 125)))))
        heart_rate = int(max(40, min(200, int(data.get('heart_rate', 75)))))
        blood_glucose = float(max(40.0, min(500.0, float(data.get('blood_glucose', 110.0)))))

        input_df = pd.DataFrame([{
            'age': age,
            'gender': gender,
            'department': department,
            'admission_type': admission_type,
            'triage_acuity': triage_acuity,
            'primary_diagnosis': primary_diagnosis,
            'comorbidity_index': comorbidity_index,
            'num_previous_admissions': num_previous_admissions,
            'systolic_bp': systolic_bp,
            'heart_rate': heart_rate,
            'blood_glucose': blood_glucose
        }])

        pipeline = self._los_bundle['pipeline']
        predicted_days = float(pipeline.predict(input_df)[0])
        predicted_days = max(1.0, round(predicted_days, 1))

        # Benchmarks & discharge planning band
        if predicted_days <= 3.0:
            stay_category = "Short Stay (<4 Days)"
            bed_turnover_impact = "Rapid Bed Turnover"
        elif predicted_days <= 7.0:
            stay_category = "Standard Acute Care Stay (4-7 Days)"
            bed_turnover_impact = "Normal Hospital Stay"
        else:
            stay_category = "Extended Complex Stay (>7 Days)"
            bed_turnover_impact = "Resource-Intensive Inpatient Care"

        return {
            'predicted_length_of_stay_days': predicted_days,
            'stay_category': stay_category,
            'bed_turnover_impact': bed_turnover_impact,
            'inputs_evaluated': input_df.to_dict(orient='records')[0]
        }

    # 3. 30-Day Readmission Risk Prediction
    def predict_readmission(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self._readmission_bundle:
            raise RuntimeError("Readmission model is not loaded.")

        # Extract & validate inputs
        age = int(max(1, min(105, int(data.get('age', 62)))))
        gender = str(data.get('gender', 'Female'))
        department = str(data.get('department', 'Cardiology'))
        admission_type = str(data.get('admission_type', 'Emergency'))
        triage_acuity = int(max(1, min(5, int(data.get('triage_acuity', 2)))))
        primary_diagnosis = str(data.get('primary_diagnosis', 'Congestive Heart Failure'))
        comorbidity_index = int(max(0, min(10, int(data.get('comorbidity_index', 3)))))
        num_previous_admissions = int(max(0, min(15, int(data.get('num_previous_admissions', 1)))))
        length_of_stay = int(max(1, min(60, int(data.get('length_of_stay', 5)))))
        discharge_disposition = str(data.get('discharge_disposition', 'Home Health Care'))
        systolic_bp = int(max(60, min(240, int(data.get('systolic_bp', 135)))))
        blood_glucose = float(max(40.0, min(500.0, float(data.get('blood_glucose', 130.0)))))

        input_df = pd.DataFrame([{
            'age': age,
            'gender': gender,
            'department': department,
            'admission_type': admission_type,
            'triage_acuity': triage_acuity,
            'primary_diagnosis': primary_diagnosis,
            'comorbidity_index': comorbidity_index,
            'num_previous_admissions': num_previous_admissions,
            'length_of_stay': length_of_stay,
            'discharge_disposition': discharge_disposition,
            'systolic_bp': systolic_bp,
            'blood_glucose': blood_glucose
        }])

        pipeline = self._readmission_bundle['pipeline']
        probabilities = pipeline.predict_proba(input_df)[0]
        readmit_prob = float(probabilities[1])
        readmit_prob_pct = round(readmit_prob * 100, 1)

        # Threshold and Risk Tier (standard clinical risk threshold: 0.50 default, >0.35 elevated)
        if readmit_prob < 0.30:
            risk_tier = "Low Risk"
            risk_badge = "success"
            action_plan = "Standard discharge summary and routine primary care follow-up within 14 days."
        elif readmit_prob < 0.60:
            risk_tier = "Moderate Risk"
            risk_badge = "warning"
            action_plan = "Schedule telehealth nurse check-in within 72 hours; verify medication reconciliation."
        else:
            risk_tier = "High Risk"
            risk_badge = "danger"
            action_plan = "Initiate transitional care management (TCM), bedside pharmacist consult, and 48-hour post-discharge home health visit."

        return {
            'readmission_probability': readmit_prob,
            'readmission_probability_pct': readmit_prob_pct,
            'is_high_risk': bool(readmit_prob >= 0.50),
            'risk_tier': risk_tier,
            'risk_badge': risk_badge,
            'clinical_action_plan': action_plan,
            'inputs_evaluated': input_df.to_dict(orient='records')[0]
        }


# Global singleton instance
predictor = HealthPredictor()
