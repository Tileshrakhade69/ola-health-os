"""
OLA Health OS - Data Generation Engine
Generates realistic, clinical-grade synthetic hospital operational and patient data.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set seeds for deterministic reproducibility
np.random.seed(42)
random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DEPARTMENTS = ["Emergency", "ICU", "Cardiology", "Neurology", "General Surgery", "Pulmonology", "Orthopedics", "Pediatrics"]
BED_TYPES = {
    "Emergency": ["ER Resus Bay", "ER Observation", "ER Rapid Triage"],
    "ICU": ["Medical ICU (MICU)", "Surgical ICU (SICU)", "Cardiac Care (CCU)", "Neuro ICU"],
    "Cardiology": ["Telemetry Step-Down", "Cardio Ward Bed"],
    "Neurology": ["Stroke Unit", "Neuro Observation"],
    "General Surgery": ["Post-Op Recovery", "Surgical Ward Bed"],
    "Pulmonology": ["Respiratory Isolation", "Pulmonary Ward Bed"],
    "Orthopedics": ["Ortho Rehab Bed", "Ortho Ward Bed"],
    "Pediatrics": ["PICU Bed", "Pediatric Ward Bed"]
}

DIAGNOSES = [
    {"name": "Acute Myocardial Infarction", "dept": "Cardiology", "base_los": 4.5, "acuity": "High", "readmit_rate": 0.18},
    {"name": "Congestive Heart Failure", "dept": "Cardiology", "base_los": 5.2, "acuity": "High", "readmit_rate": 0.22},
    {"name": "Sepsis / Septic Shock", "dept": "ICU", "base_los": 7.8, "acuity": "Critical", "readmit_rate": 0.24},
    {"name": "Acute Ischemic Stroke", "dept": "Neurology", "base_los": 6.1, "acuity": "High", "readmit_rate": 0.16},
    {"name": "Severe Pneumonia / ARDS", "dept": "Pulmonology", "base_los": 5.0, "acuity": "Medium", "readmit_rate": 0.14},
    {"name": "COPD Exacerbation", "dept": "Pulmonology", "base_los": 4.2, "acuity": "Medium", "readmit_rate": 0.20},
    {"name": "Multiple Trauma / Fracture", "dept": "Orthopedics", "base_los": 4.8, "acuity": "Medium", "readmit_rate": 0.08},
    {"name": "Acute Appendicitis / Laparotomy", "dept": "General Surgery", "base_los": 2.5, "acuity": "Medium", "readmit_rate": 0.05},
    {"name": "Diabetic Ketoacidosis (DKA)", "dept": "ICU", "base_los": 3.8, "acuity": "High", "readmit_rate": 0.15},
    {"name": "Pediatric Bronchiolitis / Asthma", "dept": "Pediatrics", "base_los": 2.2, "acuity": "Low", "readmit_rate": 0.07},
    {"name": "Acute Renal Failure", "dept": "ICU", "base_los": 6.4, "acuity": "High", "readmit_rate": 0.19},
    {"name": "Gastrointestinal Hemorrhage", "dept": "General Surgery", "base_los": 3.9, "acuity": "High", "readmit_rate": 0.13}
]

def generate_patients(n=3500):
    """Generate patient demographics and medical history."""
    patient_records = []
    first_names_m = ["James", "Alexander", "Marcus", "Ethan", "David", "Leo", "Lucas", "Noah", "William", "Benjamin", "Julian", "Oliver", "Adrian", "Gabriel"]
    first_names_f = ["Emma", "Sophia", "Elena", "Olivia", "Amelia", "Maya", "Isabella", "Clara", "Chloe", "Zoe", "Nora", "Aria", "Victoria", "Hazel"]
    last_names = ["Chen", "Vance", "Mercer", "Alvarez", "Sterling", "Kowalski", "Patel", "Nakamura", "Novak", "O'Connor", "Rossi", "Sinclair", "Holloway", "Kim", "Zhang", "Gupta"]

    for i in range(1, n + 1):
        pid = f"PAT-{i:05d}"
        gender = random.choice(["Male", "Female"])
        first_name = random.choice(first_names_m if gender == "Male" else first_names_f)
        last_name = random.choice(last_names)
        age = int(np.clip(np.random.normal(54, 19), 1, 95))
        
        # Chronic conditions (probabilistic with age)
        p_comorbid = min(0.85, max(0.1, (age - 20) / 75))
        has_hypertension = int(random.random() < p_comorbid * 0.7)
        has_diabetes = int(random.random() < p_comorbid * 0.5)
        has_copd = int(random.random() < p_comorbid * 0.3)
        has_cad = int(random.random() < p_comorbid * 0.4)
        charlson_index = has_hypertension + (has_diabetes * 2) + (has_copd * 2) + (has_cad * 2) + (1 if age > 60 else 0)

        blood_type = random.choice(["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"])
        insurance = random.choices(["Medicare", "Medicaid", "Private Commercial", "Uninsured / Self-Pay"], weights=[0.42, 0.22, 0.31, 0.05])[0]

        patient_records.append({
            "patient_id": pid,
            "full_name": f"{first_name} {last_name}",
            "gender": gender,
            "age": age,
            "blood_type": blood_type,
            "insurance_type": insurance,
            "hypertension": has_hypertension,
            "diabetes": has_diabetes,
            "copd": has_copd,
            "coronary_artery_disease": has_cad,
            "charlson_comorbidity_index": charlson_index
        })
    df = pd.DataFrame(patient_records)
    df.to_csv(os.path.join(DATA_DIR, "patient_records.csv"), index=False)
    print(f"[OK] Generated {len(df)} patient records -> data/patient_records.csv")
    return df

def generate_beds():
    """Generate hospital bed inventory with locations and telemetry links."""
    beds = []
    bed_id_counter = 101

    dept_capacities = {
        "Emergency": 36,
        "ICU": 24,
        "Cardiology": 32,
        "Neurology": 24,
        "General Surgery": 40,
        "Pulmonology": 28,
        "Orthopedics": 26,
        "Pediatrics": 20
    }

    floor_map = {
        "Emergency": "Floor 1 - Wing Alpha",
        "ICU": "Floor 2 - Critical Core",
        "Cardiology": "Floor 3 - Heart Institute",
        "Neurology": "Floor 3 - Neuro Tower",
        "General Surgery": "Floor 4 - Surgical Pavilion",
        "Pulmonology": "Floor 4 - Thoracic Wing",
        "Orthopedics": "Floor 5 - Mobility Center",
        "Pediatrics": "Floor 5 - Children's Wing"
    }

    for dept, cap in dept_capacities.items():
        subtypes = BED_TYPES[dept]
        for i in range(1, cap + 1):
            bid = f"BED-{bed_id_counter}"
            bed_id_counter += 1
            subtype = subtypes[i % len(subtypes)]
            
            # Status: 75% occupied, 15% available, 6% cleaning, 4% maintenance
            status = random.choices(["Occupied", "Available", "Cleaning", "Maintenance"], weights=[0.74, 0.16, 0.06, 0.04])[0]
            
            beds.append({
                "bed_id": bid,
                "department": dept,
                "ward_name": floor_map[dept],
                "bed_type": subtype,
                "room_number": f"{dept[:3].upper()}-{100 + i}",
                "status": status,
                "has_telemetry": 1 if (dept in ["Emergency", "ICU", "Cardiology"] or random.random() < 0.6) else 0,
                "has_ventilator_support": 1 if (dept == "ICU" or (dept == "Emergency" and "Resus" in subtype)) else 0,
                "has_negative_pressure": 1 if (dept == "Pulmonology" and "Isolation" in subtype) else 0,
                "turnaround_time_mins": int(np.random.normal(38, 9))
            })
    df = pd.DataFrame(beds)
    df.to_csv(os.path.join(DATA_DIR, "bed_inventory.csv"), index=False)
    print(f"[OK] Generated {len(df)} bed inventory items -> data/bed_inventory.csv")
    return df

def generate_staff():
    """Generate hospital operational staff across shifts."""
    staff = []
    roles = [
        {"role": "Attending Physician", "base_ratio": 8, "shifts": ["Day (07:00-19:00)", "Night (19:00-07:00)"]},
        {"role": "Emergency Resident", "base_ratio": 6, "shifts": ["Day (07:00-15:00)", "Evening (15:00-23:00)", "Night (23:00-07:00)"]},
        {"role": "ICU Registered Nurse (RN)", "base_ratio": 2, "shifts": ["Day (07:00-19:00)", "Night (19:00-07:00)"]},
        {"role": "Telemetry / Floor Nurse", "base_ratio": 4, "shifts": ["Day (07:00-19:00)", "Night (19:00-07:00)"]},
        {"role": "Respiratory Therapist", "base_ratio": 12, "shifts": ["Day (07:00-19:00)", "Night (19:00-07:00)"]},
        {"role": "Bed Management Coordinator", "base_ratio": 50, "shifts": ["Day (08:00-16:00)", "Evening (16:00-00:00)"]}
    ]

    staff_counter = 1
    for dept in DEPARTMENTS:
        for r in roles:
            # Scale count by department size
            count = 4 if r["role"] == "Attending Physician" else (12 if "Nurse" in r["role"] else 3)
            for _ in range(count):
                sid = f"STF-{staff_counter:04d}"
                staff_counter += 1
                shift = random.choice(r["shifts"])
                workload_score = round(random.uniform(62.0, 94.0), 1)
                burnout_risk = "High" if workload_score > 85 else ("Moderate" if workload_score > 74 else "Normal")
                
                staff.append({
                    "staff_id": sid,
                    "name": f"Provider {staff_counter}",
                    "department": dept,
                    "role": r["role"],
                    "current_shift": shift,
                    "patients_assigned": int(random.uniform(1, r["base_ratio"] + 2)),
                    "shift_hours_worked": round(random.uniform(2.0, 11.5), 1),
                    "workload_score": workload_score,
                    "fatigue_risk_level": burnout_risk,
                    "status": random.choices(["Active", "On Break", "Off Duty"], weights=[0.8, 0.1, 0.1])[0]
                })
    df = pd.DataFrame(staff)
    df.to_csv(os.path.join(DATA_DIR, "staff_schedules.csv"), index=False)
    print(f"[OK] Generated {len(df)} medical staff records -> data/staff_schedules.csv")
    return df

def generate_admissions_and_telemetry(patient_df, bed_df, days_history=120):
    """Generate historical admissions, ER inflow time-series, clinical outcomes, and wearable telemetry."""
    admissions = []
    pids = patient_df["patient_id"].tolist()
    patient_map = patient_df.set_index("patient_id").to_dict(orient="index")
    bed_list = bed_df["bed_id"].tolist()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_history)

    # Inflow simulation: Hour-by-hour over past 120 days
    curr_time = start_date
    adm_counter = 1

    weather_conditions = ["Clear / Mild", "Rain / Storm", "Extreme Heat", "Freezing / Snow", "High Smog / Poor AQI"]

    while curr_time <= end_date:
        # Inflow follows diurnal pattern (peak 11am-2pm and 6pm-9pm, lowest 3am-5am)
        hour = curr_time.hour
        day_of_week = curr_time.weekday() # 0 = Monday, 6 = Sunday
        
        # Diurnal factor
        if 9 <= hour <= 14:
            diurnal = 2.4
        elif 15 <= hour <= 21:
            diurnal = 2.0
        elif 22 <= hour or hour <= 4:
            diurnal = 0.6
        else:
            diurnal = 1.3

        # Weekend factor (higher trauma/ER on Fri/Sat night, higher scheduled Mon morning)
        weekend_factor = 1.25 if day_of_week in [4, 5] and hour >= 18 else (1.15 if day_of_week == 0 and 8 <= hour <= 12 else 1.0)
        
        # Weather influence (e.g. storms/freezing increase accidents/respiratory)
        weather = random.choices(weather_conditions, weights=[0.65, 0.15, 0.08, 0.07, 0.05])[0]
        weather_factor = 1.35 if weather in ["Freezing / Snow", "Rain / Storm"] else (1.2 if weather == "High Smog / Poor AQI" else 1.0)

        # Expected arrivals this hour
        expected_arrivals = int(np.random.poisson(lam=1.8 * diurnal * weekend_factor * weather_factor))
        expected_arrivals = min(expected_arrivals, 8)

        for _ in range(expected_arrivals):
            adm_id = f"ADM-{adm_counter:06d}"
            adm_counter += 1
            pid = random.choice(pids)
            p_info = patient_map[pid]

            diag_obj = random.choice(DIAGNOSES)
            department = diag_obj["dept"]

            # Emergency Severity Index (ESI: 1 = Resuscitation / Immediate, 5 = Non-urgent)
            if diag_obj["acuity"] == "Critical":
                esi_score = random.choices([1, 2], weights=[0.45, 0.55])[0]
            elif diag_obj["acuity"] == "High":
                esi_score = random.choices([2, 3], weights=[0.60, 0.40])[0]
            else:
                esi_score = random.choices([3, 4, 5], weights=[0.50, 0.35, 0.15])[0]

            arrival_mode = random.choices(["Walk-In", "Ambulance", "Helicopter EMS", "Physician Referral"], 
                                         weights=[0.55, 0.33, 0.03, 0.09])[0]
            if esi_score == 1:
                arrival_mode = random.choices(["Ambulance", "Helicopter EMS"], weights=[0.75, 0.25])[0]

            # Wait time (minutes from triage to physician contact)
            base_wait = 15 if esi_score == 1 else (35 if esi_score == 2 else (75 if esi_score == 3 else 120))
            er_wait_time_mins = max(4, int(np.random.normal(base_wait, base_wait * 0.35)))

            # Length of Stay calculation (affected by age, charlson index, acuity, complications)
            age_factor = 1.0 + (p_info["age"] / 100.0) * 0.6
            comorbid_factor = 1.0 + (p_info["charlson_comorbidity_index"] * 0.18)
            noise = np.random.lognormal(mean=0, sigma=0.35)
            los_days = round(float(diag_obj["base_los"] * age_factor * comorbid_factor * noise), 1)
            los_days = max(0.5, min(los_days, 32.0))

            discharge_time = curr_time + timedelta(days=los_days)
            is_currently_admitted = 1 if discharge_time > end_date else 0

            # 30-Day Readmission probability
            readmit_base = diag_obj["readmit_rate"]
            readmit_prob = readmit_base * (1.0 + p_info["charlson_comorbidity_index"] * 0.22) * (1.15 if p_info["age"] > 65 else 1.0)
            readmitted_30d = 1 if (not is_currently_admitted and random.random() < min(0.65, readmit_prob)) else 0

            # Vitals at admission (simulated IoT sensor / initial triage)
            # High acuity leads to abnormal vitals
            if esi_score in [1, 2]:
                hr = int(np.random.normal(118, 18))
                spo2 = int(np.clip(np.random.normal(90, 4), 78, 99))
                sys_bp = int(np.random.normal(152, 24))
                dia_bp = int(np.random.normal(94, 14))
                resp_rate = int(np.random.normal(26, 5))
                temp_c = round(float(np.random.normal(38.4, 0.8)), 1)
            else:
                hr = int(np.random.normal(78, 12))
                spo2 = int(np.clip(np.random.normal(98, 1.5), 94, 100))
                sys_bp = int(np.random.normal(122, 14))
                dia_bp = int(np.random.normal(78, 9))
                resp_rate = int(np.random.normal(16, 2))
                temp_c = round(float(np.random.normal(36.8, 0.4)), 1)

            # National Early Warning Score 2 (NEWS2 approximation: 0 to 18)
            news2_score = 0
            if hr > 110 or hr < 50: news2_score += 2
            if spo2 < 92: news2_score += 3
            elif spo2 < 95: news2_score += 1
            if sys_bp > 160 or sys_bp < 95: news2_score += 2
            if resp_rate > 24 or resp_rate < 10: news2_score += 3
            if temp_c > 38.5 or temp_c < 35.5: news2_score += 2
            if esi_score == 1: news2_score += 4

            # Patient satisfaction score (1-5, lower when wait times are huge or complications occur)
            satisfaction = round(float(np.clip(5.0 - (er_wait_time_mins / 80.0) + np.random.normal(0.4, 0.5), 1.0, 5.0)), 1)

            admissions.append({
                "admission_id": adm_id,
                "patient_id": pid,
                "admission_timestamp": curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                "discharge_timestamp": discharge_time.strftime("%Y-%m-%d %H:%M:%S") if not is_currently_admitted else None,
                "department": department,
                "diagnosis": diag_obj["name"],
                "esi_score": esi_score,
                "arrival_mode": arrival_mode,
                "weather_condition": weather,
                "heart_rate": hr,
                "oxygen_saturation": spo2,
                "systolic_bp": sys_bp,
                "diastolic_bp": dia_bp,
                "respiratory_rate": resp_rate,
                "body_temperature": temp_c,
                "news2_deterioration_score": news2_score,
                "er_wait_time_mins": er_wait_time_mins,
                "length_of_stay_days": los_days,
                "is_currently_admitted": is_currently_admitted,
                "assigned_bed_id": random.choice(bed_list) if is_currently_admitted else None,
                "readmitted_30d": readmitted_30d,
                "patient_satisfaction_score": satisfaction,
                "hour_of_day": hour,
                "day_of_week": day_of_week,
                "month": curr_time.month,
                "is_weekend": 1 if day_of_week in [5, 6] else 0
            })

        curr_time += timedelta(hours=2) # step every 2 hours to get dense 120-day timeline

    df = pd.DataFrame(admissions)
    df.to_csv(os.path.join(DATA_DIR, "hospital_admissions.csv"), index=False)
    print(f"[OK] Generated {len(df)} historical admission events -> data/hospital_admissions.csv")
    return df

def run_all_generation():
    print("=" * 60)
    print(">>> OLA Health OS: Initiating Synthetic Clinical Data Engine")
    print("=" * 60)
    p_df = generate_patients(n=2500)
    b_df = generate_beds()
    s_df = generate_staff()
    adm_df = generate_admissions_and_telemetry(p_df, b_df, days_history=90)
    print(f"[COMPLETE] Synthetic Hospital Datasets fully generated in: {DATA_DIR}")

if __name__ == "__main__":
    run_all_generation()
