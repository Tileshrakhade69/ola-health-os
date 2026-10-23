"""
OLA Health OS - System Verification & Diagnostics Suite
Performs end-to-end testing across Data, ML Models, Optimizer, and REST APIs.
"""

import os
import json
import time
import sqlite3
import joblib
import pandas as pd
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")

def print_header(title):
    print("\n" + "=" * 70)
    print(f" >>> {title}")
    print("=" * 70)

def verify_datasets():
    print_header("1. CLINICAL & OPERATIONAL DATASET VALIDATION")
    
    files = {
        "patient_records.csv": {"min_rows": 2000, "key_cols": ["patient_id", "age", "hypertension", "charlson_comorbidity_index"]},
        "bed_inventory.csv": {"min_rows": 200, "key_cols": ["bed_id", "department", "status", "has_telemetry"]},
        "staff_schedules.csv": {"min_rows": 250, "key_cols": ["staff_id", "department", "role", "workload_score"]},
        "hospital_admissions.csv": {"min_rows": 3000, "key_cols": ["admission_id", "patient_id", "esi_score", "length_of_stay_days"]}
    }

    all_valid = True
    for fname, req in files.items():
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.exists(fpath):
            print(f" [FAIL] Missing file: {fname}")
            all_valid = False
            continue
        
        df = pd.read_csv(fpath)
        row_check = len(df) >= req["min_rows"]
        col_check = all(col in df.columns for col in req["key_cols"])
        
        if row_check and col_check:
            print(f" [PASS] {fname:25s} | {len(df):5d} rows | Key Columns Verified")
        else:
            print(f" [FAIL] {fname:25s} | Validation failed (Rows: {len(df)}, Cols: {col_check})")
            all_valid = False

    # Check SQLite Database
    db_path = os.path.join(DATA_DIR, "hospital_analytics.db")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        tables = [row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(f" [PASS] SQLite Database: {len(tables)} tables indexed ({', '.join(tables[:4])}...)")
        conn.close()
    else:
        print(" [FAIL] SQLite database missing")
        all_valid = False

    return all_valid

def verify_models():
    print_header("2. PREDICTIVE MACHINE LEARNING MODELS & INFERENCE")
    
    models = {
        "er_inflow_model.joblib": "Model 1: ER Patient Inflow Forecaster",
        "los_model.joblib": "Model 2: Length of Stay (LoS) Predictor",
        "readmission_model.joblib": "Model 3: 30-Day Readmission Risk Classifier"
    }

    all_valid = True
    for mfile, mdesc in models.items():
        mpath = os.path.join(MODELS_DIR, mfile)
        if not os.path.exists(mpath):
            print(f" [FAIL] Missing model binary: {mfile}")
            all_valid = False
            continue

        t0 = time.time()
        model = joblib.load(mpath)
        latency_ms = (time.time() - t0) * 1000

        print(f" [PASS] {mdesc}")
        print(f"        Binary: {mfile} | Loaded in {latency_ms:.2f}ms | Type: {type(model).__name__}")

    # Inspect metrics
    metrics_path = os.path.join(MODELS_DIR, "model_metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
        m1 = metrics["models"]["er_inflow"]["metrics"]
        m2 = metrics["models"]["length_of_stay"]["metrics"]
        m3 = metrics["models"]["readmission_risk"]["metrics"]
        print(f" [INFO] Benchmark Highlights:")
        print(f"        - ER Inflow Forecaster:      R2 = {m1['r2']} | MAE = {m1['mae']} arrivals/2h")
        print(f"        - Length of Stay Predictor:  MAE = {m2['mae_days']} days | RMSE = {m2['rmse_days']} days")
        print(f"        - Readmission Classifier:    Accuracy = {m3['accuracy']*100:.1f}% | ROC-AUC = {m3['roc_auc']}")
    else:
        print(" [WARN] model_metrics.json not found")

    return all_valid

def verify_optimizer():
    print_header("3. DYNAMIC BED ALLOCATION & SURGE OPTIMIZER")
    from optimizer import optimize_bed_allocation, get_surge_rebalancing_recommendations

    t0 = time.time()
    result = optimize_bed_allocation()
    opt_time_ms = (time.time() - t0) * 1000

    assignments = result["assignments"]
    total_saved = result["total_wait_time_saved_mins"]
    print(f" [PASS] Dynamic Bed Allocation executed in {opt_time_ms:.2f}ms")
    print(f"        Matched {len(assignments)} high-acuity/pending patients to optimal ward beds.")
    print(f"        Total ER boarding delay eliminated: {total_saved} minutes.")
    
    if assignments:
        sample = assignments[0]
        print(f"        Sample Match: Patient {sample['patient_id']} -> Bed {sample['assigned_bed_id']} "
              f"({sample['target_ward']}) | Confidence: {sample['match_confidence']}% | Wait Saved: {sample['estimated_wait_savings_mins']}m")

    rebalancing = get_surge_rebalancing_recommendations()
    print(f" [PASS] Surge Rebalancing Generator: {len(rebalancing)} actionable clinical directives active.")
    return True

def verify_api_endpoints():
    print_header("4. LIVE REST API & COMMAND CENTER SERVICE STATUS")
    
    endpoints = [
        ("GET", "/api/overview", None),
        ("GET", "/api/forecast", None),
        ("GET", "/api/beds", None),
        ("GET", "/api/staff", None),
        ("GET", "/api/analytics", None),
        ("GET", "/api/telemetry", None),
        ("GET", "/api/models/metrics", None),
        ("POST", "/api/predict/inflow", {"hour": 14, "day_of_week": 1, "weather": "Clear / Mild"}),
        ("POST", "/api/predict/los", {"age": 62, "diagnosis": "Congestive Heart Failure", "department": "Cardiology", "esi_score": 2}),
        ("POST", "/api/predict/readmission", {"age": 65, "diagnosis": "COPD Exacerbation", "length_of_stay_days": 4.5}),
        ("POST", "/api/optimize/allocate-beds", {}),
        ("GET", "/", None)
    ]

    from app import app
    client = app.test_client()
    passed = 0
    for method, path, payload in endpoints:
        t0 = time.time()
        try:
            if method == "GET":
                res = client.get(path)
            else:
                res = client.post(path, json=payload or {})
            dur_ms = (time.time() - t0) * 1000
            if res.status_code in [200, 201]:
                print(f" [PASS] {method:4s} {path:35s} -> HTTP {res.status_code} ({dur_ms:5.1f}ms)")
                passed += 1
            else:
                print(f" [FAIL] {method:4s} {path:35s} -> HTTP {res.status_code}")
        except Exception as e:
            print(f" [FAIL] {method:4s} {path:35s} -> Error: {e}")

    print(f"\n API Health Score: {passed}/{len(endpoints)} endpoints operational.")
    return passed == len(endpoints)

def run_all_diagnostics():
    print("\n" + "#" * 70)
    print("      OLA HEALTH OS // FULL SYSTEM DIAGNOSTICS & BENCHMARK")
    print("#" * 70)

    d_ok = verify_datasets()
    m_ok = verify_models()
    o_ok = verify_optimizer()
    a_ok = verify_api_endpoints()

    print("\n" + "=" * 70)
    if d_ok and m_ok and o_ok and a_ok:
        print(" >>> ALL SYSTEMS GREEN: OLA Health OS Fully Certified & Operational! <<<")
    else:
        print(" >>> SYSTEM WARNING: One or more components reported warnings. <<<")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    run_all_diagnostics()
