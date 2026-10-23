-- =====================================================================
-- OLA Health OS - Analytical SQL Suite
-- Real-World Healthcare Business Intelligence Queries for Data Analysts
-- =====================================================================

-- ---------------------------------------------------------------------
-- QUERY 1: Monthly Admission Trends and Growth Rates
-- Business Goal: Track hospital bed intake volume month-over-month and growth rate.
-- Techniques: Date truncation, Window Function LAG(), Subquery/CTE.
-- ---------------------------------------------------------------------
WITH monthly_admissions AS (
    SELECT 
        DATE_FORMAT(admission_date, '%Y-%m') AS admission_month,
        COUNT(admission_id) AS total_admissions,
        COUNT(DISTINCT patient_id) AS unique_patients,
        ROUND(AVG(length_of_stay), 2) AS avg_los,
        ROUND(SUM(billing_amount), 2) AS total_revenue
    FROM admissions
    GROUP BY DATE_FORMAT(admission_date, '%Y-%m')
)
SELECT 
    admission_month,
    total_admissions,
    unique_patients,
    avg_los,
    total_revenue,
    LAG(total_admissions, 1) OVER (ORDER BY admission_month) AS prev_month_admissions,
    ROUND(
        ((total_admissions - LAG(total_admissions, 1) OVER (ORDER BY admission_month)) * 100.0) 
        / NULLIF(LAG(total_admissions, 1) OVER (ORDER BY admission_month), 0), 
        2
    ) AS mom_growth_pct
FROM monthly_admissions
ORDER BY admission_month DESC;


-- ---------------------------------------------------------------------
-- QUERY 2: Department-Level Operational Benchmarks & Readmission Rate
-- Business Goal: Identify department performance, bed utilization, and readmission risk.
-- Techniques: Aggregations, Conditional Sums, Percentage calculations, ORDER BY.
-- ---------------------------------------------------------------------
SELECT 
    department,
    COUNT(admission_id) AS total_admissions,
    ROUND(AVG(length_of_stay), 2) AS avg_length_of_stay,
    MIN(length_of_stay) AS min_stay_days,
    MAX(length_of_stay) AS max_stay_days,
    SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS total_readmissions,
    ROUND(
        (SUM(CASE WHEN readmitted_30d = 1 THEN 1.0 ELSE 0.0 END) * 100.0) / COUNT(admission_id), 
        2
    ) AS readmission_rate_pct,
    ROUND(AVG(billing_amount), 2) AS avg_billing_per_case
FROM admissions
GROUP BY department
ORDER BY total_admissions DESC;


-- ---------------------------------------------------------------------
-- QUERY 3: Ranking Top High-Volume Clinical Diagnoses within Departments
-- Business Goal: Identify top clinical demand drivers per department for staffing.
-- Techniques: Window Function DENSE_RANK() OVER (PARTITION BY ... ORDER BY ...), CTE.
-- ---------------------------------------------------------------------
WITH diagnosis_counts AS (
    SELECT 
        department,
        primary_diagnosis,
        COUNT(admission_id) AS diagnosis_volume,
        ROUND(AVG(length_of_stay), 2) AS avg_diagnosis_los,
        ROUND(AVG(billing_amount), 2) AS avg_case_cost,
        DENSE_RANK() OVER (
            PARTITION BY department 
            ORDER BY COUNT(admission_id) DESC
        ) AS dept_rank
    FROM admissions
    GROUP BY department, primary_diagnosis
)
SELECT 
    department,
    primary_diagnosis,
    diagnosis_volume,
    avg_diagnosis_los,
    avg_case_cost,
    dept_rank
FROM diagnosis_counts
WHERE dept_rank <= 3
ORDER BY department, dept_rank;


-- ---------------------------------------------------------------------
-- QUERY 4: 30-Day Readmission Risk Stratification by Comorbidity & Age Bracket
-- Business Goal: Clinical quality assurance - evaluate how chronic disease index impacts readmission.
-- Techniques: CASE WHEN bucketization, GROUP BY multiple dimensions.
-- ---------------------------------------------------------------------
SELECT 
    CASE 
        WHEN age < 40 THEN '1. Under 40'
        WHEN age BETWEEN 40 AND 64 THEN '2. 40 to 64'
        ELSE '3. 65 and Older (Seniors)'
    END AS age_cohort,
    CASE 
        WHEN comorbidity_index = 0 THEN 'No Comorbidities (0)'
        WHEN comorbidity_index BETWEEN 1 AND 2 THEN 'Mild / Moderate (1-2)'
        ELSE 'Severe Multimorbidity (3+)'
    END AS comorbidity_tier,
    COUNT(admission_id) AS total_cohort_patients,
    SUM(readmitted_30d) AS readmitted_patients,
    ROUND((SUM(readmitted_30d) * 100.0) / COUNT(admission_id), 2) AS readmission_rate_pct,
    ROUND(AVG(length_of_stay), 2) AS avg_los
FROM admissions a
JOIN patients p ON a.patient_id = p.patient_id
GROUP BY 
    CASE 
        WHEN age < 40 THEN '1. Under 40'
        WHEN age BETWEEN 40 AND 64 THEN '2. 40 to 64'
        ELSE '3. 65 and Older (Seniors)'
    END,
    CASE 
        WHEN comorbidity_index = 0 THEN 'No Comorbidities (0)'
        WHEN comorbidity_index BETWEEN 1 AND 2 THEN 'Mild / Moderate (1-2)'
        ELSE 'Severe Multimorbidity (3+)'
    END
ORDER BY age_cohort, comorbidity_tier;


-- ---------------------------------------------------------------------
-- QUERY 5: Emergency Department Surge Analysis by Day of Week & Arrival Hour
-- Business Goal: Optimize ER shift staffing rosters and triage bed allocations.
-- Techniques: Multi-variable grouping, Filtering emergency cases.
-- ---------------------------------------------------------------------
SELECT 
    er_arrival_day,
    er_arrival_hour,
    COUNT(admission_id) AS er_inflow_count,
    ROUND(AVG(triage_acuity), 2) AS avg_acuity_score,
    SUM(CASE WHEN triage_acuity <= 2 THEN 1 ELSE 0 END) AS critical_resuscitation_cases
FROM admissions
WHERE admission_type IN ('Emergency', 'Trauma')
GROUP BY er_arrival_day, er_arrival_hour
ORDER BY 
    FIELD(er_arrival_day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
    er_arrival_hour;


-- ---------------------------------------------------------------------
-- QUERY 6: Frequent Hospital Users ("High Utilizer" Cohort Analysis)
-- Business Goal: Identify repeat patients with multiple readmissions to assign Care Navigators.
-- Techniques: HAVING clause, JOIN, Window Function ROW_NUMBER().
-- ---------------------------------------------------------------------
SELECT 
    p.patient_id,
    p.age,
    p.gender,
    p.insurance_provider,
    COUNT(a.admission_id) AS recorded_hospital_stays,
    MAX(a.comorbidity_index) AS max_comorbidity_score,
    SUM(a.readmitted_30d) AS total_30d_readmissions,
    ROUND(SUM(a.billing_amount), 2) AS cumulative_billing,
    ROUND(AVG(a.length_of_stay), 2) AS avg_stay_duration
FROM patients p
JOIN admissions a ON p.patient_id = a.patient_id
GROUP BY p.patient_id, p.age, p.gender, p.insurance_provider
HAVING COUNT(a.admission_id) >= 3 OR SUM(a.readmitted_30d) >= 2
ORDER BY total_30d_readmissions DESC, cumulative_billing DESC;


-- ---------------------------------------------------------------------
-- QUERY 7: Outlier Detection - Extended Length of Stay (> 95th Percentile)
-- Business Goal: Discharge planning audit to unblock inpatient beds and reduce stay outliers.
-- Techniques: CTE, NTILE or Percentile ranking, Subqueries.
-- ---------------------------------------------------------------------
WITH los_percentiles AS (
    SELECT 
        admission_id,
        patient_id,
        department,
        primary_diagnosis,
        length_of_stay,
        billing_amount,
        discharge_disposition,
        NTILE(20) OVER (ORDER BY length_of_stay) AS ventile_bucket
    FROM admissions
)
SELECT 
    admission_id,
    patient_id,
    department,
    primary_diagnosis,
    length_of_stay AS outlier_stay_days,
    billing_amount,
    discharge_disposition
FROM los_percentiles
WHERE ventile_bucket = 20  -- Top 5% longest inpatient hospitalizations
ORDER BY length_of_stay DESC;


-- ---------------------------------------------------------------------
-- QUERY 8: Financial Revenue and Average Stay by Payer (Insurance Provider)
-- Business Goal: Managed care contract analysis and commercial vs public reimbursement.
-- Techniques: GROUP BY, Aggregate functions, Percentage share of revenue.
-- ---------------------------------------------------------------------
WITH payer_summary AS (
    SELECT 
        insurance_provider,
        COUNT(a.admission_id) AS total_encounters,
        ROUND(AVG(a.length_of_stay), 2) AS avg_days_stay,
        ROUND(SUM(a.billing_amount), 2) AS total_billed_revenue
    FROM patients p
    JOIN admissions a ON p.patient_id = a.patient_id
    GROUP BY insurance_provider
)
SELECT 
    insurance_provider,
    total_encounters,
    avg_days_stay,
    total_billed_revenue,
    ROUND(
        (total_billed_revenue * 100.0) / (SELECT SUM(total_billed_revenue) FROM payer_summary), 
        2
    ) AS revenue_share_pct
FROM payer_summary
ORDER BY total_billed_revenue DESC;
