"""
OLA Health OS - Relational Database Engine (SQLite & SQLAlchemy Core)
Manages hospital records, bed status, live IoT telemetry feeds, and ML predictions.
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "hospital_analytics.db")

def get_db_connection():
    """Create and return a database connection with dict-like row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database(force_reload=False):
    """Create tables and seed with generated CSV data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if force_reload:
        print("[DB] Dropping existing tables for fresh re-seed...")
        cursor.executescript("""
            DROP TABLE IF EXISTS patients;
            DROP TABLE IF EXISTS beds;
            DROP TABLE IF EXISTS staff;
            DROP TABLE IF EXISTS admissions;
            DROP TABLE IF EXISTS iot_telemetry_events;
            DROP TABLE IF EXISTS optimization_logs;
        """)
        conn.commit()

    # Schema creation
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY,
        full_name TEXT,
        gender TEXT,
        age INTEGER,
        blood_type TEXT,
        insurance_type TEXT,
        hypertension INTEGER,
        diabetes INTEGER,
        copd INTEGER,
        coronary_artery_disease INTEGER,
        charlson_comorbidity_index INTEGER
    );

    CREATE TABLE IF NOT EXISTS beds (
        bed_id TEXT PRIMARY KEY,
        department TEXT,
        ward_name TEXT,
        bed_type TEXT,
        room_number TEXT,
        status TEXT,
        has_telemetry INTEGER,
        has_ventilator_support INTEGER,
        has_negative_pressure INTEGER,
        turnaround_time_mins INTEGER,
        current_patient_id TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS staff (
        staff_id TEXT PRIMARY KEY,
        name TEXT,
        department TEXT,
        role TEXT,
        current_shift TEXT,
        patients_assigned INTEGER,
        shift_hours_worked REAL,
        workload_score REAL,
        fatigue_risk_level TEXT,
        status TEXT
    );

    CREATE TABLE IF NOT EXISTS admissions (
        admission_id TEXT PRIMARY KEY,
        patient_id TEXT,
        admission_timestamp TEXT,
        discharge_timestamp TEXT,
        department TEXT,
        diagnosis TEXT,
        esi_score INTEGER,
        arrival_mode TEXT,
        weather_condition TEXT,
        heart_rate INTEGER,
        oxygen_saturation INTEGER,
        systolic_bp INTEGER,
        diastolic_bp INTEGER,
        respiratory_rate INTEGER,
        body_temperature REAL,
        news2_deterioration_score INTEGER,
        er_wait_time_mins INTEGER,
        length_of_stay_days REAL,
        is_currently_admitted INTEGER,
        assigned_bed_id TEXT,
        readmitted_30d INTEGER,
        patient_satisfaction_score REAL,
        hour_of_day INTEGER,
        day_of_week INTEGER,
        month INTEGER,
        is_weekend INTEGER,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
    );

    CREATE TABLE IF NOT EXISTS iot_telemetry_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        patient_id TEXT,
        bed_id TEXT,
        metric_name TEXT,
        metric_value REAL,
        threshold_status TEXT, -- NORMAL, WARNING, CRITICAL
        alert_message TEXT
    );

    CREATE TABLE IF NOT EXISTS optimization_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        recommendation_type TEXT,
        action_taken TEXT,
        efficiency_gain_est TEXT
    );
    """)
    conn.commit()

    # Load and seed data from CSVs if empty
    cursor.execute("SELECT count(*) as count FROM patients")
    if cursor.fetchone()["count"] == 0:
        print("[DB] Seeding SQLite database from generated CSV files...")
        
        patients_df = pd.read_csv(os.path.join(DATA_DIR, "patient_records.csv"))
        patients_df.to_sql("patients", conn, if_exists="append", index=False)

        beds_df = pd.read_csv(os.path.join(DATA_DIR, "bed_inventory.csv"))
        beds_df.to_sql("beds", conn, if_exists="append", index=False)

        staff_df = pd.read_csv(os.path.join(DATA_DIR, "staff_schedules.csv"))
        staff_df.to_sql("staff", conn, if_exists="append", index=False)

        adm_df = pd.read_csv(os.path.join(DATA_DIR, "hospital_admissions.csv"))
        adm_df.to_sql("admissions", conn, if_exists="append", index=False)

        # Seed initial IoT events
        initial_events = [
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "PAT-00102", "BED-104", "SpO2 Drop", 88.5, "CRITICAL", "Acute desaturation detected via smart optical wearable. Supplemental O2 dispatched."),
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "PAT-00445", "BED-112", "Tachycardia", 134.0, "WARNING", "Sustained supraventricular tachycardia trend > 15 mins. EKG triggered."),
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "PAT-00219", "BED-128", "Hypertensive Surge", 188.0, "CRITICAL", "Systolic BP peaked at 188 mmHg. Telemetry auto-alert to on-call resident."),
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "PAT-00780", "BED-145", "Respiratory Rate Alert", 28.0, "WARNING", "Tachypneic breathing pattern (28 bpm). NEWS2 score jumped to 7."),
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "PAT-00331", "BED-162", "Arrhythmia Alert", 112.0, "WARNING", "Irregular R-R interval signature flagged by wearable patch.")
        ]
        cursor.executemany("""
            INSERT INTO iot_telemetry_events 
            (timestamp, patient_id, bed_id, metric_name, metric_value, threshold_status, alert_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, initial_events)

        conn.commit()
        print("[DB] Initial database seeding successfully completed.")
    else:
        print("[DB] Database already initialized and populated.")

    conn.close()

# Helper queries for operational analytics
def fetch_kpi_summary():
    """Calculates top-level operational and clinical KPIs."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Bed occupancy
    cursor.execute("""
        SELECT 
            count(*) as total_beds,
            sum(case when status = 'Occupied' then 1 else 0 end) as occupied_beds,
            sum(case when status = 'Available' then 1 else 0 end) as available_beds,
            sum(case when status = 'Cleaning' then 1 else 0 end) as cleaning_beds,
            sum(case when status = 'Maintenance' then 1 else 0 end) as maintenance_beds
        FROM beds
    """)
    bed_stats = dict(cursor.fetchone())
    occupancy_rate = round((bed_stats["occupied_beds"] / bed_stats["total_beds"]) * 100, 1)

    # Active inpatients & wait times
    cursor.execute("""
        SELECT 
            count(*) as active_patients,
            round(avg(er_wait_time_mins), 1) as avg_wait_time,
            round(avg(length_of_stay_days), 1) as avg_los,
            round(avg(patient_satisfaction_score), 2) as avg_satisfaction,
            round(avg(readmitted_30d) * 100, 1) as readmit_rate_pct
        FROM admissions
    """)
    adm_stats = dict(cursor.fetchone())

    # Staff metrics
    cursor.execute("""
        SELECT 
            count(*) as total_staff,
            round(avg(workload_score), 1) as avg_workload,
            sum(case when fatigue_risk_level = 'High' then 1 else 0 end) as high_burnout_count
        FROM staff
        WHERE status = 'Active'
    """)
    staff_stats = dict(cursor.fetchone())

    # IoT Alert counts
    cursor.execute("SELECT count(*) as alert_count FROM iot_telemetry_events WHERE threshold_status = 'CRITICAL'")
    critical_alerts = cursor.fetchone()["alert_count"]

    conn.close()

    return {
        "bed_occupancy_rate": occupancy_rate,
        "total_beds": bed_stats["total_beds"],
        "occupied_beds": bed_stats["occupied_beds"],
        "available_beds": bed_stats["available_beds"],
        "cleaning_beds": bed_stats["cleaning_beds"],
        "maintenance_beds": bed_stats["maintenance_beds"],
        "active_inpatients": adm_stats["active_patients"],
        "avg_er_wait_time_mins": adm_stats["avg_wait_time"],
        "avg_length_of_stay_days": adm_stats["avg_los"],
        "avg_patient_satisfaction": adm_stats["avg_satisfaction"],
        "readmission_rate_pct": adm_stats["readmit_rate_pct"],
        "active_staff_count": staff_stats["total_staff"],
        "avg_staff_workload": staff_stats["avg_workload"],
        "high_burnout_staff_count": staff_stats["high_burnout_count"],
        "active_critical_alerts": critical_alerts
    }

if __name__ == "__main__":
    import sys
    reload = "--reload" in sys.argv or "-r" in sys.argv
    init_database(force_reload=reload)
    kpis = fetch_kpi_summary()
    print("Hospital KPI Summary:", kpis)
