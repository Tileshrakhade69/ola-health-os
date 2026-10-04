/**
 * OLA Health OS - Digital Twin Bed Matrix & AI Optimizer
 * Interactive 3D/Matrix representation of hospital ward beds and automated allocation.
 */

const DigitalTwinManager = {
  allBeds: [],
  currentWardFilter: 'All',
  currentStatusFilter: 'All',

  async init() {
    await this.fetchBeds();
    this.setupListeners();
  },

  async fetchBeds() {
    try {
      const res = await fetch('/api/beds');
      const data = await res.json();
      this.allBeds = data.beds || [];
      this.renderBedGrid();
    } catch (err) {
      console.error("Failed to load beds:", err);
    }
  },

  setupListeners() {
    // Ward filters
    document.querySelectorAll('.ward-filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.ward-filter-btn').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        this.currentWardFilter = e.currentTarget.dataset.ward;
        this.renderBedGrid();
      });
    });

    // Run Optimizer Button
    const optBtn = document.getElementById('run-ai-optimizer-btn');
    if (optBtn) {
      optBtn.addEventListener('click', () => this.runBedOptimization());
    }
  },

  renderBedGrid() {
    const grid = document.getElementById('digital-twin-grid');
    if (!grid) return;

    let filtered = this.allBeds;
    if (this.currentWardFilter !== 'All') {
      filtered = filtered.filter(b => b.department === this.currentWardFilter);
    }

    grid.innerHTML = filtered.map(bed => {
      const statusClass = bed.status.toLowerCase();
      return `
        <div class="bed-tile ${statusClass}" onclick="DigitalTwinManager.inspectBed('${bed.bed_id}')">
          <div class="bed-tile-id">${bed.bed_id}</div>
          <span class="bed-tile-status">${bed.status}</span>
          <div style="font-size:0.7rem; color:#94a3b8; margin-bottom:0.25rem;">${bed.room_number}</div>
          <div class="bed-badges">
            <i class="fa-solid fa-heart-pulse ${bed.has_telemetry ? 'active-feature' : ''}" title="IoT Telemetry"></i>
            <i class="fa-solid fa-lungs ${bed.has_ventilator_support ? 'active-feature' : ''}" title="Ventilator Ready"></i>
          </div>
        </div>
      `;
    }).join('');
  },

  inspectBed(bedId) {
    const bed = this.allBeds.find(b => b.bed_id === bedId);
    if (!bed) return;

    const modal = document.getElementById('bed-inspect-modal');
    const content = document.getElementById('bed-inspect-details');
    if (!modal || !content) return;

    content.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.25rem;">
        <h3 style="font-family:'Outfit', sans-serif; color:#00f0ff; font-size:1.4rem;">${bed.bed_id}</h3>
        <span class="bed-tile-status" style="font-size:0.85rem; padding:4px 10px;">${bed.status}</span>
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; font-size:0.85rem; margin-bottom:1.5rem;">
        <div><span style="color:#64748b;">Department:</span> <strong style="color:#fff;">${bed.department}</strong></div>
        <div><span style="color:#64748b;">Room:</span> <strong style="color:#fff;">${bed.room_number}</strong></div>
        <div><span style="color:#64748b;">Ward / Location:</span> <strong style="color:#fff;">${bed.ward_name}</strong></div>
        <div><span style="color:#64748b;">Type:</span> <strong style="color:#fff;">${bed.bed_type}</strong></div>
        <div><span style="color:#64748b;">Turnaround Time:</span> <strong style="color:#38bdf8;">${bed.turnaround_time_mins} mins</strong></div>
        <div><span style="color:#64748b;">IoT Telemetry Link:</span> <strong style="color:${bed.has_telemetry ? '#10b981' : '#64748b'};">${bed.has_telemetry ? 'ACTIVE (Online)' : 'None'}</strong></div>
        <div><span style="color:#64748b;">Ventilator Hookup:</span> <strong style="color:${bed.has_ventilator_support ? '#00f0ff' : '#64748b'};">${bed.has_ventilator_support ? 'Equipped' : 'No'}</strong></div>
      </div>
      <div style="display:flex; gap:0.75rem;">
        <button class="btn-scenario" style="flex:1;" onclick="DigitalTwinManager.closeModal()">Close Details</button>
      </div>
    `;

    modal.classList.add('active');
  },

  closeModal() {
    const modal = document.getElementById('bed-inspect-modal');
    if (modal) modal.classList.remove('active');
  },

  async runBedOptimization() {
    const btn = document.getElementById('run-ai-optimizer-btn');
    if (btn) {
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Calculating Quantum Allocation...`;
      btn.disabled = true;
    }

    try {
      const res = await fetch('/api/optimize/allocate-beds', { method: 'POST' });
      const data = await res.json();

      const resultsContainer = document.getElementById('optimizer-results-container');
      const assignmentsList = document.getElementById('optimizer-assignments-list');
      const rebalanceList = document.getElementById('rebalancing-actions-list');

      if (resultsContainer) resultsContainer.style.display = 'block';

      // Summary KPIs
      const savingsEl = document.getElementById('opt-wait-savings-val');
      const countEl = document.getElementById('opt-assigned-count-val');
      if (savingsEl) savingsEl.textContent = `${data.optimization.total_wait_time_saved_mins} mins`;
      if (countEl) countEl.textContent = `${data.optimization.total_optimized} Patients Matched`;

      // Render assignments
      if (assignmentsList && data.optimization.assignments) {
        assignmentsList.innerHTML = data.optimization.assignments.map(a => `
          <div class="glass-panel" style="padding:1rem; margin-bottom:0.85rem; border-color:rgba(0, 240, 255, 0.3);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
              <div>
                <strong style="color:#00f0ff; font-family:'JetBrains Mono', monospace;">${a.patient_id}</strong>
                <span style="font-size:0.78rem; color:#94a3b8; margin-left:0.5rem;">${a.diagnosis}</span>
              </div>
              <span class="live-badge" style="color:#10b981;">Confidence: ${a.match_confidence}%</span>
            </div>
            <div style="display:flex; align-items:center; justify-content:space-between; font-size:0.82rem;">
              <div>
                <span style="color:#64748b;">Assigned Bed:</span> 
                <strong style="color:#fff; font-family:'JetBrains Mono';">${a.assigned_bed_id}</strong> 
                <span style="color:#38bdf8;">(${a.target_ward} - ${a.room_number})</span>
              </div>
              <div style="color:#10b981; font-weight:600;">
                <i class="fa-solid fa-clock"></i> Saves ${a.estimated_wait_savings_mins} mins wait time
              </div>
            </div>
          </div>
        `).join('');
      }

      // Render surge rebalancing actions
      if (rebalanceList && data.rebalancing_actions) {
        rebalanceList.innerHTML = data.rebalancing_actions.map(r => `
          <div class="rebalance-card">
            <div class="rebalance-meta">
              <span class="rebalance-badge ${r.priority.toLowerCase()}">${r.priority}</span>
              <div>
                <strong style="color:#fff; font-size:0.88rem;">${r.action}</strong>
                <div style="font-size:0.76rem; color:#94a3b8;">${r.source} &rarr; ${r.target}</div>
              </div>
            </div>
            <div style="text-align:right;">
              <span style="font-size:0.78rem; color:#00f0ff; font-weight:500;">${r.impact}</span>
              <div style="font-size:0.7rem; color:#64748b;">Confidence: ${r.confidence}</div>
            </div>
          </div>
        `).join('');
      }

      // Smooth scroll to results
      resultsContainer.scrollIntoView({ behavior: 'smooth' });

    } catch (err) {
      console.error("Optimization error:", err);
    } finally {
      if (btn) {
        btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Run AI Bed Allocation Optimizer`;
        btn.disabled = false;
      }
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  DigitalTwinManager.init();
});
