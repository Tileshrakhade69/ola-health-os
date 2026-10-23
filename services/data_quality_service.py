"""
Data Quality & Audit Service for OLA Health OS.
Performs data profiling, completeness audit, duplicate detection, schema validation,
range checks, and outlier detection using standard statistical criteria (IQR).
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'hospital_data.csv')


class DataQualityService:
    def __init__(self):
        pass

    def run_full_audit(self) -> Dict[str, Any]:
        """Perform comprehensive data profiling and quality audit."""
        if not os.path.exists(DATA_PATH):
            return {'error': 'Dataset not found.'}

        df = pd.read_csv(DATA_PATH)
        total_rows = len(df)
        total_cols = len(df.columns)

        # 1. Column-by-column profiling: nulls, unique count, data types
        col_profile = []
        for col in df.columns:
            null_count = int(df[col].isnull().sum())
            null_pct = round((null_count / total_rows) * 100, 2)
            unique_count = int(df[col].nunique())
            dtype_str = str(df[col].dtype)
            sample_val = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else "N/A"

            col_profile.append({
                'column': col,
                'data_type': dtype_str,
                'null_count': null_count,
                'null_pct': null_pct,
                'unique_count': unique_count,
                'sample_value': sample_val,
                'status': 'Clean' if null_count == 0 else 'Has Nulls'
            })

        # 2. Duplicate Detection
        exact_duplicates = int(df.duplicated().sum())
        duplicate_admissions = int(df.duplicated(subset=['admission_id']).sum())
        unique_patients = int(df['patient_id'].nunique())
        repeat_patients = int((df['patient_id'].value_counts() > 1).sum())

        # 3. Clinical Range / Business Rule Validation
        rule_checks = []

        # Rule 1: Age between 0 and 120
        invalid_age = int(((df['age'] < 0) | (df['age'] > 120)).sum())
        rule_checks.append({
            'rule': 'Patient Age Domain Check',
            'expectation': '0 <= age <= 120',
            'violations': invalid_age,
            'passed': invalid_age == 0,
            'severity': 'Critical'
        })

        # Rule 2: Length of stay >= 1
        invalid_los = int((df['length_of_stay'] < 1).sum())
        rule_checks.append({
            'rule': 'Length of Stay Non-Zero Positive Check',
            'expectation': 'length_of_stay >= 1 day',
            'violations': invalid_los,
            'passed': invalid_los == 0,
            'severity': 'Critical'
        })

        # Rule 3: Triage Acuity between 1 and 5
        invalid_acuity = int((~df['triage_acuity'].isin([1, 2, 3, 4, 5])).sum())
        rule_checks.append({
            'rule': 'Triage Acuity Valid Level Check',
            'expectation': 'triage_acuity IN (1, 2, 3, 4, 5)',
            'violations': invalid_acuity,
            'passed': invalid_acuity == 0,
            'severity': 'High'
        })

        # Rule 4: Readmission target is binary
        invalid_readmit = int((~df['readmitted_30d'].isin([0, 1])).sum())
        rule_checks.append({
            'rule': '30-Day Readmission Binary Target Check',
            'expectation': 'readmitted_30d IN (0, 1)',
            'violations': invalid_readmit,
            'passed': invalid_readmit == 0,
            'severity': 'Critical'
        })

        # Rule 5: Systolic Blood Pressure physiological range (50-260)
        invalid_sbp = int(((df['systolic_bp'] < 50) | (df['systolic_bp'] > 260)).sum())
        rule_checks.append({
            'rule': 'Systolic BP Physiological Plausibility',
            'expectation': '50 <= systolic_bp <= 260 mmHg',
            'violations': invalid_sbp,
            'passed': invalid_sbp == 0,
            'severity': 'Medium'
        })

        # Rule 6: Billing Amount >= 0
        invalid_billing = int((df['billing_amount'] < 0).sum())
        rule_checks.append({
            'rule': 'Billing Amount Non-Negative Check',
            'expectation': 'billing_amount >= $0.00',
            'violations': invalid_billing,
            'passed': invalid_billing == 0,
            'severity': 'High'
        })

        # 4. Statistical Outliers via Interquartile Range (IQR) Method
        outlier_summary = []
        for num_col in ['length_of_stay', 'billing_amount', 'blood_glucose']:
            q25 = df[num_col].quantile(0.25)
            q75 = df[num_col].quantile(0.75)
            iqr = q75 - q25
            lower_bound = round(q25 - (1.5 * iqr), 2)
            upper_bound = round(q75 + (1.5 * iqr), 2)

            outlier_count = int(((df[num_col] < lower_bound) | (df[num_col] > upper_bound)).sum())
            outlier_pct = round((outlier_count / total_rows) * 100, 2)

            outlier_summary.append({
                'column': num_col,
                'q25': round(q25, 2),
                'median': round(df[num_col].median(), 2),
                'q75': round(q75, 2),
                'lower_fence': lower_bound,
                'upper_fence': upper_bound,
                'outliers_count': outlier_count,
                'outliers_pct': outlier_pct
            })

        # 5. Composite Quality Score
        total_rules = len(rule_checks)
        passed_rules = sum(1 for r in rule_checks if r['passed'])
        null_penalty = sum(col['null_pct'] for col in col_profile) / len(col_profile)
        rule_score = (passed_rules / total_rules) * 100
        overall_health_score = max(0, round(rule_score - null_penalty, 1))

        return {
            'overview': {
                'total_records': total_rows,
                'total_columns': total_cols,
                'exact_duplicates': exact_duplicates,
                'duplicate_admission_ids': duplicate_admissions,
                'unique_patients': unique_patients,
                'repeat_patient_cohort': repeat_patients,
                'overall_health_score': overall_health_score,
                'file_size_kb': round(os.path.getsize(DATA_PATH) / 1024, 1)
            },
            'column_profile': col_profile,
            'rule_checks': rule_checks,
            'outlier_summary': outlier_summary
        }


# Global singleton
data_quality_service = DataQualityService()
