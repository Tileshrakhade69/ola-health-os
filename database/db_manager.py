"""
Database Manager for OLA Health OS.
Supports dual-mode database access:
- Mode 1: MySQL (Production / Local Enterprise Server)
- Mode 2: SQLite Demonstration Engine (Zero-configuration fallback using hospital_data.csv)
Provides parameterized query execution, schema initialization, and connection health status.
"""

import os
import sqlite3
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'hospital_data.csv')
SQLITE_DB_PATH = '/tmp/hospital_analytics.db'
class DatabaseManager:
    def __init__(self):
        self.mode = "sqlite"  # 'mysql' or 'sqlite'
        self.mysql_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DB', 'ola_health_os')
        }
        self._initialize()

    def _initialize(self):
        """Attempt MySQL connection if password/env provided; otherwise initialize SQLite."""
        if os.getenv('MYSQL_PASSWORD'):
            try:
                import pymysql
                conn = pymysql.connect(
                    host=self.mysql_config['host'],
                    port=self.mysql_config['port'],
                    user=self.mysql_config['user'],
                    password=self.mysql_config['password'],
                    database=self.mysql_config['database'],
                    connect_timeout=3
                )
                conn.close()
                self.mode = "mysql"
                print(f"[OK] DatabaseManager connected to MySQL at {self.mysql_config['host']}:{self.mysql_config['port']}/{self.mysql_config['database']}")
                return
            except Exception as e:
                print(f"[*] MySQL connection skipped or failed ({e}). Defaulting to SQLite Demonstration Database.")

        self.mode = "sqlite"
        self._init_sqlite_db()

    def _init_sqlite_db(self):
        """Create and populate local SQLite database from hospital_data.csv if not exists."""
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Check if tables exist and have records
        cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='admissions'")
        has_table = cursor.fetchone()[0] > 0

        has_data = False
        if has_table:
            cursor.execute("SELECT COUNT(*) FROM admissions")
            has_data = cursor.fetchone()[0] > 0

        if not has_data and os.path.exists(DATA_PATH):
            df = pd.read_csv(DATA_PATH)

            # 1. Unique Patients table
            patients_df = df[['patient_id', 'age', 'gender', 'insurance_provider']].drop_duplicates(subset=['patient_id'])
            patients_df.to_sql('patients', conn, if_exists='replace', index=False)

            # 2. Admissions table
            adm_cols = [
                'admission_id', 'patient_id', 'admission_date', 'discharge_date',
                'admission_type', 'department', 'triage_acuity', 'primary_diagnosis',
                'comorbidity_index', 'num_previous_admissions', 'er_arrival_hour',
                'er_arrival_day', 'length_of_stay', 'readmitted_30d',
                'discharge_disposition', 'billing_amount'
            ]
            admissions_df = df[adm_cols]
            admissions_df.to_sql('admissions', conn, if_exists='replace', index=False)

            # 3. Clinical Vitals table
            vitals_cols = ['admission_id', 'systolic_bp', 'heart_rate', 'blood_glucose']
            vitals_df = df[vitals_cols].reset_index(names='vital_id')
            vitals_df.to_sql('clinical_vitals', conn, if_exists='replace', index=False)

            # 4. Departments lookup
            dept_df = pd.DataFrame({
                'department_id': range(1, df['department'].nunique() + 1),
                'department_name': df['department'].unique(),
                'total_beds': [60, 45, 55, 70, 35, 40, 50, 30]
            })
            dept_df.to_sql('departments', conn, if_exists='replace', index=False)

            conn.commit()
            print(f"[OK] SQLite database initialized at {SQLITE_DB_PATH} with {len(admissions_df)} records.")

        conn.close()

    def get_connection(self):
        """Return an active connection object for the current active database mode."""
        if self.mode == "mysql":
            import pymysql
            return pymysql.connect(
                host=self.mysql_config['host'],
                port=self.mysql_config['port'],
                user=self.mysql_config['user'],
                password=self.mysql_config['password'],
                database=self.mysql_config['database'],
                cursorclass=pymysql.cursors.DictCursor
            )
        else:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Safely execute a SELECT SQL query and return rows as dictionaries."""
        start_time = datetime.now()
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if self.mode == "mysql":
                rows = cursor.fetchall()
            else:
                rows = [dict(row) for row in cursor.fetchall()]

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            return rows
        finally:
            conn.close()

    def get_connection_info(self) -> Dict[str, Any]:
        """Return connectivity metadata for UI display and status monitoring."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM admissions")
            if self.mode == "mysql":
                count = list(cursor.fetchone().values())[0]
            else:
                count = cursor.fetchone()[0]

            return {
                'status': 'Online',
                'mode': self.mode.upper(),
                'engine': 'MySQL 8.0' if self.mode == 'mysql' else 'SQLite 3 (Demonstration Mode)',
                'total_admissions': count,
                'location': f"{self.mysql_config['host']}:{self.mysql_config['port']}" if self.mode == 'mysql' else 'Local File (hospital_analytics.db)',
                'is_demo_mode': self.mode == 'sqlite'
            }
        except Exception as e:
            return {
                'status': 'Error',
                'mode': self.mode.upper(),
                'error': str(e),
                'is_demo_mode': True
            }
        finally:
            conn.close()


# Global singleton instance
db_manager = DatabaseManager()
