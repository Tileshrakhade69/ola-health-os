"""
Analytics Service for OLA Health OS.
Provides statistical calculations, KPI metrics, dynamic multi-dimensional filtering,
trend aggregations, and clinical cohort analysis using Pandas and NumPy.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'hospital_data.csv')


class AnalyticsService:
    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._load_data()

    def _load_data(self):
        """Load and type-cast the hospital dataset."""
        if os.path.exists(DATA_PATH):
            df = pd.read_csv(DATA_PATH)
            df['admission_date'] = pd.to_datetime(df['admission_date'])
            df['discharge_date'] = pd.to_datetime(df['discharge_date'])
            df['adm_month'] = df['admission_date'].dt.strftime('%Y-%m')
            df['adm_date_only'] = df['admission_date'].dt.strftime('%Y-%m-%d')
            self._df = df
        else:
            self._df = pd.DataFrame()

    def get_raw_dataframe(self) -> pd.DataFrame:
        if self._df is None or self._df.empty:
            self._load_data()
        return self._df.copy()

    def get_filter_options(self) -> Dict[str, Any]:
        """Return available unique categories and date ranges for dashboard filters."""
        df = self.get_raw_dataframe()
        if df.empty:
            return {}
        return {
            'departments': sorted(df['department'].unique().tolist()),
            'admission_types': sorted(df['admission_type'].unique().tolist()),
            'genders': sorted(df['gender'].unique().tolist()),
            'insurance_providers': sorted(df['insurance_provider'].unique().tolist()),
            'min_date': df['admission_date'].min().strftime('%Y-%m-%d'),
            'max_date': df['admission_date'].max().strftime('%Y-%m-%d'),
            'min_age': int(df['age'].min()),
            'max_age': int(df['age'].max())
        }

    def filter_data(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply user filters across multiple dimensions."""
        df = self.get_raw_dataframe()
        if df.empty:
            return df

        if filters.get('department') and filters['department'] != 'All':
            df = df[df['department'] == filters['department']]

        if filters.get('admission_type') and filters['admission_type'] != 'All':
            df = df[df['admission_type'] == filters['admission_type']]

        if filters.get('gender') and filters['gender'] != 'All':
            df = df[df['gender'] == filters['gender']]

        if filters.get('insurance') and filters['insurance'] != 'All':
            df = df[df['insurance_provider'] == filters['insurance']]

        if filters.get('date_from'):
            df = df[df['admission_date'] >= pd.to_datetime(filters['date_from'])]

        if filters.get('date_to'):
            # Include end of that day
            df = df[df['admission_date'] <= pd.to_datetime(filters['date_to']) + pd.Timedelta(days=1)]

        if filters.get('age_min') is not None and str(filters['age_min']).isdigit():
            df = df[df['age'] >= int(filters['age_min'])]

        if filters.get('age_max') is not None and str(filters['age_max']).isdigit():
            df = df[df['age'] <= int(filters['age_max'])]

        return df

    def get_executive_kpis(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Compute high-level executive KPIs from filtered or full dataset."""
        if df is None:
            df = self.get_raw_dataframe()

        if df.empty:
            return {
                'total_admissions': 0,
                'unique_patients': 0,
                'avg_los': 0.0,
                'readmission_rate_pct': 0.0,
                'er_volume': 0,
                'total_billed': 0.0,
                'critical_triage_pct': 0.0
            }

        total_admissions = len(df)
        unique_patients = int(df['patient_id'].nunique())
        avg_los = round(float(df['length_of_stay'].mean()), 2)
        readmission_rate_pct = round(float(df['readmitted_30d'].mean() * 100), 2)
        er_volume = int(len(df[df['admission_type'].isin(['Emergency', 'Trauma'])]))
        total_billed = round(float(df['billing_amount'].sum()), 2)
        critical_triage_pct = round(float((df['triage_acuity'] <= 2).mean() * 100), 2)

        return {
            'total_admissions': total_admissions,
            'unique_patients': unique_patients,
            'avg_los': avg_los,
            'readmission_rate_pct': readmission_rate_pct,
            'er_volume': er_volume,
            'total_billed': total_billed,
            'critical_triage_pct': critical_triage_pct
        }

    def get_monthly_trends(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Group admissions by month for trend charts."""
        if df is None:
            df = self.get_raw_dataframe()

        if df.empty:
            return {'months': [], 'admissions': [], 'avg_los': [], 'readmission_rate': []}

        monthly = df.groupby('adm_month').agg(
            admissions=('admission_id', 'count'),
            avg_los=('length_of_stay', 'mean'),
            readmission_rate=('readmitted_30d', lambda x: round(x.mean() * 100, 1))
        ).reset_index().sort_values('adm_month')

        monthly['avg_los'] = monthly['avg_los'].round(1)

        return {
            'months': monthly['adm_month'].tolist(),
            'admissions': monthly['admissions'].tolist(),
            'avg_los': monthly['avg_los'].tolist(),
            'readmission_rate': monthly['readmission_rate'].tolist()
        }

    def get_department_benchmarks(self, df: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
        """Compute operational benchmarks per department."""
        if df is None:
            df = self.get_raw_dataframe()

        if df.empty:
            return []

        dept_grp = df.groupby('department').agg(
            total_admissions=('admission_id', 'count'),
            avg_los=('length_of_stay', 'mean'),
            readmission_rate=('readmitted_30d', lambda x: round(x.mean() * 100, 1)),
            total_billing=('billing_amount', 'sum'),
            avg_billing=('billing_amount', 'mean')
        ).reset_index().sort_values('total_admissions', ascending=False)

        dept_grp['avg_los'] = dept_grp['avg_los'].round(1)
        dept_grp['total_billing'] = dept_grp['total_billing'].round(2)
        dept_grp['avg_billing'] = dept_grp['avg_billing'].round(2)

        return dept_grp.to_dict(orient='records')

    def get_los_distribution(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Calculate length of stay histogram bins and summary percentiles."""
        if df is None:
            df = self.get_raw_dataframe()

        if df.empty:
            return {'bins': [], 'counts': [], 'stats': {}}

        los_series = df['length_of_stay']
        # Categorical bins: 1-2, 3-5, 6-9, 10-14, 15+ days
        bins = [0, 2, 5, 9, 14, 100]
        labels = ['1-2 Days (Short)', '3-5 Days (Moderate)', '6-9 Days (Standard)', '10-14 Days (Extended)', '15+ Days (Severe)']
        binned = pd.cut(los_series, bins=bins, labels=labels).value_counts()[labels]

        stats = {
            'min': int(los_series.min()),
            'q25': float(round(los_series.quantile(0.25), 1)),
            'median': float(round(los_series.median(), 1)),
            'q75': float(round(los_series.quantile(0.75), 1)),
            'q90': float(round(los_series.quantile(0.90), 1)),
            'max': int(los_series.max()),
            'mean': float(round(los_series.mean(), 2))
        }

        return {
            'labels': labels,
            'counts': binned.tolist(),
            'stats': stats
        }

    def get_readmission_analysis(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """In-depth breakdown of readmission risk by diagnosis, comorbidity, and disposition."""
        if df is None:
            df = self.get_raw_dataframe()

        if df.empty:
            return {}

        # 1. By Comorbidity Index
        comorb = df.groupby('comorbidity_index').agg(
            total=('admission_id', 'count'),
            rate=('readmitted_30d', lambda x: round(x.mean() * 100, 1))
        ).reset_index()

        # 2. Top Diagnoses with Highest Readmission
        diag = df.groupby('primary_diagnosis').agg(
            admissions=('admission_id', 'count'),
            rate=('readmitted_30d', lambda x: round(x.mean() * 100, 1))
        ).reset_index().sort_values('rate', ascending=False)

        # 3. By Discharge Disposition
        disp = df.groupby('discharge_disposition').agg(
            admissions=('admission_id', 'count'),
            rate=('readmitted_30d', lambda x: round(x.mean() * 100, 1))
        ).reset_index().sort_values('admissions', ascending=False)

        return {
            'by_comorbidity': {
                'index_levels': comorb['comorbidity_index'].tolist(),
                'rates': comorb['rate'].tolist(),
                'counts': comorb['total'].tolist()
            },
            'by_diagnosis': diag.to_dict(orient='records'),
            'by_disposition': disp.to_dict(orient='records')
        }

    def get_er_inflow_metrics(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Emergency department hourly arrivals, day of week patterns, and acuity splits."""
        if df is None:
            df = self.get_raw_dataframe()

        er_cases = df[df['admission_type'].isin(['Emergency', 'Trauma'])].copy()
        if er_cases.empty:
            return {}

        # Hourly Distribution (0 to 23)
        hourly = er_cases.groupby('er_arrival_hour').size().reindex(range(24), fill_value=0)

        # Day of Week Distribution
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily = er_cases['er_arrival_day'].value_counts().reindex(days_order, fill_value=0)

        # Triage Acuity Distribution
        triage_labels = {
            1: 'Acuity 1 (Resuscitation)',
            2: 'Acuity 2 (Emergent)',
            3: 'Acuity 3 (Urgent)',
            4: 'Acuity 4 (Less Urgent)',
            5: 'Acuity 5 (Non-Urgent)'
        }
        triage_counts = er_cases['triage_acuity'].value_counts().sort_index()
        triage_data = {
            'labels': [triage_labels.get(k, f"Level {k}") for k in triage_counts.index],
            'counts': triage_counts.tolist()
        }

        return {
            'total_er_cases': len(er_cases),
            'hourly_labels': [f"{h:02d}:00" for h in range(24)],
            'hourly_counts': hourly.tolist(),
            'daily_labels': days_order,
            'daily_counts': daily.tolist(),
            'triage_data': triage_data,
            'peak_hour': f"{int(hourly.idxmax()):02d}:00",
            'peak_day': str(daily.idxmax())
        }

    def get_demographics(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Patient demographics, age cohorts, gender ratios, insurance mix."""
        if df is None:
            df = self.get_raw_dataframe()

        if df.empty:
            return {}

        # Age Groups
        age_bins = [0, 29, 49, 64, 79, 120]
        age_labels = ['< 30', '30-49', '50-64', '65-79', '80+']
        age_dist = pd.cut(df['age'], bins=age_bins, labels=age_labels).value_counts()[age_labels]

        # Gender & Insurance
        gender_dist = df['gender'].value_counts()
        ins_dist = df['insurance_provider'].value_counts()
        adm_type_dist = df['admission_type'].value_counts()

        return {
            'age_labels': age_labels,
            'age_counts': age_dist.tolist(),
            'gender_labels': gender_dist.index.tolist(),
            'gender_counts': gender_dist.tolist(),
            'insurance_labels': ins_dist.index.tolist(),
            'insurance_counts': ins_dist.tolist(),
            'admission_type_labels': adm_type_dist.index.tolist(),
            'admission_type_counts': adm_type_dist.tolist()
        }

    def get_correlation_matrix(self) -> Dict[str, Any]:
        """Compute Pearson correlation across numerical clinical and operational variables."""
        df = self.get_raw_dataframe()
        numeric_cols = [
            'age', 'triage_acuity', 'comorbidity_index',
            'num_previous_admissions', 'systolic_bp', 'heart_rate',
            'blood_glucose', 'length_of_stay', 'readmitted_30d', 'billing_amount'
        ]
        corr_df = df[numeric_cols].corr().round(2)
        return {
            'columns': numeric_cols,
            'matrix': corr_df.values.tolist()
        }


# Global singleton instance
analytics_service = AnalyticsService()
