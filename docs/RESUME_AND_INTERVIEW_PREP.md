# OLA Health OS - Data Analyst Resume & Placement Interview Preparation Kit

This document provides career placement materials, ATS-optimized resume bullet points, interview explanations, technical Q&A, and SQL interview challenges tailored to the implementation of **OLA Health OS**.

---

## Part A: Professional Project Titles
Choose one of these titles based on the specific job description:
1. **OLA Health OS: Predictive Healthcare Operations & Clinical BI Platform** *(Recommended for Data Analyst / BI Analyst roles)*
2. **Hospital Operations Analytics & 30-Day Readmission Risk System** *(Recommended for Healthcare Data Analytics roles)*
3. **Clinical Decision-Support & Patient Inflow Prediction Engine** *(Recommended for AI/Data Analytics Intern roles)*

---

## Part B: Concise Project Summary (1-2 Sentences for Resume/LinkedIn)
> Developed an end-to-end Healthcare Analytics and Clinical Decision-Support platform integrating Python, Flask, MySQL, and Power BI to analyze 1,600+ inpatient encounters, forecast emergency room demand, benchmark departmental length of stay, and classify 30-day readmission risk with a 0.724 ROC-AUC.

---

## Part C: ATS-Friendly Resume Bullet Points

- **Data Analytics & EDA:** Engineered an automated healthcare data pipeline in Python (Pandas, NumPy) to profile 1,600+ inpatient admissions, executing missing-value audits, Pearson correlation matrices, and Tukey's IQR outlier analysis to uncover key drivers of hospital stay duration.
- **Relational SQL & Query Optimization:** Designed a normalized MySQL relational schema (admissions, patients, vitals) and authored 12+ analytical queries utilizing Common Table Expressions (CTEs), Window Functions (`LAG`, `DENSE_RANK`), and multi-table aggregations to benchmark department bed turnover and readmission rates.
- **Power BI & Business Intelligence:** Architected a star-schema data model (`Fact_Admissions`, `Dim_Patient`, `Dim_Department`) and authored 10+ production DAX measures (ALOS, MoM growth %, High-Acuity share) in Power BI Desktop to deliver executive KPI visibility.
- **Predictive Machine Learning:** Built and serialized 3 scikit-learn ML pipelines (ER daily demand forecaster, Length of Stay gradient boosting regressor with 2.68-day MAE, and 30-day readmission random forest classifier achieving 69.1% accuracy and 0.724 ROC-AUC) using time-aware chronological validation to prevent data leakage.

---

## Part D: Genuine Technical Skills Demonstrated

- **Programming & Scripting:** Python 3.14 / 3.11, JavaScript (ES6+), HTML5, Vanilla CSS3.
- **Data Manipulation & Analysis:** Pandas, NumPy, SciPy, Data Cleaning, Data Imputation, Missing-Value Profiling, Outlier Detection (Tukey's IQR), Quantile Binning.
- **Database & SQL:** MySQL 8.0, SQLite 3, Relational Schema Design, Foreign Keys, Performance Indexing, CTEs, Window Functions (`LAG`, `DENSE_RANK`, `ROW_NUMBER`), Subqueries, Parameterized Queries.
- **Business Intelligence & Visualization:** Power BI Desktop, Star Schema Modeling, DAX (Data Analysis Expressions), Chart.js, KPI Scorecard Design.
- **Machine Learning & Statistical Modeling:** Scikit-Learn (Pipelines, ColumnTransformer, OneHotEncoder, StandardScaler), Ridge Regression, Gradient Boosting, Random Forest, Time-Series Train/Test Splitting, Confusion Matrices, ROC-AUC, Precision/Recall, MAE, RMSE.
- **Software Engineering & Web Architecture:** Flask 3.1, Jinja2 Templating, RESTful APIs, Environment Configuration (`.env`), Automated Unit Testing (`unittest`), Error Handling.

---

## Part E: 60-Second Interview Elevator Pitch (Verbatim Script)

> "In my final year of B.Tech in Artificial Intelligence, I built **OLA Health OS**, a comprehensive healthcare operations analytics and predictive decision-support system. 
> 
> The core problem I wanted to solve was operational throughput in hospitals: specifically, emergency room overcrowding, extended length of stay, and high 30-day readmissions, which carry heavy CMS financial penalties.
> 
> I built the system in Python and Flask, with a relational database layer supporting both MySQL and SQLite. On the analytics side, I used Pandas to profile 1,600+ inpatient encounters, building interactive dashboards that track Average Length of Stay, diurnal ER arrival curves, and comorbidity risk distributions. I also engineered 12 advanced SQL queries using CTEs and window functions like `LAG` and `DENSE_RANK` to measure month-over-month admissions growth.
> 
> To assist clinical operations, I deployed three machine learning models: a time-aware ER inflow forecaster that achieved an MAE of 0.85 patients per day, a Gradient Boosting model predicting length of stay within 2.68 days, and a Random Forest classifier that stratifies 30-day readmission risk with a 0.724 ROC-AUC. 
> 
> Finally, I prepared a star-schema data model with 10+ DAX measures for Power BI Desktop. The project taught me how to connect statistical analysis and SQL directly to measurable healthcare operational outcomes."

---

## Part F: 10 Technical Interview Questions & Answers

### Q1: Why did you use a chronological split instead of random train_test_split for the ER Inflow model?
**Answer:** ER patient inflow is a time-series aggregation problem where patient arrivals correlate with calendar dynamics (day of week, seasonality, recent 7-day volume). If you perform random k-fold or random train_test_split on time series data, future observations leak into past training sets (data leakage/lookahead bias), giving artificially inflated test scores. By using chronological out-of-time validation (training on the first 80% of days and evaluating on the final 20%), the model simulates real-world forecasting where tomorrow's arrivals are unknown.

### Q2: What is the difference between MAE and RMSE, and why did you report both for the Length of Stay model?
**Answer:** Mean Absolute Error (MAE) measures the average magnitude of errors in the original units (days) and treats all errors linearly. Root Mean Squared Error (RMSE) squares errors before averaging, which penalizes large outlier errors much more heavily. In our LOS model, MAE was 2.68 days and RMSE was 3.74 days. The fact that RMSE is moderately higher than MAE indicates that while typical predictions are within 2.5 days, there are a few severe, complex inpatient cases where the stay was significantly longer than expected.

### Q3: How did you handle categorical variables in your Scikit-Learn pipelines?
**Answer:** I used `ColumnTransformer` with `OneHotEncoder(handle_unknown='ignore')` for nominal categoricals like `department`, `admission_type`, and `primary_diagnosis`. Numerical features like `age`, `blood_glucose`, and `systolic_bp` were passed through `StandardScaler`. Wrapping both inside a Scikit-learn `Pipeline` ensures that the encoders and scalers are fitted strictly on the training set and transformed on the test set, preventing preprocessing leakage.

### Q4: How did you address class imbalance in the 30-Day Readmission model?
**Answer:** Readmissions typically represent a minority of total hospital discharges (in our dataset, ~35.5%). Standard classifiers tend to favor the majority class. I configured `RandomForestClassifier(class_weight='balanced')`, which inversely weights class frequencies during tree splitting, and evaluated using Precision, Recall, F1-score, and ROC-AUC rather than raw Accuracy alone.

### Q5: How does your application ensure SQL injection prevention?
**Answer:** All queries with dynamic user inputs (such as date bounds, department selections, or search terms) use parameterized SQL queries (`cursor.execute(query, params)`) or ORM/Pandas parameter binding rather than string concatenation or f-strings. In addition, the interactive SQL runner endpoint enforces a strict read-only safety policy restricting statements to `SELECT` and `WITH` CTEs.

### Q6: Can you explain Tukey's IQR method implemented on your Data Quality page?
**Answer:** Tukey's IQR rule is a non-parametric outlier detection technique that does not assume a normal Gaussian distribution (crucial for healthcare variables like Length of Stay and Billing, which are heavily right-skewed). We compute the 25th percentile ($Q_1$) and 75th percentile ($Q_3$). The Interquartile Range is $IQR = Q_3 - Q_1$. Lower fence is $Q_1 - 1.5 \times IQR$ and upper fence is $Q_3 + 1.5 \times IQR$. Any observation outside these fences is flagged as a statistical outlier.

### Q7: What is the business and financial significance of the 30-Day Readmission metric in healthcare?
**Answer:** Under the Affordable Care Act and CMS Hospital Readmissions Reduction Program (HRRP), hospitals face up to a 3% reduction in all Medicare reimbursement if their 30-day readmission rates for benchmark conditions (such as Congestive Heart Failure, Pneumonia, Acute Myocardial Infarction, and COPD) exceed national risk-adjusted averages. Stratifying readmission risk enables hospitals to allocate care coordinators, pharmacist medication reconciliation, and home health visits to high-risk patients.

### Q8: How did you design the database schema for analytical querying?
**Answer:** I implemented a relational schema separating patient demographics (`patients`), clinical vitals (`clinical_vitals`), and hospital stays (`admissions`). I added foreign key constraints (`patient_id` and `admission_id`) with cascade rules, and created performance indexes on high-cardinality and frequently filtered columns: `admission_date`, `department`, `admission_type`, and `readmitted_30d`.

### Q9: What happens if MySQL is not installed on the evaluator's machine?
**Answer:** The application features a resilient dual-mode database manager (`DatabaseManager`). It checks environment credentials for MySQL. If MySQL is unavailable, it automatically initializes and populates a local SQLite demonstration database (`hospital_analytics.db`) using ANSI SQL syntax, ensuring that zero setup or configuration is required for a recruiter or interviewer to run and test the application.

### Q10: Why did you include ethical and clinical safety disclaimers across the application?
**Answer:** Machine learning models in healthcare must never be presented as diagnostic tools without rigorous prospective clinical trials, FDA/CE clearance, and IRB approval. As an aspiring Data Analyst, demonstrating domain awareness—including HIPAA privacy, synthetic data labeling, and clinical decision-support boundaries—shows professional maturity and data governance integrity.

---

## Part G: 5 Project-Specific SQL Interview Questions

### SQL 1: Calculate Month-over-Month Admissions Growth Percentage
```sql
WITH monthly_admissions AS (
    SELECT 
        DATE_FORMAT(admission_date, '%Y-%m') AS adm_month,
        COUNT(admission_id) AS current_admissions
    FROM admissions
    GROUP BY DATE_FORMAT(admission_date, '%Y-%m')
)
SELECT 
    adm_month,
    current_admissions,
    LAG(current_admissions, 1) OVER (ORDER BY adm_month) AS prev_admissions,
    ROUND(
        ((current_admissions - LAG(current_admissions, 1) OVER (ORDER BY adm_month)) * 100.0) 
        / NULLIF(LAG(current_admissions, 1) OVER (ORDER BY adm_month), 0), 
        2
    ) AS mom_growth_pct
FROM monthly_admissions;
```
*Key concepts tested:* Common Table Expressions (CTE), `LAG()` Window Function, `NULLIF()` to prevent division by zero.

### SQL 2: Find the Top 3 Most Frequent Diagnoses Per Department
```sql
WITH ranked_diagnoses AS (
    SELECT 
        department,
        primary_diagnosis,
        COUNT(admission_id) AS case_count,
        DENSE_RANK() OVER (
            PARTITION BY department 
            ORDER BY COUNT(admission_id) DESC
        ) AS rank_in_dept
    FROM admissions
    GROUP BY department, primary_diagnosis
)
SELECT department, primary_diagnosis, case_count, rank_in_dept
FROM ranked_diagnoses
WHERE rank_in_dept <= 3
ORDER BY department, rank_in_dept;
```
*Key concepts tested:* `DENSE_RANK()`, `PARTITION BY`, filtering window results via CTE.

### SQL 3: Identify "Super-Utilizer" Patients with Elevated Readmissions
```sql
SELECT 
    p.patient_id,
    p.age,
    p.insurance_provider,
    COUNT(a.admission_id) AS total_admissions,
    SUM(a.readmitted_30d) AS total_readmissions,
    ROUND(AVG(a.length_of_stay), 1) AS avg_los,
    ROUND(SUM(a.billing_amount), 2) AS total_cost
FROM patients p
JOIN admissions a ON p.patient_id = a.patient_id
GROUP BY p.patient_id, p.age, p.insurance_provider
HAVING COUNT(a.admission_id) >= 3 OR SUM(a.readmitted_30d) >= 2
ORDER BY total_readmissions DESC, total_cost DESC;
```
*Key concepts tested:* Inner `JOIN`, `HAVING` clause vs `WHERE` clause, multi-column `GROUP BY`.

### SQL 4: Stratify Inpatient Stay by Acuity and Calculate Critical Case %
```sql
SELECT 
    department,
    COUNT(admission_id) AS total_cases,
    SUM(CASE WHEN triage_acuity <= 2 THEN 1 ELSE 0 END) AS critical_cases,
    ROUND(
        (SUM(CASE WHEN triage_acuity <= 2 THEN 1.0 ELSE 0.0 END) * 100.0) / COUNT(admission_id), 
        1
    ) AS critical_case_pct
FROM admissions
GROUP BY department
ORDER BY critical_case_pct DESC;
```
*Key concepts tested:* Conditional aggregation using `CASE WHEN`, floating-point division.

### SQL 5: Identify Admissions with Length of Stay Exceeding the Department Average
```sql
SELECT 
    a.admission_id,
    a.patient_id,
    a.department,
    a.length_of_stay,
    ROUND(dept_avg.avg_dept_los, 1) AS dept_benchmark_los,
    (a.length_of_stay - ROUND(dept_avg.avg_dept_los, 1)) AS excess_days
FROM admissions a
JOIN (
    SELECT department, AVG(length_of_stay) AS avg_dept_los
    FROM admissions
    GROUP BY department
) dept_avg ON a.department = dept_avg.department
WHERE a.length_of_stay > dept_avg.avg_dept_los
ORDER BY excess_days DESC
LIMIT 15;
```
*Key concepts tested:* Correlated subquery / Derived table `JOIN`, benchmarking comparisons.

---

## Part H: Strategic High-Value Enhancements for Entry-Level Data Analysts

1. **Deploy to Render / Railway / Azure App Service:** Hosting a live web URL to include directly on your resume alongside the GitHub repository link demonstrates end-to-end deployment skills.
2. **Publish a Power BI Service Dashboard Link:** Export the `.pbix` file to Power BI Service (Power BI Web) and create a public or PDF export to embed in your portfolio.
3. **Add Automated PDF Executive Briefing Download:** Implement `WeasyPrint` or `ReportLab` to allow executives to click a button and generate a branded 2-page operational PDF report.
4. **Implement Survival Analysis (Kaplan-Meier Curves):** For a specialized clinical biostatistics role, modeling time-to-readmission using `lifelines` demonstrates advanced healthcare analytical depth.
