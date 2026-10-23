"""
Unit Tests for OLA Health OS Analytics Service.
"""

import unittest
from services.analytics_service import analytics_service

class TestAnalyticsService(unittest.TestCase):
    def setUp(self):
        self.service = analytics_service

    def test_raw_data_loaded(self):
        df = self.service.get_raw_dataframe()
        self.assertFalse(df.empty, "Dataset should not be empty.")
        self.assertGreaterEqual(len(df), 1000, "Should contain at least 1,000 records.")
        self.assertIn('patient_id', df.columns)
        self.assertIn('length_of_stay', df.columns)
        self.assertIn('readmitted_30d', df.columns)

    def test_executive_kpis(self):
        kpis = self.service.get_executive_kpis()
        self.assertGreater(kpis['total_admissions'], 0)
        self.assertGreater(kpis['avg_los'], 0.0)
        self.assertTrue(0.0 <= kpis['readmission_rate_pct'] <= 100.0)
        self.assertGreater(kpis['total_billed'], 0.0)

    def test_filtering(self):
        dept_filter = {'department': 'Cardiology'}
        filtered = self.service.filter_data(dept_filter)
        self.assertTrue((filtered['department'] == 'Cardiology').all())

    def test_los_distribution(self):
        los = self.service.get_los_distribution()
        self.assertEqual(len(los['labels']), 5)
        self.assertEqual(len(los['counts']), 5)
        self.assertGreater(los['stats']['median'], 0)

    def test_correlation_matrix(self):
        corr = self.service.get_correlation_matrix()
        self.assertIn('columns', corr)
        self.assertIn('matrix', corr)
        self.assertEqual(len(corr['columns']), len(corr['matrix']))

if __name__ == '__main__':
    unittest.main()
