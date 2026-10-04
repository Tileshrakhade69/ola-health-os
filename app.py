"""
OLA Health OS - Futuristic Hospital Operations & Patient Analytics Backend
Flask Application Server & Predictive ML Engine API
"""

import os
import json
import random
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request

import config
import database
from optimizer import optimize_bed_allocation, get_surge_rebalancing_recommendations

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = config.SECRET_KEY

# Global models cache
MODELS = {}

def load_ml_models():
    """Load pre-trained scikit-learn models from disk."""
    global MODELS
    try:
        er_path = os.path.join(config.MODELS_DIR, "er_inflow_model.joblib")
        los_path = os.path.join(config.MODELS_DIR, "los_model.joblib")
        readmit_path = os.path.join(config.MODELS_DIR, "readmission_model.joblib")

        if os.path.exists(er_path):
            MODELS["er_inflow"] = joblib.load(er_path)
        if os.path.exists(los_path):
            MODELS["los"] = joblib.load(los_path)
        if os.path.exists(readmit_path):
            MODELS["readmission"] = joblib.load(readmit_path)
        print(f"[OLA ML] Loaded {len(MODELS)} predictive models into memory.")
    except Exception as e:
        print(f"[OLA ML] Warning loading models: {e}")

# Initialize DB and models on startup
with app.app_context():
    database.init_database()
    load_ml_models()

@app.route("/")
def index():
    """Renders the futuristic OLA Command Center single-page web app."""
    return render_template("index.html")

@app.route("/api/overview", methods=["GET"])
def api_overview():
    """Return top-level operational, staffing, bed occupancy, and alert KPIs."""
    kpi_data = database.fetch_kpi_summary()
    
    # Calculate real-time forecast estimate for next 12 hours
    curr_hour = datetime.now().hour
    is_surge = kpi_data["bed_occupancy_rate"] > 85.0 or kpi_data["avg_er_wait_time_mins"] > 75.0
    
    response = {
        "status": "online",
        "telemetry_sync": "Synchronized (Holographic Mesh)",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "kpis": kpi_data,
        "surge_status": "CRITICAL SURGE" if is_surge else "NOMINAL CAPACITY",
        "system_health": {
            "iot_nodes_active": 418,
            "ai_inference_latency_ms": 12.4,
            "ola_mesh_uptime": "99.98%"
        }
    }
    return jsonify(response)

@app.route("/api/forecast", methods=["GET"])
def api_forecast():
    """
    Generate dynamic 48-hour forward patient inflow forecast using Model 1.
    Includes diurnal cycles, confidence intervals, and emergency surge detection.
    """
    now = datetime.now()
    forecast_points = []
    
    inflow_model = MODELS.get("er_inflow")
    
    running_lag_2h = 3.2
    running_lag_4h = 2.8

    for h_offset in range(0, 48, 2):
        t = now + timedelta(hours=h_offset)
        hour = t.hour
        day_of_week = t.weekday()
        month = t.month
        is_weekend = 1 if day_of_week in [5, 6] else 0
        weather = "Clear / Mild" if h_offset < 24 else "Rain / Storm"
        rolling_mean = (running_lag_2h + running_lag_4h) / 2.0

        if inflow_model:
            input_df = pd.DataFrame([{
                "hour": hour,
                "day_of_week": day_of_week,
                "month": month,
                "is_weekend": is_weekend,
                "weather": weather,
                "lag_2h": running_lag_2h,
                "lag_4h": running_lag_4h,
                "rolling_mean_6h": rolling_mean
            }])
            pred = float(inflow_model.predict(input_df)[0])
        else:
            # Fallback mathematical curve
            diurnal = 2.2 if 9 <= hour <= 21 else 0.8
            pred = 1.8 * diurnal

        pred = max(0.5, round(pred, 2))
        lower_bound = max(0.0, round(pred * 0.78, 2))
        upper_bound = round(pred * 1.25 + 0.5, 2)
        is_surge_hour = pred >= 4.2

        forecast_points.append({
            "timestamp": t.strftime("%Y-%m-%d %H:%M"),
            "hour_label": t.strftime("%a %H:%M"),
            "predicted_arrivals": pred,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "is_surge": is_surge_hour,
            "weather": weather
        })

        running_lag_4h = running_lag_2h
        running_lag_2h = pred

    return jsonify({
        "forecast_horizon_hours": 48,
        "forecast_interval_hours": 2,
        "surge_threshold": 4.2,
        "forecast": forecast_points
    })

@app.route("/api/beds", methods=["GET"])
def api_beds():
    """Return hospital beds categorized by department, status, and telemetry capabilities."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            department,
            ward_name,
            count(*) as total_beds,
            sum(case when status = 'Occupied' then 1 else 0 end) as occupied,
            sum(case when status = 'Available' then 1 else 0 end) as available,
            sum(case when status = 'Cleaning' then 1 else 0 end) as cleaning,
            sum(case when status = 'Maintenance' then 1 else 0 end) as maintenance,
            sum(has_telemetry) as telemetry_enabled,
            sum(has_ventilator_support) as ventilator_equipped
        FROM beds
        GROUP BY department, ward_name
        ORDER BY total_beds DESC
    """)
    departments = [dict(row) for row in cursor.fetchall()]

    for d in departments:
        d["occupancy_pct"] = round((d["occupied"] / d["total_beds"]) * 100, 1) if d["total_beds"] > 0 else 0

    # Detailed bed list sample for interactive grid
    cursor.execute("""
        SELECT bed_id, department, ward_name, bed_type, room_number, status, 
               has_telemetry, has_ventilator_support, turnaround_time_mins
        FROM beds
        ORDER BY department, bed_id
    """)
    all_beds = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "departments": departments,
        "beds": all_beds
    })

@app.route("/api/staff", methods=["GET"])
def api_staff():
    """Return medical staffing workload, burnout risk distribution, and nurse-to-patient ratios."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            department,
            count(*) as total_providers,
            round(avg(workload_score), 1) as avg_workload,
            round(avg(patients_assigned), 1) as avg_patient_ratio,
            sum(case when fatigue_risk_level = 'High' then 1 else 0 end) as high_risk_burnout,
            sum(case when fatigue_risk_level = 'Moderate' then 1 else 0 end) as moderate_risk_burnout,
            sum(case when fatigue_risk_level = 'Normal' then 1 else 0 end) as normal_load
        FROM staff
        WHERE status = 'Active'
        GROUP BY department
    """)
    dept_staff = [dict(row) for row in cursor.fetchall()]

    # Role breakdown
    cursor.execute("""
        SELECT role, count(*) as count, round(avg(workload_score), 1) as avg_score
        FROM staff
        WHERE status = 'Active'
        GROUP BY role
    """)
    role_breakdown = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "departments": dept_staff,
        "roles": role_breakdown
    })

@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    """Return clinical outcomes: Readmissions, Length of Stay distributions, and diagnosis stats."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    # Diagnosis stats
    cursor.execute("""
        SELECT 
            diagnosis,
            department,
            count(*) as total_cases,
            round(avg(length_of_stay_days), 1) as avg_los,
            round(avg(readmitted_30d) * 100, 1) as readmit_pct,
            round(avg(er_wait_time_mins), 0) as avg_er_wait,
            round(avg(patient_satisfaction_score), 2) as satisfaction
        FROM admissions
        GROUP BY diagnosis
        ORDER BY total_cases DESC
    """)
    diagnosis_stats = [dict(row) for row in cursor.fetchall()]

    # Acuity breakdown (ESI levels 1-5)
    cursor.execute("""
        SELECT 
            esi_score,
            count(*) as count,
            round(avg(er_wait_time_mins), 1) as avg_wait_time,
            round(avg(length_of_stay_days), 1) as avg_los
        FROM admissions
        GROUP BY esi_score
        ORDER BY esi_score ASC
    """)
    esi_breakdown = [dict(row) for row in cursor.fetchall()]

    # LoS Distribution buckets
    cursor.execute("""
        SELECT 
            case 
                when length_of_stay_days < 2 then '0-2 Days (Acute)'
                when length_of_stay_days < 5 then '2-5 Days (Moderate)'
                when length_of_stay_days < 9 then '5-9 Days (Extended)'
                else '9+ Days (Complex/ICU)'
            end as los_bucket,
            count(*) as count
        FROM admissions
        GROUP BY los_bucket
        ORDER BY count DESC
    """)
    los_buckets = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "diagnoses": diagnosis_stats,
        "acuity_breakdown": esi_breakdown,
        "los_distribution": los_buckets
    })

@app.route("/api/telemetry", methods=["GET"])
def api_telemetry():
    """Simulate real-time streaming wearable IoT telemetry and clinical emergency feeds."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT event_id, timestamp, patient_id, bed_id, metric_name, metric_value, threshold_status, alert_message
        FROM iot_telemetry_events
        ORDER BY event_id DESC
        LIMIT 10
    """)
    recent_events = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Dynamic live synthetic stream item
    vitals_stream = [
        {"patient": "PAT-00382", "room": "ICU-102", "hr": random.randint(72, 115), "spo2": random.randint(93, 99), "bp": f"{random.randint(118, 145)}/{random.randint(70, 92)}", "news2": random.choice([1, 2, 4]), "status": "Normal"},
        {"patient": "PAT-00914", "room": "CAR-106", "hr": random.randint(68, 88), "spo2": random.randint(96, 100), "bp": f"{random.randint(110, 130)}/{random.randint(68, 82)}", "news2": 0, "status": "Normal"},
        {"patient": "PAT-00120", "room": "PUL-111", "hr": random.randint(92, 128), "spo2": random.randint(89, 93), "bp": f"{random.randint(135, 165)}/{random.randint(85, 100)}", "news2": random.choice([5, 6, 8]), "status": "Elevated"},
        {"patient": "PAT-00741", "room": "SUR-115", "hr": random.randint(64, 82), "spo2": random.randint(97, 99), "bp": f"{random.randint(115, 128)}/{random.randint(72, 80)}", "news2": 1, "status": "Normal"}
    ]

    return jsonify({
        "active_telemetry_streams": vitals_stream,
        "recent_alerts": recent_events
    })

@app.route("/api/predict/inflow", methods=["POST"])
def api_predict_inflow():
    """Predicts patient inflow given user parameters (hour, day, weather)."""
    data = request.get_json() or {}
    hour = int(data.get("hour", 14))
    day_of_week = int(data.get("day_of_week", 1))
    weather = data.get("weather", "Clear / Mild")
    is_weekend = 1 if day_of_week in [5, 6] else 0

    model = MODELS.get("er_inflow")
    if model:
        df = pd.DataFrame([{
            "hour": hour,
            "day_of_week": day_of_week,
            "month": 10,
            "is_weekend": is_weekend,
            "weather": weather,
            "lag_2h": 3.0,
            "lag_4h": 2.5,
            "rolling_mean_6h": 2.8
        }])
        predicted = float(model.predict(df)[0])
    else:
        predicted = 3.5

    predicted = max(0.5, round(predicted, 2))
    surge_risk = "HIGH" if predicted > 4.0 else ("MODERATE" if predicted > 2.8 else "LOW")

    return jsonify({
        "predicted_arrivals_2h": predicted,
        "surge_risk_category": surge_risk,
        "recommended_er_staffing": max(4, int(predicted * 2.2))
    })

@app.route("/api/predict/los", methods=["POST"])
def api_predict_los():
    """Predicts Length of Stay in hospital days for an individual patient profile."""
    data = request.get_json() or {}
    
    age = int(data.get("age", 62))
    gender = data.get("gender", "Male")
    department = data.get("department", "Cardiology")
    diagnosis = data.get("diagnosis", "Congestive Heart Failure")
    esi_score = int(data.get("esi_score", 2))
    arrival_mode = data.get("arrival_mode", "Ambulance")
    
    hypertension = int(data.get("hypertension", 1))
    diabetes = int(data.get("diabetes", 1))
    copd = int(data.get("copd", 0))
    cad = int(data.get("coronary_artery_disease", 1))
    charlson = hypertension + (diabetes * 2) + (copd * 2) + (cad * 2) + (1 if age > 60 else 0)

    heart_rate = int(data.get("heart_rate", 94))
    oxygen_saturation = int(data.get("oxygen_saturation", 94))
    systolic_bp = int(data.get("systolic_bp", 142))
    news2 = int(data.get("news2_deterioration_score", 4))

    model = MODELS.get("los")
    if model:
        features_df = pd.DataFrame([{
            "age": age,
            "gender": gender,
            "department": department,
            "diagnosis": diagnosis,
            "esi_score": esi_score,
            "arrival_mode": arrival_mode,
            "hypertension": hypertension,
            "diabetes": diabetes,
            "copd": copd,
            "coronary_artery_disease": cad,
            "charlson_comorbidity_index": charlson,
            "heart_rate": heart_rate,
            "oxygen_saturation": oxygen_saturation,
            "systolic_bp": systolic_bp,
            "news2_deterioration_score": news2
        }])
        predicted_los = float(model.predict(features_df)[0])
    else:
        predicted_los = 5.2

    predicted_los = max(1.0, round(predicted_los, 1))
    discharge_date = (datetime.now() + timedelta(days=predicted_los)).strftime("%b %d, %Y")

    return jsonify({
        "predicted_los_days": predicted_los,
        "projected_discharge": discharge_date,
        "bed_turnaround_category": "Complex Recovery" if predicted_los > 7 else ("Standard Inpatient" if predicted_los > 3 else "Rapid Discharge"),
        "charlson_score": charlson
    })

@app.route("/api/predict/readmission", methods=["POST"])
def api_predict_readmission():
    """Predicts 30-day readmission risk percentage and severity tier."""
    data = request.get_json() or {}
    
    age = int(data.get("age", 65))
    gender = data.get("gender", "Female")
    department = data.get("department", "Pulmonology")
    diagnosis = data.get("diagnosis", "COPD Exacerbation")
    esi_score = int(data.get("esi_score", 3))
    
    hypertension = int(data.get("hypertension", 1))
    diabetes = int(data.get("diabetes", 1))
    copd = int(data.get("copd", 1))
    cad = int(data.get("coronary_artery_disease", 0))
    charlson = hypertension + (diabetes * 2) + (copd * 2) + (cad * 2) + (1 if age > 60 else 0)

    heart_rate = int(data.get("heart_rate", 88))
    oxygen_saturation = int(data.get("oxygen_saturation", 92))
    news2 = int(data.get("news2_deterioration_score", 3))
    los_days = float(data.get("length_of_stay_days", 4.5))

    model = MODELS.get("readmission")
    if model:
        features_df = pd.DataFrame([{
            "age": age,
            "gender": gender,
            "department": department,
            "diagnosis": diagnosis,
            "esi_score": esi_score,
            "hypertension": hypertension,
            "diabetes": diabetes,
            "copd": copd,
            "coronary_artery_disease": cad,
            "charlson_comorbidity_index": charlson,
            "heart_rate": heart_rate,
            "oxygen_saturation": oxygen_saturation,
            "news2_deterioration_score": news2,
            "length_of_stay_days": los_days
        }])
        prob = float(model.predict_proba(features_df)[0][1])
    else:
        prob = 0.24

    prob_pct = round(prob * 100, 1)
    risk_tier = "CRITICAL RISK" if prob_pct >= 45 else ("MODERATE RISK" if prob_pct >= 22 else "LOW RISK")
    interventions = [
        "Schedule 48-hour Post-Discharge Telehealth Check",
        "Enroll in Remote Patient Monitoring (RPM Wearable SpO2)",
        "Pharmacist Medication Reconciliation Review"
    ] if prob_pct >= 22 else ["Standard Primary Care follow-up in 14 days"]

    return jsonify({
        "readmission_probability_pct": prob_pct,
        "risk_tier": risk_tier,
        "recommended_interventions": interventions
    })

@app.route("/api/optimize/allocate-beds", methods=["POST"])
def api_optimize_beds():
    """Trigger the dynamic bed allocation algorithm and return optimal matching results."""
    optimization_results = optimize_bed_allocation()
    rebalancing = get_surge_rebalancing_recommendations()
    return jsonify({
        "status": "success",
        "optimization": optimization_results,
        "rebalancing_actions": rebalancing
    })

@app.route("/api/models/metrics", methods=["GET"])
def api_models_metrics():
    """Return trained model evaluation performance metrics and feature rankings."""
    metrics_path = os.path.join(config.MODELS_DIR, "model_metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Metrics not found"}), 404

if __name__ == "__main__":
    print(f"[*] OLA Health OS Command Center launching on http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=False)
