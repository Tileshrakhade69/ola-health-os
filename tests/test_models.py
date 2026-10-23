"""
Unit Tests for OLA Health OS Machine Learning Predictor Service.
"""

import unittest
from ml_models.predictor import predictor

class TestPredictorService(unittest.TestCase):
    def setUp(self):
        self.predictor = predictor

    def test_metadata_available(self):
        meta = self.predictor.get_all_metadata()
        self.assertIn('er_inflow', meta)
        self.assertIn('los', meta)
        self.assertIn('readmission', meta)
        self.assertIn('clinical_disclaimer', meta)

    def test_er_inflow_prediction(self):
        input_data = {
            'day_of_week': 'Monday',
            'day_of_month': 15,
            'month': 10,
            'lag_1': 4.0,
            'lag_7': 5.0,
            'rolling_7d_mean': 4.2
        }
        res = self.predictor.predict_er_inflow(input_data)
        self.assertIn('predicted_daily_inflow', res)
        self.assertGreaterEqual(res['predicted_daily_inflow'], 0.0)
        self.assertIn('surge_status', res)

    def test_los_prediction(self):
        input_data = {
            'age': 65,
            'gender': 'Male',
            'department': 'Cardiology',
            'admission_type': 'Emergency',
            'triage_acuity': 2,
            'primary_diagnosis': 'Acute Myocardial Infarction',
            'comorbidity_index': 3,
            'num_previous_admissions': 1,
            'systolic_bp': 140,
            'heart_rate': 82,
            'blood_glucose': 130.0
        }
        res = self.predictor.predict_los(input_data)
        self.assertIn('predicted_length_of_stay_days', res)
        self.assertGreaterEqual(res['predicted_length_of_stay_days'], 1.0)
        self.assertIn('stay_category', res)

    def test_readmission_prediction(self):
        input_data = {
            'age': 72,
            'gender': 'Female',
            'department': 'Internal Medicine',
            'admission_type': 'Emergency',
            'triage_acuity': 2,
            'primary_diagnosis': 'Congestive Heart Failure',
            'comorbidity_index': 4,
            'num_previous_admissions': 2,
            'length_of_stay': 7,
            'discharge_disposition': 'Home Health Care',
            'systolic_bp': 145,
            'blood_glucose': 155.0
        }
        res = self.predictor.predict_readmission(input_data)
        self.assertIn('readmission_probability', res)
        self.assertTrue(0.0 <= res['readmission_probability'] <= 1.0)
        self.assertIn('risk_tier', res)
        self.assertIn('clinical_action_plan', res)

if __name__ == '__main__':
    unittest.main()
