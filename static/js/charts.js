/**
 * OLA Health OS - Chart Visualization Suite
 * Built on Chart.js with glowing cyber-clinical themes.
 */

const ChartManager = {
  instances: {},

  // Common dark theme options
  defaultOptions: {
    responsive: true,
    maintainAspectRatio: false,
    color: '#94a3b8',
    plugins: {
      legend: {
        labels: {
          color: '#94a3b8',
          font: { family: "'Inter', sans-serif", size: 11 }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(12, 19, 34, 0.95)',
        titleColor: '#00f0ff',
        bodyColor: '#f8fafc',
        borderColor: 'rgba(56, 189, 248, 0.3)',
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#64748b', font: { family: "'JetBrains Mono', monospace", size: 10 } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#64748b', font: { family: "'JetBrains Mono', monospace", size: 10 } }
      }
    }
  },

  async initInflowForecast(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    try {
      const res = await fetch('/api/forecast');
      const data = await res.json();

      const labels = data.forecast.map(p => p.hour_label);
      const predicted = data.forecast.map(p => p.predicted_arrivals);
      const upper = data.forecast.map(p => p.upper_bound);
      const lower = data.forecast.map(p => p.lower_bound);
      const surgeThresholds = data.forecast.map(() => data.surge_threshold);

      if (this.instances.forecast) this.instances.forecast.destroy();

      this.instances.forecast = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Predicted Arrivals (per 2h)',
              data: predicted,
              borderColor: '#00f0ff',
              backgroundColor: 'rgba(0, 240, 255, 0.12)',
              fill: true,
              tension: 0.35,
              borderWidth: 2.5,
              pointRadius: 3,
              pointBackgroundColor: '#00f0ff'
            },
            {
              label: 'Upper Confidence (95%)',
              data: upper,
              borderColor: 'rgba(56, 189, 248, 0.4)',
              borderDash: [4, 4],
              borderWidth: 1.5,
              fill: false,
              pointRadius: 0
            },
            {
              label: 'Lower Confidence (95%)',
              data: lower,
              borderColor: 'rgba(56, 189, 248, 0.25)',
              borderDash: [4, 4],
              borderWidth: 1,
              fill: false,
              pointRadius: 0
            },
            {
              label: 'ER Surge Trigger Threshold',
              data: surgeThresholds,
              borderColor: '#f43f5e',
              borderDash: [6, 6],
              borderWidth: 1.5,
              fill: false,
              pointRadius: 0
            }
          ]
        },
        options: {
          ...this.defaultOptions,
          interaction: { mode: 'index', intersect: false }
        }
      });
    } catch (err) {
      console.error("Forecast chart error:", err);
    }
  },

  async initBedCapacity(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    try {
      const res = await fetch('/api/beds');
      const data = await res.json();

      const labels = data.departments.map(d => d.department);
      const occupied = data.departments.map(d => d.occupied);
      const available = data.departments.map(d => d.available);
      const cleaning = data.departments.map(d => d.cleaning);
      const maintenance = data.departments.map(d => d.maintenance);

      if (this.instances.beds) this.instances.beds.destroy();

      this.instances.beds = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [
            { label: 'Occupied', data: occupied, backgroundColor: 'rgba(244, 63, 94, 0.8)' },
            { label: 'Available', data: available, backgroundColor: 'rgba(16, 185, 129, 0.8)' },
            { label: 'Cleaning', data: cleaning, backgroundColor: 'rgba(245, 158, 11, 0.8)' },
            { label: 'Maintenance', data: maintenance, backgroundColor: 'rgba(100, 116, 139, 0.6)' }
          ]
        },
        options: {
          ...this.defaultOptions,
          indexAxis: 'y',
          scales: {
            x: { stacked: true, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
            y: { stacked: true, grid: { color: 'rgba(255, 255, 255, 0.05)' } }
          }
        }
      });
    } catch (err) {
      console.error("Bed capacity chart error:", err);
    }
  },

  async initStaffWorkload(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    try {
      const res = await fetch('/api/staff');
      const data = await res.json();

      const labels = data.departments.map(d => d.department);
      const workloadScores = data.departments.map(d => d.avg_workload);
      const patientRatios = data.departments.map(d => d.avg_patient_ratio);

      if (this.instances.staff) this.instances.staff.destroy();

      this.instances.staff = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Avg Workload Score (0-100)',
              data: workloadScores,
              backgroundColor: 'rgba(0, 240, 255, 0.75)',
              borderColor: '#00f0ff',
              borderWidth: 1,
              borderRadius: 4
            },
            {
              label: 'Assigned Patients / Provider',
              data: patientRatios,
              backgroundColor: 'rgba(99, 102, 241, 0.75)',
              borderColor: '#6366f1',
              borderWidth: 1,
              borderRadius: 4
            }
          ]
        },
        options: this.defaultOptions
      });
    } catch (err) {
      console.error("Staff chart error:", err);
    }
  },

  async initDiagnosisOutcomes(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    try {
      const res = await fetch('/api/analytics');
      const data = await res.json();

      const topDiag = data.diagnoses.slice(0, 8);
      const labels = topDiag.map(d => d.diagnosis.length > 20 ? d.diagnosis.substring(0, 18) + '...' : d.diagnosis);
      const los = topDiag.map(d => d.avg_los);
      const satisfaction = topDiag.map(d => d.satisfaction);

      if (this.instances.outcomes) this.instances.outcomes.destroy();

      this.instances.outcomes = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [
            {
              type: 'bar',
              label: 'Avg Length of Stay (Days)',
              data: los,
              backgroundColor: 'rgba(56, 189, 248, 0.7)',
              yAxisID: 'y'
            },
            {
              type: 'line',
              label: 'Patient Satisfaction (1-5)',
              data: satisfaction,
              borderColor: '#f59e0b',
              backgroundColor: '#f59e0b',
              borderWidth: 2,
              tension: 0.3,
              yAxisID: 'y1'
            }
          ]
        },
        options: {
          ...this.defaultOptions,
          scales: {
            x: { grid: { color: 'rgba(255, 255, 255, 0.05)' } },
            y: {
              type: 'linear',
              position: 'left',
              title: { display: true, text: 'Days', color: '#64748b' },
              grid: { color: 'rgba(255, 255, 255, 0.05)' }
            },
            y1: {
              type: 'linear',
              position: 'right',
              min: 3,
              max: 5,
              title: { display: true, text: 'Score', color: '#f59e0b' },
              grid: { drawOnChartArea: false }
            }
          }
        }
      });
    } catch (err) {
      console.error("Outcomes chart error:", err);
    }
  },

  async initReadmissionDonut(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    try {
      const res = await fetch('/api/analytics');
      const data = await res.json();

      const labels = data.los_distribution.map(d => d.los_bucket);
      const counts = data.los_distribution.map(d => d.count);

      if (this.instances.readmit) this.instances.readmit.destroy();

      this.instances.readmit = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            data: counts,
            backgroundColor: [
              'rgba(16, 185, 129, 0.8)',
              'rgba(0, 240, 255, 0.8)',
              'rgba(245, 158, 11, 0.8)',
              'rgba(244, 63, 94, 0.8)'
            ],
            borderColor: '#060911',
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: { color: '#94a3b8', font: { family: "'Inter', sans-serif", size: 10 } }
            }
          }
        }
      });
    } catch (err) {
      console.error("Readmission donut error:", err);
    }
  }
};
