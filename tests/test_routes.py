"""
Integration Route Tests for OLA Health OS Flask Application.
"""

import unittest
from app import app

class TestFlaskRoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_overview_route(self):
        response = self.client.get('/overview')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Executive Analytics Dashboard', response.data)

    def test_patient_analytics_route(self):
        response = self.client.get('/patient-analytics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Patient Demographics', response.data)

    def test_er_inflow_route(self):
        response = self.client.get('/er-inflow')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Emergency Room (ER) Patient Inflow', response.data)

    def test_los_analysis_route(self):
        response = self.client.get('/los-analysis')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Length of Stay (LOS)', response.data)

    def test_readmission_route(self):
        response = self.client.get('/readmission-analysis')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Readmission Risk', response.data)

    def test_data_explorer_route(self):
        response = self.client.get('/data-explorer')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Data Explorer', response.data)

    def test_prediction_center_route(self):
        response = self.client.get('/prediction-center')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Prediction Center', response.data)

    def test_reports_route(self):
        response = self.client.get('/reports')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Analytical SQL', response.data)

    def test_data_quality_route(self):
        response = self.client.get('/data-quality')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Data Quality', response.data)

    def test_about_route(self):
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'About OLA Health OS', response.data)

    def test_api_db_status(self):
        response = self.client.get('/api/db-status')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn('mode', json_data)
        self.assertIn('total_admissions', json_data)

    def test_export_csv_route(self):
        response = self.client.get('/export-csv')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('text/csv' in response.content_type)
        self.assertIn(b'patient_id,admission_id', response.data)

if __name__ == '__main__':
    unittest.main()
