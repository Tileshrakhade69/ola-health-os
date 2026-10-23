-- =====================================================================
-- OLA Health OS - Enterprise Healthcare Relational Database Schema
-- Compatible with MySQL 8.0+ and SQLite (ANSI SQL Standard)
-- =====================================================================

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    head_of_department VARCHAR(100),
    total_beds INT DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Patients Table
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(50) PRIMARY KEY,
    age INT NOT NULL,
    gender VARCHAR(20) NOT NULL,
    insurance_provider VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Admissions Fact Table
CREATE TABLE IF NOT EXISTS admissions (
    admission_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL,
    admission_date DATETIME NOT NULL,
    discharge_date DATETIME NOT NULL,
    admission_type VARCHAR(50) NOT NULL,
    department VARCHAR(100) NOT NULL,
    triage_acuity INT NOT NULL CHECK (triage_acuity BETWEEN 1 AND 5),
    primary_diagnosis VARCHAR(255) NOT NULL,
    comorbidity_index INT NOT NULL DEFAULT 0,
    num_previous_admissions INT NOT NULL DEFAULT 0,
    er_arrival_hour INT CHECK (er_arrival_hour BETWEEN 0 AND 23),
    er_arrival_day VARCHAR(20),
    length_of_stay INT NOT NULL CHECK (length_of_stay >= 1),
    readmitted_30d TINYINT NOT NULL DEFAULT 0 CHECK (readmitted_30d IN (0, 1)),
    discharge_disposition VARCHAR(100) NOT NULL,
    billing_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

-- 4. Clinical Vitals Observation Table
CREATE TABLE IF NOT EXISTS clinical_vitals (
    vital_id INT AUTO_INCREMENT PRIMARY KEY,
    admission_id VARCHAR(50) NOT NULL,
    systolic_bp INT,
    heart_rate INT,
    blood_glucose DECIMAL(6, 2),
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id) ON DELETE CASCADE
);

-- =====================================================================
-- Performance Indexes for Analytical Workloads
-- =====================================================================
CREATE INDEX idx_admissions_date ON admissions(admission_date);
CREATE INDEX idx_admissions_department ON admissions(department);
CREATE INDEX idx_admissions_type ON admissions(admission_type);
CREATE INDEX idx_admissions_readmitted ON admissions(readmitted_30d);
CREATE INDEX idx_admissions_los ON admissions(length_of_stay);
CREATE INDEX idx_patients_age ON patients(age);
