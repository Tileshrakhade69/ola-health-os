# OLA Health OS: Enterprise Healthcare Operations & Predictive Analytics System

[![Python](https://img.shields.io/badge/Python-3.14%20%7C%203.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.1-black.svg)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn%201.4+-orange.svg)](https://scikit-learn.org/)
[![Database](https://img.shields.io/badge/Database-MySQL%208.0%20%2F%20SQLite-teal.svg)](https://www.mysql.com/)
[![Power BI](https://img.shields.io/badge/BI-Power%20BI%20Ready-yellow.svg)](https://powerbi.microsoft.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-inspired Healthcare Data Analytics, Decision Support, and Predictive Machine Learning platform designed to analyze hospital throughput, inpatient bed utilization, emergency room surge dynamics, and clinical quality risk. 

Built specifically as an end-to-end portfolio project for **Data Analyst**, **Business Intelligence Analyst**, and **Data Analytics Engineering** placement interviews.

---

## 1. Project Overview & Problem Statement

Modern hospitals encounter complex operational bottlenecks:
- **Emergency Department Overcrowding:** Unanticipated patient inflow surges lead to prolonged triage wait times, bed boarding, and ambulance diversion.
- **Inpatient Bed Scarcity:** Suboptimal discharge planning causes extended Length of Stay (LOS), reducing bed turnover and inflating hospitalization costs.
- **High 30-Day Readmission Penalties:** Regulatory frameworks (e.g., CMS Hospital Readmissions Reduction Program) penalize hospitals for uncoordinated care transitions, particularly among elderly patients with multimorbidities.

**OLA Health OS** addresses these operational hurdles by unifying data ingestion, statistical exploratory data analysis, relational SQL modeling, interactive executive BI dashboards, and three scikit-learn machine learning prediction pipelines into a cohesive platform.

---

## 2. Key Features

1. **Executive Operational Scorecard:** Real-time calculation of admissions volume, Average Length of Stay (ALOS), 30-day readmission rate %, critical emergency volume, and billed hospital revenue.
2. **Patient Demographics & Cohort Intelligence:** Multi-variable cohort analysis exploring age brackets, gender distribution, payer/insurance mix, and Pearson correlation matrices between clinical vitals and stay outcomes.
3. **Emergency Room Inflow Diagnostics:** 24-hour diurnal arrival patterns, day-of-week surge profiling, Canadian/Manchester triage urgency distributions, and peak staffing recommendations.
4. **Inpatient Length of Stay (LOS) Analytics:** Right-skewed duration histograms, non-parametric percentiles (25th, Median, 75th, 90th), departmental stay benchmarks, and extended-stay outlier auditing (>14 days).
5. **30-Day Readmission Risk Stratification:** Risk curves modeled against the Charlson Comorbidity Index, post-acute discharge destinations (Home, Skilled Nursing Facility, Rehab, Home Health), and diagnosis-specific risk tiers.
6. **Clinical Data Explorer:** Interactive query grid featuring multi-column search, departmental and readmission status filters, table pagination, and filtered CSV dataset downloads.
7. **Three Production ML Prediction Modules:**
   - **Module A: ER Inflow Forecaster:** Ridge regression with chronological 80/20 out-of-time validation, lag features (Lag 1, Lag 7, 7-day rolling mean), and calendar predictors.
   - **Module B: Length of Stay Predictor:** Gradient Boosting Regressor predicting inpatient hospital days with Gini feature importances.
   - **Module C: 30-Day Readmission Classifier:** Balanced Random Forest Classifier providing probability scores, confusion matrices, and risk bands.
8. **Automated Executive & Clinical Reports:** Heuristic narrative briefing synthesizing throughput bottlenecks and actionable clinical operational directives.
9. **Data Quality & Schema Audit Suite:** Completeness checks, duplicate detection, deterministic domain boundary rules, and Tukey's Interquartile Range (IQR) outlier fence audits.
10. **Dual Database Architecture & In-Browser SQL Runner:** Operates seamlessly with production MySQL 8.0 or automatic zero-configuration SQLite demonstration fallback, with an interactive analytical SQL runner executing 8+ CTE and window function queries.

---

## 3. Technology Stack

- **Backend & Web Framework:** Python 3.14 / 3.11+, Flask 3.1, Jinja2, Python-Dotenv
- **Data Analytics & Engineering:** Pandas 3.0, NumPy 2.5, SciPy
- **Machine Learning & Modeling:** Scikit-Learn 1.9, Joblib
- **Database & Query Layer:** MySQL 8.0, PyMySQL, SQLAlchemy 2.1, SQLite 3
- **Frontend & Visualization:** Vanilla CSS3 Design System, JavaScript (ES6+), Chart.js 4.4
- **Business Intelligence & Reporting:** Power BI Desktop Star Schema, DAX Measures Suite

---

## 4. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        OLA Health OS Web Client                         │
│     (Responsive Vanilla CSS + Chart.js + Interactive REST Handlers)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / JSON
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          Flask Application (app.py)                    │
│   ├── Analytics Router       ├── REST Prediction Endpoints             │
│   ├── Data Explorer Grid     ├── SQL Query Execution Runner            │
│   └── Data Quality Profiler  └── CSV Streaming Service                 │
└───────────┬───────────────────────────────┬────────────────────────────┘
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌────────────────────────────────────────┐
│  Services & Analytics │       │         ML Prediction Center           │
│  ├── AnalyticsService │       │  ├── ER Inflow Forecaster (Ridge)      │
│  ├── DataQualityAudit │       │  ├── Length of Stay Predictor (GBR)    │
│  └── ReportService    │       │  └── 30d Readmission Classifier (RF)   │
└───────────┬───────────┘       └────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    Dual Data Persistence Layer                         │
│   ├── Mode A: MySQL 8.0 (Enterprise relational schema via .env)        │
│   └── Mode B: SQLite 3 Fallback (Zero-config local demonstration db)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Dataset Description & Synthetic Data Disclosure

- **Records:** 1,600 inpatient admission encounters.
- **Features:** 22 clinical, demographic, operational, and financial columns.
- **Attributes:** `patient_id`, `admission_id`, `age`, `gender`, `admission_date`, `discharge_date`, `admission_type`, `department`, `triage_acuity`, `primary_diagnosis`, `comorbidity_index`, `num_previous_admissions`, `er_arrival_hour`, `er_arrival_day`, `systolic_bp`, `heart_rate`, `blood_glucose`, `length_of_stay`, `readmitted_30d`, `discharge_disposition`, `insurance_provider`, `billing_amount`.
- **Synthetic Data Notice:** All records are synthetically generated using clinical epidemiological distributions (log-normal/exponential stay times, Charlson comorbidity weighting, and realistic vital ranges). The dataset contains zero protected health information (PHI) and strictly complies with HIPAA privacy regulations. It is created for portfolio demonstration and educational evaluation only.

---

## 6. Installation & Quickstart (Windows PowerShell)

### Step 1: Clone or Navigate to Project Directory
```powershell
cd "c:\Users\ASUS\OneDrive\Desktop\OLA HEALTHCARE"
```

### Step 2: Set Up Virtual Environment (Recommended)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Generate Demonstration Dataset & Train ML Models
```powershell
# Generate 1,600-record clinical dataset
python data/generate_dataset.py

# Train, evaluate, and serialize all three ML pipelines
python ml_models/train_models.py

# Export clean Star Schema tables for Power BI
python power_bi/export_data.py
```

### Step 5: (Optional) Configure MySQL 8.0
By default, the application runs out-of-the-box in zero-configuration SQLite demonstration mode. If you wish to connect to a live local MySQL server:
1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Edit `.env` and provide your MySQL root password:
   ```ini
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DB=ola_health_os
   ```
3. Initialize the schema using MySQL Workbench or CLI:
   ```powershell
   & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p < database/schema.sql
   ```

### Step 6: Start the Application Server
```powershell
python app.py
```
Open your web browser and navigate to: **`http://127.0.0.1:5000`**

---

## 7. Machine Learning Model Evaluation Summary

All models were evaluated using rigorous, leakage-free validation protocols:

| Model Task | Algorithm | Target Variable | Validation Strategy | Primary Metric | Secondary Metric |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ER Inflow Forecaster** | Ridge Regression | Daily ER Arrivals | Chronological 80/20 Split | **MAE: 0.85 patients** | RMSE: 1.06 patients |
| **Length of Stay (LOS)** | Gradient Boosting | Inpatient Days | 80/20 Hold-out Split | **MAE: 2.68 days** | RMSE: 3.74 days |
| **30-Day Readmission** | Random Forest | `readmitted_30d` (0/1) | Stratified 80/20 Split | **ROC-AUC: 0.724** | Accuracy: 69.1% (F1: 0.586) |

---

## 8. Analytical SQL Suite

The file `database/analytical_queries.sql` contains production-ready queries answering critical clinical business questions:
- **Query 1:** Monthly admissions volume and Month-over-Month (MoM) growth % utilizing the `LAG()` window function.
- **Query 2:** Department-level operational throughput, average length of stay, and readmission rate %.
- **Query 3:** Top 3 clinical diagnoses per department using `DENSE_RANK() OVER (PARTITION BY department)`.
- **Query 4:** Chronic comorbidity and age cohort risk stratification.
- **Query 5:** Emergency Department arrival surge matrices by day of week and hour.
- **Query 6:** Frequent hospital utilizers ("super-utilizer" cohort identification).
- **Query 7:** Extended length of stay outlier detection (> 95th percentile).
- **Query 8:** Financial revenue and average stay duration by insurance payer.

---

## 9. Power BI Integration

The `power_bi/` directory includes a comprehensive implementation guide (`POWER_BI_GUIDE.md`) and pre-exported CSV tables:
- `Fact_Admissions.csv`
- `Dim_Patient.csv`
- `Dim_Department.csv`
- `Hospital_Operations_PowerBI.csv`

Includes 10+ validated DAX measures:
- `[Total Admissions]`, `[Avg Length of Stay]`, `[Readmission Rate %]`, `[High Acuity Volume]`, `[High Acuity %]`, `[Total Inpatient Revenue]`, `[Admissions MoM Growth %]`, `[Extended Stay Outliers]`.

---

## 10. Automated Testing

Run the automated unit and route integration test suite:
```powershell
python -m unittest discover tests
```
*Current test status: 21 passed tests in 0.7s.*

---

## 11. Clinical Safety & Ethical Disclaimers

> [!WARNING]
> **Prototype Demonstration Notice:**
> 1. OLA Health OS is an analytical prototype created for educational and career placement evaluation.
> 2. It does not provide medical diagnoses, treatment decisions, or clinical triage instructions.
> 3. Real-world hospital deployment requires prospective clinical validation, demographic fairness audits, EHR FHIR/HL7 integration, and Institutional Review Board (IRB) review.

---

## 12. Author & License

- **Developer:** B.Tech Artificial Intelligence Student
- **Specialization:** Healthcare Analytics, BI Engineering, Predictive Modeling, SQL Development
- **License:** Open Source under the MIT License.
