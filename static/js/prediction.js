/**
 * OLA Health OS - Prediction Center Interactive Handlers
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. ER Inflow Prediction Form
    const erForm = document.getElementById('er-prediction-form');
    if (erForm) {
        erForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = erForm.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.innerText = 'Calculating Forecast...';

            const payload = {
                day_of_week: document.getElementById('er-day').value,
                day_of_month: parseInt(document.getElementById('er-month-day').value),
                month: parseInt(document.getElementById('er-month').value),
                lag_1: parseFloat(document.getElementById('er-lag1').value || 3),
                lag_7: parseFloat(document.getElementById('er-lag7').value || 4),
                rolling_7d_mean: parseFloat(document.getElementById('er-rolling7').value || 3.5)
            };

            try {
                const res = await fetch('/api/predict/er-inflow', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.error) throw new Error(data.error);

                const resultBox = document.getElementById('er-result-box');
                resultBox.classList.add('active');
                document.getElementById('er-predicted-val').innerText = `${data.predicted_daily_inflow} Patients`;
                document.getElementById('er-surge-status').innerText = data.surge_status;
                document.getElementById('er-staffing-rec').innerText = data.staffing_recommendation;

                showToast('ER Inflow forecasted successfully!', 'success');
            } catch (err) {
                showToast(`Error: ${err.message}`, 'error');
            } finally {
                btn.disabled = false;
                btn.innerText = 'Run Inflow Forecast';
            }
        });
    }

    // 2. Length of Stay (LOS) Prediction Form
    const losForm = document.getElementById('los-prediction-form');
    if (losForm) {
        losForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = losForm.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.innerText = 'Predicting Inpatient Stay...';

            const payload = {
                age: parseInt(document.getElementById('los-age').value),
                gender: document.getElementById('los-gender').value,
                department: document.getElementById('los-department').value,
                admission_type: document.getElementById('los-adm-type').value,
                triage_acuity: parseInt(document.getElementById('los-acuity').value),
                primary_diagnosis: document.getElementById('los-diagnosis').value,
                comorbidity_index: parseInt(document.getElementById('los-comorbidity').value),
                num_previous_admissions: parseInt(document.getElementById('los-prev-adm').value),
                systolic_bp: parseInt(document.getElementById('los-sbp').value),
                heart_rate: parseInt(document.getElementById('los-hr').value),
                blood_glucose: parseFloat(document.getElementById('los-glucose').value)
            };

            try {
                const res = await fetch('/api/predict/los', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.error) throw new Error(data.error);

                const resultBox = document.getElementById('los-result-box');
                resultBox.classList.add('active');
                document.getElementById('los-predicted-val').innerText = `${data.predicted_length_of_stay_days} Days`;
                document.getElementById('los-stay-category').innerText = data.stay_category;
                document.getElementById('los-turnover-impact').innerText = data.bed_turnover_impact;

                showToast('Length of Stay calculated successfully!', 'success');
            } catch (err) {
                showToast(`Error: ${err.message}`, 'error');
            } finally {
                btn.disabled = false;
                btn.innerText = 'Predict Length of Stay';
            }
        });
    }

    // 3. 30-Day Readmission Risk Form
    const readmitForm = document.getElementById('readmission-prediction-form');
    if (readmitForm) {
        readmitForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = readmitForm.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.innerText = 'Stratifying Risk...';

            const payload = {
                age: parseInt(document.getElementById('readmit-age').value),
                gender: document.getElementById('readmit-gender').value,
                department: document.getElementById('readmit-department').value,
                admission_type: document.getElementById('readmit-adm-type').value,
                triage_acuity: parseInt(document.getElementById('readmit-acuity').value),
                primary_diagnosis: document.getElementById('readmit-diagnosis').value,
                comorbidity_index: parseInt(document.getElementById('readmit-comorbidity').value),
                num_previous_admissions: parseInt(document.getElementById('readmit-prev-adm').value),
                length_of_stay: parseInt(document.getElementById('readmit-los').value),
                discharge_disposition: document.getElementById('readmit-disp').value,
                systolic_bp: parseInt(document.getElementById('readmit-sbp').value),
                blood_glucose: parseFloat(document.getElementById('readmit-glucose').value)
            };

            try {
                const res = await fetch('/api/predict/readmission', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.error) throw new Error(data.error);

                const resultBox = document.getElementById('readmit-result-box');
                resultBox.classList.add('active');
                document.getElementById('readmit-predicted-pct').innerText = `${data.readmission_probability_pct}%`;
                
                const tierEl = document.getElementById('readmit-risk-tier');
                tierEl.innerText = data.risk_tier;
                tierEl.className = `badge badge-${data.risk_badge}`;

                document.getElementById('readmit-action-plan').innerText = data.clinical_action_plan;

                showToast('30-Day Readmission risk assessed successfully!', 'success');
            } catch (err) {
                showToast(`Error: ${err.message}`, 'error');
            } finally {
                btn.disabled = false;
                btn.innerText = 'Assess Readmission Risk';
            }
        });
    }
});
