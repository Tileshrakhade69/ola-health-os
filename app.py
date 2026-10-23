"""
OLA Health OS - Enterprise Healthcare Analytics & Decision-Support System
Flask Web Application Entrypoint
"""

import os
import io
import math
import pandas as pd
from flask import Flask, render_template, request, jsonify, Response, send_file
from flask_cors import CORS

from config import Config
from database.db_manager import db_manager
from services.analytics_service import analytics_service
from services.data_quality_service import data_quality_service
from services.report_service import report_service
from ml_models.predictor import predictor

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)


# --------------------------------------------------------------------------
# 1. Executive Overview Dashboard
# --------------------------------------------------------------------------
@app.route('/')
@app.route('/overview')
def overview():
    selected_filters = {
        'department': request.args.get('department', 'All'),
        'admission_type': request.args.get('admission_type', 'All'),
        'date_from': request.args.get('date_from', ''),
        'date_to': request.args.get('date_to', '')
    }

    filtered_df = analytics_service.filter_data(selected_filters)
    kpis = analytics_service.get_executive_kpis(filtered_df)
    monthly_trends = analytics_service.get_monthly_trends(filtered_df)
    dept_benchmarks = analytics_service.get_department_benchmarks(filtered_df)
    filter_opts = analytics_service.get_filter_options()

    return render_template(
        'overview.html',
        active_page='overview',
        kpis=kpis,
        monthly_trends=monthly_trends,
        department_benchmarks=dept_benchmarks,
        filter_options=filter_opts,
        selected_filters=selected_filters
    )


# --------------------------------------------------------------------------
# 2. Patient Analytics & Demographics
# --------------------------------------------------------------------------
@app.route('/patient-analytics')
def patient_analytics():
    demographics = analytics_service.get_demographics()
    correlation = analytics_service.get_correlation_matrix()
    return render_template(
        'patient_analytics.html',
        active_page='patient_analytics',
        demographics=demographics,
        correlation=correlation
    )


# --------------------------------------------------------------------------
# 3. Emergency Room Inflow Analysis
# --------------------------------------------------------------------------
@app.route('/er-inflow')
def er_inflow():
    er_data = analytics_service.get_er_inflow_metrics()
    all_metadata = predictor.get_all_metadata()
    er_meta = all_metadata.get('er_inflow') or {}
    chart_preview = er_meta.get('chart_preview') or {'dates': [], 'actual': [], 'predicted': []}

    return render_template(
        'er_inflow.html',
        active_page='er_inflow',
        er_data=er_data,
        model_preview=chart_preview
    )


# --------------------------------------------------------------------------
# 4. Length of Stay (LOS) Analysis
# --------------------------------------------------------------------------
@app.route('/los-analysis')
def los_analysis():
    los_data = analytics_service.get_los_distribution()
    dept_benchmarks = analytics_service.get_department_benchmarks()

    # Outliers with LOS > 14 days
    raw_df = analytics_service.get_raw_dataframe()
    outliers_df = raw_df[raw_df['length_of_stay'] > 14].sort_values('length_of_stay', ascending=False)
    outliers = outliers_df.head(20).to_dict(orient='records')

    return render_template(
        'los_analysis.html',
        active_page='los_analysis',
        los_data=los_data,
        department_benchmarks=dept_benchmarks,
        outliers=outliers
    )


# --------------------------------------------------------------------------
# 5. Readmission Risk Analysis
# --------------------------------------------------------------------------
@app.route('/readmission-analysis')
def readmission_analysis():
    readmit_data = analytics_service.get_readmission_analysis()
    return render_template(
        'readmission.html',
        active_page='readmission',
        readmit_data=readmit_data
    )


# --------------------------------------------------------------------------
# 6. Data Explorer
# --------------------------------------------------------------------------
@app.route('/data-explorer')
def data_explorer():
    search_query = request.args.get('search', '').strip()
    selected_dept = request.args.get('department', 'All')
    selected_readmitted = request.args.get('readmitted', 'All')
    page = int(request.args.get('page', 1))
    per_page = 25

    df = analytics_service.get_raw_dataframe()

    if selected_dept != 'All':
        df = df[df['department'] == selected_dept]

    if selected_readmitted in ['0', '1']:
        df = df[df['readmitted_30d'] == int(selected_readmitted)]

    if search_query:
        mask = (
            df['patient_id'].str.contains(search_query, case=False, na=False) |
            df['admission_id'].str.contains(search_query, case=False, na=False) |
            df['department'].str.contains(search_query, case=False, na=False) |
            df['primary_diagnosis'].str.contains(search_query, case=False, na=False)
        )
        df = df[mask]

    total_count = len(df)
    total_pages = max(1, math.ceil(total_count / per_page))
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    records = df.iloc[start_idx:end_idx].to_dict(orient='records')

    filter_opts = analytics_service.get_filter_options()

    return render_template(
        'data_explorer.html',
        active_page='data_explorer',
        records=records,
        departments=filter_opts.get('departments', []),
        search_query=search_query,
        selected_dept=selected_dept,
        selected_readmitted=selected_readmitted,
        current_page=page,
        total_pages=total_pages,
        total_count=total_count
    )


# --------------------------------------------------------------------------
# 7. Prediction Center
# --------------------------------------------------------------------------
@app.route('/prediction-center')
def prediction_center():
    all_metadata = predictor.get_all_metadata()
    return render_template(
        'prediction_center.html',
        active_page='prediction_center',
        metadata=all_metadata
    )


# --------------------------------------------------------------------------
# 8. Reports and Insights
# --------------------------------------------------------------------------
@app.route('/reports')
def reports():
    briefing = report_service.generate_executive_briefing()
    return render_template(
        'reports.html',
        active_page='reports',
        briefing=briefing
    )


# --------------------------------------------------------------------------
# 9. Data Quality Audit
# --------------------------------------------------------------------------
@app.route('/data-quality')
def data_quality():
    audit_results = data_quality_service.run_full_audit()
    return render_template(
        'data_quality.html',
        active_page='data_quality',
        audit=audit_results
    )


# --------------------------------------------------------------------------
# 10. About Project
# --------------------------------------------------------------------------
@app.route('/about')
def about():
    all_metadata = predictor.get_all_metadata()
    return render_template(
        'about.html',
        active_page='about',
        metadata=all_metadata
    )


# ==========================================================================
# REST API Endpoints
# ==========================================================================

@app.route('/api/db-status')
def api_db_status():
    return jsonify(db_manager.get_connection_info())


@app.route('/api/predict/er-inflow', methods=['POST'])
def api_predict_er():
    try:
        data = request.get_json(force=True) or {}
        result = predictor.predict_er_inflow(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/predict/los', methods=['POST'])
def api_predict_los():
    try:
        data = request.get_json(force=True) or {}
        result = predictor.predict_los(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/predict/readmission', methods=['POST'])
def api_predict_readmission():
    try:
        data = request.get_json(force=True) or {}
        result = predictor.predict_readmission(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/sql-runner', methods=['POST'])
def api_sql_runner():
    try:
        body = request.get_json(force=True) or {}
        query = body.get('query', '').strip()
        if not query:
            return jsonify({'error': 'No query provided.'}), 400

        # Safety restriction: read-only SELECT queries
        clean_q = query.lstrip().upper()
        if not (clean_q.startswith('SELECT') or clean_q.startswith('WITH')):
            return jsonify({'error': 'Safety Restriction: Only read-only SELECT and CTE queries are permitted.'}), 403

        rows = db_manager.execute_query(query)
        # Limit rows to 100 for browser safety
        return jsonify({'rows': rows[:100], 'total_returned': len(rows)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/export-csv')
def export_csv():
    """Download filtered dataset as CSV."""
    search_query = request.args.get('search', '').strip()
    selected_dept = request.args.get('department', 'All')
    selected_readmitted = request.args.get('readmitted', 'All')

    df = analytics_service.get_raw_dataframe()

    if selected_dept != 'All':
        df = df[df['department'] == selected_dept]
    if selected_readmitted in ['0', '1']:
        df = df[df['readmitted_30d'] == int(selected_readmitted)]
    if search_query:
        mask = (
            df['patient_id'].str.contains(search_query, case=False, na=False) |
            df['admission_id'].str.contains(search_query, case=False, na=False) |
            df['department'].str.contains(search_query, case=False, na=False) |
            df['primary_diagnosis'].str.contains(search_query, case=False, na=False)
        )
        df = df[mask]

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return Response(
        csv_buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=ola_health_analytics_export.csv"}
    )


# --------------------------------------------------------------------------
# Error Handlers
# --------------------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(e):
    return render_template('base.html', active_page='404'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('base.html', active_page='500'), 500


if __name__ == '__main__':
    port = Config.PORT
    host = Config.HOST
    print(f"[*] Starting OLA Health OS on http://{host}:{port}")
    app.run(host=host, port=port, debug=Config.DEBUG)
