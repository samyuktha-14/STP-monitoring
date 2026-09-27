/**
 * Smart STP Monitor — Frontend Controller
 * Communicates with backend Python engine and dynamically updates UI cards, WQI gauge, and checklists.
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const sliderPh = document.getElementById('slider-ph');
  const sliderTurbidity = document.getElementById('slider-turbidity');
  const sliderTds = document.getElementById('slider-tds');
  const sliderTemp = document.getElementById('slider-temp');

  const valPh = document.getElementById('val-ph');
  const valTurbidity = document.getElementById('val-turbidity');
  const valTds = document.getElementById('val-tds');
  const valTemp = document.getElementById('val-temp');

  const btnScenarioList = document.querySelectorAll('.btn-scenario');
  const btnToggleView = document.getElementById('view-mode-toggle');
  const viewModeLabel = document.getElementById('view-mode-label');
  const mainViewport = document.getElementById('main-viewport');

  // Scenario Presets
  const SCENARIOS = {
    normal: { ph: 7.10, turbidity: 3.5, tds: 425, temp: 25.0 },
    clarifier: { ph: 7.05, turbidity: 7.8, tds: 440, temp: 25.0 },
    aeration: { ph: 6.45, turbidity: 5.5, tds: 510, temp: 25.0 },
    salinity: { ph: 7.20, turbidity: 3.6, tds: 780, temp: 25.0 },
    cpcb: { ph: 9.20, turbidity: 14.0, tds: 2250, temp: 26.0 }
  };

  // Toggle Mobile Frame vs Desktop Mode
  let isMobileMode = false;
  btnToggleView.addEventListener('click', () => {
    isMobileMode = !isMobileMode;
    if (isMobileMode) {
      mainViewport.classList.add('mobile-frame-mode');
      viewModeLabel.textContent = 'Full Dashboard Mode';
    } else {
      mainViewport.classList.remove('mobile-frame-mode');
      viewModeLabel.textContent = 'Mobile Frame Mode';
    }
  });

  // Slider change listeners
  [sliderPh, sliderTurbidity, sliderTds, sliderTemp].forEach(slider => {
    slider.addEventListener('input', () => {
      updateSliderDisplays();
      triggerBackendDiagnostic();
      // Remove active class from scenarios if user manually drags
      btnScenarioList.forEach(b => b.classList.remove('active'));
    });
  });

  function updateSliderDisplays() {
    valPh.textContent = parseFloat(sliderPh.value).toFixed(2);
    valTurbidity.textContent = parseFloat(sliderTurbidity.value).toFixed(1) + ' NTU';
    valTds.textContent = parseInt(sliderTds.value) + ' mg/L';
    valTemp.textContent = parseFloat(sliderTemp.value).toFixed(1) + ' °C';
  }

  // Scenario Button Click Handler
  btnScenarioList.forEach(btn => {
    btn.addEventListener('click', () => {
      btnScenarioList.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const scKey = btn.getAttribute('data-scenario');
      const sc = SCENARIOS[scKey];
      if (sc) {
        sliderPh.value = sc.ph;
        sliderTurbidity.value = sc.turbidity;
        sliderTds.value = sc.tds;
        sliderTemp.value = sc.temp;
        updateSliderDisplays();
        triggerBackendDiagnostic();
      }
    });
  });

  // Fetch Full Advisory from Backend Python API
  let debounceTimeout = null;
  function triggerBackendDiagnostic() {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      fetchAdvisory();
    }, 120);
  }

  async function fetchAdvisory() {
    const payload = {
      ph: parseFloat(sliderPh.value),
      turbidity: parseFloat(sliderTurbidity.value),
      tds: parseFloat(sliderTds.value),
      temp: parseFloat(sliderTemp.value)
    };

    try {
      const response = await fetch('/api/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error('Backend response error');
      }

      const data = await response.json();
      renderDashboard(data);
    } catch (err) {
      console.warn('API error, using local fallback math:', err);
      // Local fallback in case server disconnected
      renderFallback(payload);
    }
  }

  function renderDashboard(data) {
    const health = data.plant_health_summary;
    const est = data.live_and_estimated_parameters;
    const bannerCard = document.getElementById('plant-status-banner');
    const bannerHeadline = document.getElementById('banner-headline');
    const bannerDiag = document.getElementById('banner-diagnosis');
    const bannerBadge = document.getElementById('banner-status-badge');

    // 1. Update Status Banner
    bannerHeadline.textContent = health.headline.replace(/\[.*?\]\s*/, '');
    bannerDiag.textContent = data.root_cause_diagnosis;
    bannerBadge.textContent = health.operational_status.replace(/_/g, ' ');

    bannerCard.className = 'banner-card';
    if (health.operational_status.includes('CRITICAL')) {
      bannerCard.classList.add('critical-mode');
    } else if (health.operational_status.includes('ADJUSTMENT') || health.operational_status.includes('WARNING')) {
      bannerCard.classList.add('warning-mode');
    }

    // 2. Soft Sensor Cards
    document.getElementById('est-do').textContent = est.DO.toFixed(2);
    
    // Estimated TSS (Derived from Turbidity formula)
    const tssElem = document.getElementById('est-tss');
    const tssNoteElem = document.getElementById('est-tss-note');
    if (est.TSS !== null && est.TSS !== undefined && !isNaN(est.TSS)) {
      tssElem.textContent = typeof est.TSS === 'number' ? est.TSS.toFixed(1) : est.TSS;
      if (tssNoteElem) tssNoteElem.textContent = 'Estimated from turbidity';
    } else {
      tssElem.textContent = 'Unavailable';
      if (tssNoteElem) tssNoteElem.textContent = 'Turbidity reading unavailable';
    }

    document.getElementById('est-bod').textContent = est.BOD.toFixed(1);
    document.getElementById('est-cod').textContent = est.COD.toFixed(1);

    const doSatPct = ((est.DO / 8.24) * 100).toFixed(1);
    document.getElementById('do-sat-pct').textContent = `${doSatPct}% Saturation`;

    // 3. WQI Gauge
    const wqiScore = health.wqi_score;
    const wqiGrade = health.wqi_grade;
    document.getElementById('wqi-score-val').textContent = wqiScore.toFixed(1);
    document.getElementById('wqi-grade-val').textContent = `GRADE ${wqiGrade}`;
    
    let wqiLabel = 'GOOD QUALITY';
    let gaugeColor = '#10B981';
    if (wqiScore >= 90) { wqiLabel = 'EXCELLENT'; gaugeColor = '#10B981'; }
    else if (wqiScore >= 75) { wqiLabel = 'GOOD QUALITY'; gaugeColor = '#3B82F6'; }
    else if (wqiScore >= 50) { wqiLabel = 'MODERATE'; gaugeColor = '#F59E0B'; }
    else { wqiLabel = 'POOR QUALITY'; gaugeColor = '#EF4444'; }
    
    document.getElementById('wqi-cat-val').textContent = wqiLabel;
    document.getElementById('wqi-gauge-circle').style.background = 
      `conic-gradient(${gaugeColor} 0% ${wqiScore}%, rgba(255, 255, 255, 0.08) ${wqiScore}% 100%)`;

    // 4. Reuse Matrix
    renderReuseMatrix(data);

    // 5. Trend Cards
    renderTrends(data.trend_analysis);

    // 6. Action Checklist
    renderChecklist(data.prioritized_action_checklist, data.affected_equipment_units);
  }

  function renderReuseMatrix(data) {
    const container = document.getElementById('reuse-matrix-container');
    const summaryText = document.getElementById('reuse-summary-text');
    summaryText.textContent = data.reuse_recommendation;

    // Standard purposes check
    const ph = data.live_and_estimated_parameters.pH;
    const turb = data.live_and_estimated_parameters.Turbidity;
    const doVal = data.live_and_estimated_parameters.DO;
    const tds = data.live_and_estimated_parameters.TDS;

    const purposes = [
      { name: 'Landscape Gardening', suitable: (ph >= 6.5 && ph <= 8.5 && turb <= 5.0 && tds <= 1500) },
      { name: 'Construction & Dust Suppression', suitable: (ph >= 6.0 && ph <= 9.0 && turb <= 15.0) },
      { name: 'Toilet Flushing (Dual Plumbing)', suitable: (ph >= 6.5 && ph <= 8.5 && turb <= 2.0 && doVal >= 2.0) },
      { name: 'HVAC Cooling Tower Makeup', suitable: (ph >= 7.0 && ph <= 8.2 && turb <= 2.0 && tds <= 800) }
    ];

    container.innerHTML = purposes.map(p => `
      <div class="reuse-pill">
        <span>${p.name}</span>
        <span class="reuse-status-tag ${p.suitable ? 'status-suitable' : 'status-unsuitable'}">
          ${p.suitable ? 'SUITABLE' : 'UNSUITABLE'}
        </span>
      </div>
    `).join('');
  }

  function renderTrends(trendData) {
    const container = document.getElementById('trend-cards-container');
    const trends = trendData.parameter_trends || {};
    
    const params = [
      { name: 'Turbidity', key: 'Turbidity', unit: 'NTU' },
      { name: 'Dissolved Oxygen', key: 'DO', unit: 'mg/L' },
      { name: 'pH Balance', key: 'pH', unit: 'pH' },
      { name: 'Total Dissolved Solids', key: 'TDS', unit: 'mg/L' }
    ];

    container.innerHTML = params.map(p => {
      const t = trends[p.key] || {
        direction: 'STABLE',
        trend_icon: '[STEADY]',
        slope_per_day: 0.0,
        projected_3day_value: 0.0
      };

      let dirClass = 'trend-dir-stable';
      if (t.direction === 'IMPROVING') dirClass = 'trend-dir-improving';
      if (t.direction === 'DEGRADING') dirClass = 'trend-dir-degrading';

      return `
        <div class="trend-card">
          <div class="trend-card-title">
            <span>${p.name}</span>
            <span class="trend-dir-badge ${dirClass}">${t.direction}</span>
          </div>
          <div class="trend-rate">
            ${t.slope_per_day >= 0 ? '+' : ''}${t.slope_per_day.toFixed(2)} <span style="font-size:0.7rem; color:#9CA3AF">${p.unit}/day</span>
          </div>
          <div class="trend-projection">
            3-Day Proj: <strong>${t.projected_3day_value.toFixed(1)} ${p.unit}</strong>
          </div>
        </div>
      `;
    }).join('');
  }

  function renderChecklist(checklist, equipmentList) {
    const equipElem = document.getElementById('affected-equipment-tags');
    equipElem.textContent = equipmentList ? equipmentList.join(' · ') : 'All Standard Units';

    const container = document.getElementById('action-checklist-box');
    const p1 = checklist.priority_1_immediate || [];
    const p2 = checklist.priority_2_short_term || [];
    const p3 = checklist.priority_3_routine_maintenance || [];

    let html = '';

    // Priority 1
    p1.forEach(act => {
      html += `
        <div class="action-item p1-item">
          <span class="action-priority-badge badge-p1">P1 IMMEDIATE</span>
          <div class="action-details">
            <div class="action-title">${act.action}</div>
            <div class="action-text">${act.detail}</div>
            <div class="action-meta">
              <span><strong>Unit:</strong> ${act.equipment}</span>
              <span><strong>Target:</strong> ${act.target}</span>
            </div>
          </div>
        </div>
      `;
    });

    // Priority 2
    p2.forEach(act => {
      html += `
        <div class="action-item p2-item">
          <span class="action-priority-badge badge-p2">P2 PROCESS</span>
          <div class="action-details">
            <div class="action-title">${act.action}</div>
            <div class="action-text">${act.detail}</div>
            <div class="action-meta">
              <span><strong>Unit:</strong> ${act.equipment}</span>
              <span><strong>Target:</strong> ${act.target}</span>
            </div>
          </div>
        </div>
      `;
    });

    // Priority 3 (Show top 1 routine check)
    if (p3.length > 0) {
      const act = p3[0];
      html += `
        <div class="action-item p3-item">
          <span class="action-priority-badge badge-p3">P3 ROUTINE</span>
          <div class="action-details">
            <div class="action-title">${act.action}</div>
            <div class="action-text">${act.detail}</div>
            <div class="action-meta">
              <span><strong>Target:</strong> ${act.target}</span>
            </div>
          </div>
        </div>
      `;
    }

    container.innerHTML = html;
  }

  function renderFallback(p) {
    // Basic local fallback calculation if offline
    const doVal = Math.max(0.2, (8.24 * 0.3375 * (1.0 - 0.042 * (p.turbidity / 10.0))));
    const tssVal = 1.15 * p.turbidity + 5.22;
    const bodVal = 0.52 * tssVal + 0.85 * (8.24 - doVal) + 3.5;
    const codVal = 4.07 * bodVal;
    
    document.getElementById('est-do').textContent = doVal.toFixed(2);
    document.getElementById('est-tss').textContent = tssVal.toFixed(1);
    document.getElementById('est-bod').textContent = bodVal.toFixed(1);
    document.getElementById('est-cod').textContent = codVal.toFixed(1);
  }

  // Initial Load
  updateSliderDisplays();
  triggerBackendDiagnostic();
});
