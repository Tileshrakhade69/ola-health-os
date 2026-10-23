# OLA Health OS - Power BI Implementation & DAX Architecture Guide

This guide provides end-to-end instructions for Business Intelligence Analysts, Data Analysts, and interview demonstration to construct an enterprise-grade Healthcare Analytics Dashboard in **Power BI Desktop**.

---

## 1. Data Connection Instructions

You can connect Power BI to OLA Health OS through either of the two supported data layers:

### Method A: Direct File Import (CSV Star Schema - Recommended for Quick Setup)
1. Open **Power BI Desktop**.
2. Click **Get Data** > **Text/CSV**.
3. Navigate to the project's `power_bi/` directory and import:
   - `Hospital_Operations_PowerBI.csv` (Single denormalized table), **OR**
   - The Star Schema files:
     - `Fact_Admissions.csv`
     - `Dim_Patient.csv`
     - `Dim_Department.csv`
4. In Power Query Editor, verify data types:
   - `admission_date` & `discharge_date`: **Date/Time**
   - `length_of_stay`, `comorbidity_index`, `triage_acuity`: **Whole Number**
   - `billing_amount`: **Fixed Decimal Number (Currency)**
5. Click **Close & Apply**.

### Method B: Live MySQL Enterprise Connection
1. In Power BI Desktop, click **Get Data** > **MySQL Database**.
2. Server: `localhost:3306`
3. Database: `ola_health_os`
4. Data Connectivity Mode: **Import** (recommended for DAX performance) or **DirectQuery**.
5. Select tables: `admissions`, `patients`, `departments`, `clinical_vitals`.

---

## 2. Star Schema Data Model & Relationships

When using Star Schema tables in the Model View:
```
       [ Dim_Department ] (1)
             │
             │ (1:*) [department]
             ▼
     [ Fact_Admissions ] ◄────── (1:*) [patient_id] ────── [ Dim_Patient ] (1)
             ▲
             │ (1:*) [Date]
       [ Dim_Date ] (1)
```

- `Dim_Patient[patient_id]` (1) ───> `Fact_Admissions[patient_id]` (*)
  - Cardinality: **One-to-Many (1:*)**
  - Cross filter direction: **Single**
- `Dim_Department[department]` (1) ───> `Fact_Admissions[department]` (*)
  - Cardinality: **One-to-Many (1:*)**
  - Cross filter direction: **Single**

---

## 3. Production DAX Measures Reference Table

Create a dedicated measure table called `_Measures` and add the following DAX calculations:

### 1. Total Inpatient Admissions
```dax
Total Admissions = COUNTROWS(Fact_Admissions)
```

### 2. Unique Patients Treated
```dax
Unique Patients = DISTINCTCOUNT(Fact_Admissions[patient_id])
```

### 3. Average Length of Stay (ALOS)
```dax
Avg Length of Stay = 
ROUND(
    AVERAGE(Fact_Admissions[length_of_stay]), 
    1
)
```

### 4. 30-Day Hospital Readmission Rate (%)
```dax
Readmission Rate % = 
DIVIDE(
    CALCULATE(
        COUNTROWS(Fact_Admissions), 
        Fact_Admissions[readmitted_30d] = 1
    ),
    COUNTROWS(Fact_Admissions),
    0
) * 100
```

### 5. High-Acuity Emergency Cases (Triage 1 & 2)
```dax
High Acuity Volume = 
CALCULATE(
    COUNTROWS(Fact_Admissions),
    Fact_Admissions[triage_acuity] IN {1, 2}
)
```

### 6. High-Acuity Share of ER Volume (%)
```dax
High Acuity % = 
DIVIDE(
    [High Acuity Volume],
    CALCULATE(
        COUNTROWS(Fact_Admissions),
        Fact_Admissions[admission_type] IN {"Emergency", "Trauma"}
    ),
    0
) * 100
```

### 7. Total Billed Inpatient Revenue
```dax
Total Inpatient Revenue = SUM(Fact_Admissions[billing_amount])
```

### 8. Average Billed Cost Per Admission
```dax
Avg Cost Per Admission = 
DIVIDE(
    [Total Inpatient Revenue],
    [Total Admissions],
    0
)
```

### 9. Month-Over-Month (MoM) Admissions Growth %
```dax
Admissions MoM Growth % = 
VAR CurrentMonth = [Total Admissions]
VAR PreviousMonth = 
    CALCULATE(
        [Total Admissions], 
        DATEADD(Fact_Admissions[admission_date], -1, MONTH)
    )
RETURN
    DIVIDE(CurrentMonth - PreviousMonth, PreviousMonth, 0) * 100
```

### 10. Extended Stay Outlier Volume (> 14 Days)
```dax
Extended Stay Outliers = 
CALCULATE(
    COUNTROWS(Fact_Admissions),
    Fact_Admissions[length_of_stay] > 14
)
```

---

## 4. Recommended Report Canvas & Visual Layout

### Page 1: Executive Operations Scorecard
- **Top KPI Cards**: Total Admissions, Avg LOS (days), Readmission Rate %, Total Revenue ($M).
- **Line Chart**: Admissions Trend by Month with 3-Month Moving Average.
- **Clustered Bar Chart**: Department Performance (Admissions vs Avg LOS).
- **Donut Chart**: Admissions by Department / Service Line.
- **Top Slicers**: Date Range Picker, Department, Admission Type, Gender.

### Page 2: Emergency Department Surge & Triage Flow
- **Matrix / Heatmap**: ER Arrivals by Day of Week (rows) vs Hour of Day (columns).
- **Stacked Bar Chart**: Triage Acuity Distribution (Levels 1 to 5) across Admission Types.
- **KPI Card**: Peak Arrival Surge Hour and Peak Inflow Day.

### Page 3: Clinical Quality & 30-Day Readmission Analysis
- **Scatter Plot**: Length of Stay (X-axis) vs Readmission Probability (Y-axis), sized by Comorbidity Index.
- **Bar Chart**: Readmission Rate % by Primary Diagnosis (e.g. Heart Failure, COPD, Sepsis).
- **Decomposition Tree Visual**: AI visual decomposing Readmissions by Payer > Department > Age Group.

---

## 5. How to Present This in Placement Interviews
1. **Explain the Star Schema**: Mention why normalizing into dimension tables (`Dim_Patient`, `Dim_Department`) reduces redundancy and accelerates DAX in-memory VertiPaq engine queries.
2. **Discuss the Business Context of DAX Measures**: Emphasize how `Readmission Rate %` directly affects hospital CMS penalties under HRRP (Hospital Readmissions Reduction Program).
3. **Walk Through MoM Trend Calculation**: Explain how time intelligence functions like `DATEADD` and `DIVIDE` handle missing data and division-by-zero safely.
