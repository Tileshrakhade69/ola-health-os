/**
 * OLA Health OS - Real-time IoT Telemetry & ECG Waveform Engine
 * Renders high-frequency canvas ECG signal and streaming patient vitals.
 */

class TelemetryEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.x = 0;
    this.lastY = 45;
    this.heartRate = 76;
    this.spo2 = 98;
    this.phase = 0;
    this.running = true;

    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
    this.startVitalsFluctuation();
  }

  resize() {
    if (!this.canvas) return;
    this.canvas.width = this.canvas.parentElement.clientWidth;
    this.canvas.height = 90;
    this.ctx.fillStyle = '#040810';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
  }

  startVitalsFluctuation() {
    setInterval(() => {
      // Subtle realistic physiological jitter
      this.heartRate = Math.min(125, Math.max(58, this.heartRate + (Math.random() * 4 - 2)));
      const hrEl = document.getElementById('telemetry-hr-val');
      if (hrEl) hrEl.textContent = Math.round(this.heartRate);

      const spo2El = document.getElementById('telemetry-spo2-val');
      if (spo2El) {
        const spo2Val = Math.min(100, Math.max(93, this.spo2 + (Math.random() > 0.85 ? (Math.random() * 2 - 1) : 0)));
        spo2El.textContent = Math.round(spo2Val) + '%';
      }
    }, 2200);
  }

  animate() {
    if (!this.canvas || !this.running) return;

    const width = this.canvas.width;
    const height = this.canvas.height;
    const midY = height / 2;

    // Clear leading cursor slice
    this.ctx.fillStyle = '#040810';
    this.ctx.fillRect(this.x, 0, 14, height);

    // Compute synthetic P-Q-R-S-T wave
    let y = midY;
    const cyclePos = (this.phase % 100);

    if (cyclePos >= 15 && cyclePos < 25) {
      // P wave (atrial depolarization)
      y -= Math.sin((cyclePos - 15) / 10 * Math.PI) * 7;
    } else if (cyclePos >= 30 && cyclePos < 33) {
      // Q dip
      y += 5;
    } else if (cyclePos >= 33 && cyclePos < 38) {
      // R peak (ventricular depolarization)
      y -= 38;
    } else if (cyclePos >= 38 && cyclePos < 42) {
      // S dip
      y += 12;
    } else if (cyclePos >= 52 && cyclePos < 68) {
      // T wave (ventricular repolarization)
      y -= Math.sin((cyclePos - 52) / 16 * Math.PI) * 11;
    } else {
      // Baseline baseline micro-noise
      y += (Math.random() - 0.5) * 1.5;
    }

    // Draw phosphor glow line
    this.ctx.beginPath();
    this.ctx.moveTo(this.x - 2, this.lastY);
    this.ctx.lineTo(this.x, y);
    this.ctx.strokeStyle = '#10b981';
    this.ctx.lineWidth = 2;
    this.ctx.shadowBlur = 8;
    this.ctx.shadowColor = '#10b981';
    this.ctx.stroke();

    this.lastY = y;
    this.x += 2;
    this.phase += 1.4;

    if (this.x >= width) {
      this.x = 0;
    }

    requestAnimationFrame(this.animate);
  }
}

// Fetch and render IoT alerts table
async function refreshTelemetryFeed() {
  try {
    const res = await fetch('/api/telemetry');
    const data = await res.json();
    
    const tbody = document.getElementById('iot-alerts-tbody');
    if (!tbody) return;

    tbody.innerHTML = data.recent_alerts.map(alert => `
      <tr>
        <td style="font-family:'JetBrains Mono', monospace; font-size:0.75rem; color:#94a3b8;">${alert.timestamp.split(' ')[1]}</td>
        <td><strong style="color:#00f0ff;">${alert.patient_id}</strong></td>
        <td><span class="panel-badge">${alert.bed_id}</span></td>
        <td>${alert.metric_name} (<span style="color:#f8fafc; font-weight:600;">${alert.metric_value}</span>)</td>
        <td>
          <span class="rebalance-badge ${alert.threshold_status === 'CRITICAL' ? 'high' : 'medium'}">
            ${alert.threshold_status}
          </span>
        </td>
        <td style="font-size:0.78rem; color:#cbd5e1;">${alert.alert_message}</td>
      </tr>
    `).join('');

    // Update active stream cards
    const streamContainer = document.getElementById('active-streams-grid');
    if (streamContainer && data.active_telemetry_streams) {
      streamContainer.innerHTML = data.active_telemetry_streams.map(p => `
        <div class="glass-panel" style="padding:1rem;">
          <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
            <strong style="font-family:'JetBrains Mono', monospace; color:#00f0ff;">${p.patient}</strong>
            <span class="panel-badge">${p.room}</span>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; font-size:0.78rem;">
            <div><span style="color:#64748b;">Heart Rate:</span> <strong style="color:#10b981;">${p.hr} bpm</strong></div>
            <div><span style="color:#64748b;">SpO2:</span> <strong style="color:#38bdf8;">${p.spo2}%</strong></div>
            <div><span style="color:#64748b;">BP:</span> <strong style="color:#f8fafc;">${p.bp}</strong></div>
            <div><span style="color:#64748b;">NEWS2:</span> <strong style="color:${p.news2 >= 5 ? '#f43f5e' : '#f59e0b'};">${p.news2}</strong></div>
          </div>
        </div>
      `).join('');
    }

  } catch (err) {
    console.error("Telemetry fetch error:", err);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new TelemetryEngine('ecg-waveform-canvas');
  refreshTelemetryFeed();
  setInterval(refreshTelemetryFeed, 12000);
});
