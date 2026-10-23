"""
Synthetic Healthcare Data Generator for OLA Health OS.
Generates realistic, HIPAA-compliant clinical operations data for analytics,
predictive modeling, and SQL database demonstration.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_hospital_data(n_records: int = 1500, random_state: int = 42) -> pd.DataFrame:
    np.random.seed(random_state)
    random.seed(random_state)

    departments = [
        'Cardiology', 'Emergency', 'General Surgery',
        'Internal Medicine', 'Neurology', 'Oncology',
        'Orthopedics', 'Pediatrics'
    ]
    dept_weights = [0.18, 0.22, 0.12, 0.16, 0.08, 0.07, 0.10, 0.07]

    admission_types = ['Emergency', 'Urgent', 'Elective', 'Trauma']
    adm_weights = [0.45, 0.25, 0.22, 0.08]

    diagnoses = [
        'Acute Myocardial Infarction', 'Congestive Heart Failure',
        'Pneumonia', 'COPD Exacerbation', 'Acute Appendicitis',
        'Severe Sepsis', 'Acute Ischemic Stroke',
        'Type 2 Diabetes with Complications', 'Femur Fracture',
        'Atrial Fibrillation', 'Hypertensive Crisis', 'Kidney Failure'
    ]

    disposition_types = [
        'Home', 'Skilled Nursing Facility', 'Rehabilitation',
        'Home Health Care', 'Against Medical Advice'
    ]
    disp_weights = [0.65, 0.14, 0.10, 0.09, 0.02]

    insurance_types = ['Medicare', 'Medicaid', 'Private Insurance', 'Self-Pay']
    ins_weights = [0.42, 0.18, 0.32, 0.08]

    # Date range: past 18 months
    start_date = datetime(2025, 4, 1)
    end_date = datetime(2026, 9, 30)
    date_delta_days = (end_date - start_date).days

    records = []
    for i in range(1, n_records + 1):
        patient_id = f"PAT-{10000 + (i % 850) + 1}"
        admission_id = f"ADM-{20000 + i}"

        age = int(np.clip(np.random.normal(56, 18), 18, 92))
        gender = np.random.choice(['Male', 'Female'], p=[0.49, 0.51])

        # Department & Admission Type
        department = np.random.choice(departments, p=dept_weights)
        admission_type = np.random.choice(admission_types, p=adm_weights)

        # Admission Date & Time
        random_day_offset = random.randint(0, date_delta_days)
        adm_date = start_date + timedelta(days=random_day_offset)
        arrival_hour = random.choices(
            population=list(range(24)),
            weights=[2, 1, 1, 1, 1, 2, 3, 5, 7, 8, 9, 9, 8, 8, 7, 7, 8, 9, 8, 7, 5, 4, 3, 2]
        )[0]
        adm_datetime = adm_date.replace(hour=arrival_hour, minute=random.randint(0, 59))

        day_of_week = adm_datetime.strftime('%A')

        # Triage Acuity (1 = Resuscitation to 5 = Non-urgent)
        if admission_type in ['Emergency', 'Trauma']:
            triage_acuity = np.random.choice([1, 2, 3, 4], p=[0.10, 0.35, 0.40, 0.15])
        else:
            triage_acuity = np.random.choice([2, 3, 4, 5], p=[0.05, 0.30, 0.45, 0.20])

        # Clinical Diagnosis & Comorbidity
        primary_diagnosis = random.choice(diagnoses)
        # Comorbidity index increases with age
        base_comorbidity = np.random.poisson(lam=1.5 if age < 50 else (2.5 if age < 70 else 3.5))
        comorbidity_index = int(np.clip(base_comorbidity, 0, 7))

        num_previous_admissions = np.random.choice([0, 1, 2, 3, 4], p=[0.55, 0.25, 0.12, 0.05, 0.03])

        # Vitals
        systolic_bp = int(np.clip(np.random.normal(132 + (comorbidity_index * 3), 18), 90, 195))
        heart_rate = int(np.clip(np.random.normal(78 + (5 - triage_acuity) * 4, 14), 52, 145))
        blood_glucose = round(float(np.clip(np.random.normal(115 + (comorbidity_index * 12), 35), 70, 340)), 1)

        # Length of Stay (Right skewed distribution, dependent on acuity, age, comorbidity)
        base_los = np.random.exponential(scale=3.2)
        acuity_factor = (6 - triage_acuity) * 0.7
        comorbidity_factor = comorbidity_index * 0.5
        age_factor = (age / 80.0) * 1.2
        calculated_los = max(1, int(round(base_los + acuity_factor + comorbidity_factor + age_factor)))
        length_of_stay = min(calculated_los, 32)

        discharge_datetime = adm_datetime + timedelta(days=length_of_stay, hours=random.randint(1, 8))
        discharge_disposition = np.random.choice(disposition_types, p=disp_weights)
        insurance = np.random.choice(insurance_types, p=ins_weights)

        # 30-Day Readmission Risk (Realistic probability modeling)
        # Higher risk if: elderly, high comorbidity, multiple previous admissions, short/long stay, ICU/high acuity
        readmission_logit = (
            -2.4
            + (0.015 * (age - 50))
            + (0.35 * comorbidity_index)
            + (0.45 * num_previous_admissions)
            + (0.08 * length_of_stay if length_of_stay > 7 else 0)
            + (0.40 if triage_acuity <= 2 else 0)
            + (0.30 if discharge_disposition in ['Skilled Nursing Facility', 'Home Health Care'] else 0)
        )
        readmission_prob = 1.0 / (1.0 + np.exp(-readmission_logit))
        readmitted_30d = 1 if np.random.rand() < readmission_prob else 0

        # Cost / Billing Amount ($2,500 base + per day + severity)
        billing_amount = round(
            float(2500 + (length_of_stay * 1850) + (comorbidity_index * 1200) + ((5 - triage_acuity) * 2200) + random.normalvariate(0, 1500)),
            2
        )
        billing_amount = max(1500.0, billing_amount)

        records.append({
            'patient_id': patient_id,
            'admission_id': admission_id,
            'age': age,
            'gender': gender,
            'admission_date': adm_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'discharge_date': discharge_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'admission_type': admission_type,
            'department': department,
            'triage_acuity': triage_acuity,
            'primary_diagnosis': primary_diagnosis,
            'comorbidity_index': comorbidity_index,
            'num_previous_admissions': num_previous_admissions,
            'er_arrival_hour': arrival_hour,
            'er_arrival_day': day_of_week,
            'systolic_bp': systolic_bp,
            'heart_rate': heart_rate,
            'blood_glucose': blood_glucose,
            'length_of_stay': length_of_stay,
            'readmitted_30d': readmitted_30d,
            'discharge_disposition': discharge_disposition,
            'insurance_provider': insurance,
            'billing_amount': billing_amount
        })

    df = pd.DataFrame(records)
    return df

if __name__ == '__main__':
    data_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, 'hospital_data.csv')

    print("[*] Generating synthetic hospital operations dataset...")
    df = generate_hospital_data(n_records=1600, random_state=101)
    df.to_csv(csv_path, index=False)
    print(f"[OK] Saved {len(df)} records to {csv_path}")
    print(f"    - Columns: {list(df.columns)}")
    print(f"    - Readmission rate: {df['readmitted_30d'].mean()*100:.2f}%")
    print(f"    - Mean Length of Stay: {df['length_of_stay'].mean():.2f} days")
    print(f"    - Departments: {df['department'].nunique()}")
