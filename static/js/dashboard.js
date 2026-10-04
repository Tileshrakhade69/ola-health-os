/**
 * OLA Health OS - Master Dashboard Controller
 * Controls tabs, scenario simulations, ML prediction calculators, and KPI state.
 */

const DashboardApp = {
  activeScenario: 'nominal',

  async init() {
    this.setupTabs();
    this.setupScenarioButtons();
    this.setupCalculators();
    await this.fetchOverview();
    await this.fetchModelMetrics();

    // Initialize initial charts
    ChartManager.initInflowForecast('forecast-chart-cockpit');
    ChartManager.initBedCapacity('bed-capacity-chart-cockpit');
    ChartManager.initStaffWorkload('staff-workload-chart-cockpit');
    ChartManager.initDiagnosisOutcomes('outcomes-chart-care');
    ChartManager.initReadmissionDonut('readmit-donut-care');

    // Polling overview every 15s
    setInterval(() => this.fetchOverview(), 15000);
  },

  setupTabs() {
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const targetTab = e.currentTarget.dataset.target;
        
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        e.currentTarget.classList.add('active');

        document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
        const activePane = document.getElementById(targetTab);
        if (activePane) activePane.classList.add('active');

        // Re-render chart sizes if switching
        if (targetTab === 'tab-flow') {
          setTimeout(() => ChartManager.initInflowForecast('forecast-chart-flow-full'), 100);
        } else if (targetTab === 'tab-staff') {
          setTimeout(() => ChartManager.initStaffWorkload('staff-workload-chart-full'), 100);
        } else if (targetTab === 'tab-care') {
          setTimeout(() => {
            ChartManager.initDiagnosisOutcomes('outcomes-chart-care');
            ChartManager.initReadmissionDonut('readmit-donut-care');
          }, 100);
        }
      });
    });
  },

  setupScenarioButtons() {
    const btnNominal = document.getElementById('scenario-nominal');
    const btnCasualty = document.getElementById('scenario-casualty');
    const btnFlu = document.getElementById('scenario-flu');
    const surgeBadge = document.getElementById('surge-status-pill');

    if (btnNominal) {
      btnNominal.addEventListener('click', () => {
        this.activeScenario = 'nominal';
        this.updateScenarioUI(btnNominal, "NOMINAL CAPACITY", false);
        this.fetchOverview();
      });
    }

    if (btnCasualty) {
      btnCasualty.addEventListener('click', () => {
        this.activeScenario = 'casualty';
        this.updateScenarioUI(btnCasualty, "MASS CASUALTY SURGE (DEFCON 1)", true);
        this.simulateSurgeImpact(93.8, 118, 48);
      });
    }

    if (btnFlu) {
      btnFlu.addEventListener('click', () => {
        this.activeScenario = 'flu';
        this.updateScenarioUI(btnFlu, "RESPIRATORY FLU WAVE SURGE", true);
        this.simulateSurgeImpact(88.4, 94, 32);
      });
    }
  },

  updateScenarioUI(activeBtn, badgeText, isCritical) {
    document.querySelectorAll('.btn-scenario').forEach(b => b.classList.remove('active-scenario'));
    if (activeBtn) activeBtn.classList.add('active-scenario');

    const surgeBadge = document.getElementById('surge-status-pill');
    if (surgeBadge) {
      surgeBadge.textContent = badgeText;
      if (isCritical) {
        surgeBadge.classList.add('critical');
      } else {
        surgeBadge.classList.remove('critical');
      }
    }
  },

  simulateSurgeImpact(occupancy, waitTime, alerts) {
    const occEl = document.getElementById('kpi-occupancy');
    const waitEl = document.getElementById('kpi-wait-time');
    const alertEl = document.getElementById('kpi-critical-alerts');
    
    if (occEl) occEl.textContent = `${occupancy}%`;
    if (waitEl) waitEl.textContent = `${waitTime}m`;
    if (alertEl) alertEl.textContent = alerts;
  },

  async fetchOverview() {
    if (this.activeScenario !== 'nominal') return;

    try {
      const res = await fetch('/api/overview');
      const data = await res.json();
      const kpis = data.kpis;

      // Update KPI DOM
      const occEl = document.getElementById('kpi-occupancy');
      const occBar = document.getElementById('kpi-occupancy-bar');
      const inpatientsEl = document.getElementById('kpi-inpatients');
      const waitEl = document.getElementById('kpi-wait-time');
      const staffLoadEl = document.getElementById('kpi-staff-load');
      const readmitEl = document.getElementById('kpi-readmission');
      const alertEl = document.getElementById('kpi-critical-alerts');
      const availBedsEl = document.getElementById('kpi-available-beds');

      if (occEl) occEl.textContent = `${kpis.bed_occupancy_rate}%`;
      if (occBar) occBar.style.width = `${kpis.bed_occupancy_rate}%`;
      if (inpatientsEl) inpatientsEl.textContent = kpis.active_inpatients.toLocaleString();
      if (waitEl) waitEl.textContent = `${kpis.avg_er_wait_time_mins}m`;
      if (staffLoadEl) staffLoadEl.textContent = `${kpis.avg_staff_workload}/100`;
      if (readmitEl) readmitEl.textContent = `${kpis.readmission_rate_pct}%`;
      if (alertEl) alertEl.textContent = kpis.active_critical_alerts;
      if (availBedsEl) availBedsEl.textContent = `${kpis.available_beds} Beds`;

    } catch (err) {
      console.error("Overview fetch error:", err);
    }
  },

  async fetchModelMetrics() {
    try {
      const res = await fetch('/api/models/metrics');
      const data = await res.json();
      
      const m1El = document.getElementById('metric-m1-r2');
      const m1MaeEl = document.getElementById('metric-m1-mae');
      const m2El = document.getElementById('metric-m2-mae');
      const m3El = document.getElementById('metric-m3-acc');
      const m3AucEl = document.getElementById('metric-m3-auc');

      if (data.models) {
        if (m1El) m1El.textContent = data.models.er_inflow.metrics.r2;
        if (m1MaeEl) m1MaeEl.textContent = data.models.er_inflow.metrics.mae;
        if (m2El) m2El.textContent = `${data.models.length_of_stay.metrics.mae_days} days`;
        if (m3El) m3El.textContent = `${(data.models.readmission_risk.metrics.accuracy * 100).toFixed(1)}%`;
        if (m3AucEl) m3AucEl.textContent = data.models.readmission_risk.metrics.roc_auc;

        // Render feature importance lists
        this.renderFeatureImportance('m1-features-list', data.models.er_inflow.top_features);
        this.renderFeatureImportance('m2-features-list', data.models.length_of_stay.top_features);
        this.renderFeatureImportance('m3-features-list', data.models.readmission_risk.top_features);
      }
    } catch (err) {
      console.error("Model metrics error:", err);
    }
  },

  renderFeatureImportance(containerId, features) {
    const el = document.getElementById(containerId);
    if (!el || !features) return;

    el.innerHTML = features.map(f => `
      <div style="margin-bottom:0.4rem; font-size:0.75rem;">
        <div style="display:flex; justify-content:space-between; color:#94a3b8; margin-bottom:2px;">
          <span>${f.feature.replace(/cat__|num__|diag__|weather__/g, '')}</span>
          <span style="font-family:'JetBrains Mono'; color:#00f0ff;">${(f.importance * 100).toFixed(1)}%</span>
        </div>
        <div style="height:4px; background:rgba(255,255,255,0.06); border-radius:2px; overflow:hidden;">
          <div style="width:${Math.min(100, f.importance * 200)}%; height:100%; background:#00f0ff;"></div>
        </div>
      </div>
    `).join('');
  },

  setupCalculators() {
    // 1. Inflow Predictor
    const btnInflow = document.getElementById('btn-calc-inflow');
    if (btnInflow) {
      btnInflow.addEventListener('click', async () => {
        const hour = document.getElementById('calc-inflow-hour').value;
        const dow = document.getElementById('calc-inflow-dow').value;
        const weather = document.getElementById('calc-inflow-weather').value;

        const res = await fetch('/api/predict/inflow', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ hour, day_of_week: dow, weather })
        });
        const data = await res.json();

        document.getElementById('res-inflow-val').textContent = data.predicted_arrivals_2h;
        document.getElementById('res-inflow-surge').textContent = data.surge_risk_category;
        document.getElementById('res-inflow-staff').textContent = `${data.recommended_er_staffing} ER Providers`;
      });
    }

    // 2. Length of Stay Predictor
    const btnLos = document.getElementById('btn-calc-los');
    if (btnLos) {
      btnLos.addEventListener('click', async () => {
        const age = document.getElementById('calc-los-age').value;
        const dept = document.getElementById('calc-los-dept').value;
        const diag = document.getElementById('calc-los-diag').value;
        const esi = document.getElementById('calc-los-esi').value;
        const hr = document.getElementById('calc-los-hr').value;
        const spo2 = document.getElementById('calc-los-spo2').value;
        const sys = document.getElementById('calc-los-sys').value;

        const res = await fetch('/api/predict/los', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            age, department: dept, diagnosis: diag, esi_score: esi,
            heart_rate: hr, oxygen_saturation: spo2, systolic_bp: sys
          })
        });
        const data = await res.json();

        document.getElementById('res-los-val').textContent = `${data.predicted_los_days} Days`;
        document.getElementById('res-los-discharge').textContent = `Target: ${data.projected_discharge}`;
        document.getElementById('res-los-category').textContent = data.bed_turnaround_category;
      });
    }

    // 3. Readmission Risk Predictor
    const btnReadmit = document.getElementById('btn-calc-readmit');
    if (btnReadmit) {
      btnReadmit.addEventListener('click', async () => {
        const age = document.getElementById('calc-readmit-age').value;
        const diag = document.getElementById('calc-readmit-diag').value;
        const los = document.getElementById('calc-readmit-los').value;
        const hr = document.getElementById('calc-readmit-hr').value;
        const spo2 = document.getElementById('calc-readmit-spo2').value;
        const news2 = document.getElementById('calc-readmit-news2').value;

        const res = await fetch('/api/predict/readmission', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            age, diagnosis: diag, length_of_stay_days: los,
            heart_rate: hr, oxygen_saturation: spo2, news2_deterioration_score: news2
          })
        });
        const data = await res.json();

        document.getElementById('res-readmit-val').textContent = `${data.readmission_probability_pct}%`;
        const tierEl = document.getElementById('res-readmit-tier');
        tierEl.textContent = data.risk_tier;
        tierEl.className = `rebalance-badge ${data.risk_tier.includes('CRITICAL') ? 'high' : 'medium'}`;

        const interEl = document.getElementById('res-readmit-interventions');
        if (interEl) {
          interEl.innerHTML = data.recommended_interventions.map(i => `<li>${i}</li>`).join('');
        }
      });
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  DashboardApp.init();
});
