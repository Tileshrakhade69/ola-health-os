"""
Power BI Data Preparation & Export Pipeline for OLA Health OS.
Transforms hospital clinical data into star-schema dimension and fact tables,
and generates a clean, denormalized CSV file ready for immediate Power BI Desktop ingestion.
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'hospital_data.csv')
EXPORT_DIR = os.path.join(BASE_DIR, 'power_bi')

def export_for_power_bi():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Source data {DATA_PATH} not found.")

    df = pd.read_csv(DATA_PATH)
    print(f"[*] Processing {len(df)} records for Power BI export...")

    # 1. Denormalized One-Click Dataset for Power BI
    pbi_main_path = os.path.join(EXPORT_DIR, 'Hospital_Operations_PowerBI.csv')
    df.to_csv(pbi_main_path, index=False)
    print(f"[OK] Exported denormalized dataset to: {pbi_main_path}")

    # 2. Star Schema Dimension 1: Dim_Patient
    dim_patient = df[[
        'patient_id', 'age', 'gender', 'insurance_provider'
    ]].drop_duplicates(subset=['patient_id']).copy()
    dim_patient['age_group'] = pd.cut(
        dim_patient['age'],
        bins=[0, 29, 49, 64, 79, 120],
        labels=['< 30', '30-49', '50-64', '65-79', '80+']
    )
    dim_patient.to_csv(os.path.join(EXPORT_DIR, 'Dim_Patient.csv'), index=False)

    # 3. Star Schema Dimension 2: Dim_Department
    dim_dept = pd.DataFrame({
        'department': sorted(df['department'].unique()),
        'service_line': [
            'Cardiovascular Services', 'Emergency Services', 'Surgical Services',
            'Internal Medicine', 'Neurosciences', 'Oncology Care',
            'Musculoskeletal', 'Children Services'
        ],
        'standard_bed_capacity': [60, 45, 55, 70, 35, 40, 50, 30]
    })
    dim_dept.to_csv(os.path.join(EXPORT_DIR, 'Dim_Department.csv'), index=False)

    # 4. Star Schema Fact Table: Fact_Admissions
    fact_admissions = df[[
        'admission_id', 'patient_id', 'department', 'admission_date', 'discharge_date',
        'admission_type', 'triage_acuity', 'primary_diagnosis', 'comorbidity_index',
        'num_previous_admissions', 'er_arrival_hour', 'er_arrival_day',
        'length_of_stay', 'readmitted_30d', 'discharge_disposition',
        'billing_amount', 'systolic_bp', 'heart_rate', 'blood_glucose'
    ]].copy()
    fact_admissions.to_csv(os.path.join(EXPORT_DIR, 'Fact_Admissions.csv'), index=False)

    print("[OK] Exported Star Schema tables (Dim_Patient, Dim_Department, Fact_Admissions).")

if __name__ == '__main__':
    export_for_power_bi()
