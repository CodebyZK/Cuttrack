// ── Date display ─────────────────────────────────────────────
(function() {
  const now = new Date();
  const dateEl = document.getElementById('display-date');
  const dayEl = document.getElementById('display-day');
  if (dateEl) dateEl.textContent = now.toLocaleDateString('en-CA', { month: 'short', day: 'numeric', year: 'numeric' });
  if (dayEl) dayEl.textContent = now.toLocaleDateString('en-CA', { weekday: 'long' });
})();

// ── Tabs ──────────────────────────────────────────────────────
function switchTab(tab) {
  ['food', 'workout', 'sleep', 'weight'].forEach(t => {
    const el = document.getElementById('form-' + t);
    if (el) el.style.display = t === tab ? 'grid' : 'none';
  });
  document.querySelectorAll('.tab').forEach((el, i) => {
    el.classList.toggle('active', ['food', 'workout', 'sleep', 'weight'][i] === tab);
  });
}

// ── API helper ────────────────────────────────────────────────
async function api(method, path, body) {
  const res = await fetch(path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  });
  return res.json();
}

// ── Log food ──────────────────────────────────────────────────
async function logFood() {
  const name = document.getElementById('food-name').value.trim();
  const cals = parseInt(document.getElementById('food-cals').value) || 0;
  const prot = parseInt(document.getElementById('food-protein').value) || 0;
  if (!name) return;
  await api('POST', '/api/food', { name, calories: cals, protein: prot });
  location.reload();
}

// ── Log workout ───────────────────────────────────────────────
async function logWorkout() {
  const exercise = document.getElementById('workout-ex').value;
  const sets = parseInt(document.getElementById('workout-sets').value) || 0;
  const reps = parseInt(document.getElementById('workout-reps').value) || 0;
  await api('POST', '/api/workout', { exercise, sets, reps });
  location.reload();
}

// ── Log sleep ─────────────────────────────────────────────────
async function logSleep() {
  const bedtime = document.getElementById('sleep-bed').value;
  const waketime = document.getElementById('sleep-wake').value;
  if (!bedtime || !waketime) return;
  await api('POST', '/api/sleep', { bedtime, waketime });
  location.reload();
}

// ── Log weight ────────────────────────────────────────────────
async function logWeight() {
  const value = parseFloat(document.getElementById('weight-val').value);
  if (!value) return;
  await api('POST', '/api/weight', { value });
  location.reload();
}

// ── Delete helpers ────────────────────────────────────────────
async function deleteFood(id, btn) {
  await api('DELETE', '/api/food/' + id);
  btn.closest('tr').remove();
}

async function deleteWorkout(id, btn) {
  await api('DELETE', '/api/workout/' + id);
  btn.closest('tr').remove();
}

async function deleteSleep(id, btn) {
  await api('DELETE', '/api/sleep/' + id);
  btn.closest('tr').remove();
}

// ── Weight chart ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  const canvas = document.getElementById('weightChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  if (!weightData || weightData.length === 0) {
    ctx.fillStyle = getComputedStyle(document.documentElement)
      .getPropertyValue('--muted').trim() || '#6b7570';
    ctx.font = '14px DM Sans, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Log your weight to see the trend', canvas.offsetWidth / 2, 100);
    return;
  }

  const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  const labels = weightData.map(w => {
    const d = new Date(w.date + 'T00:00:00');
    return d.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' });
  });
  const values = weightData.map(w => w.value);
  const minVal = Math.max(130, Math.min(...values) - 3);
  const maxVal = Math.max(...values) + 3;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Weight',
          data: values,
          borderColor: isDark ? '#b8f566' : '#4a8f1f',
          backgroundColor: isDark ? 'rgba(184,245,102,0.07)' : 'rgba(74,143,31,0.07)',
          borderWidth: 2,
          pointBackgroundColor: isDark ? '#b8f566' : '#4a8f1f',
          pointRadius: 4,
          pointHoverRadius: 6,
          fill: true,
          tension: 0.35
        },
        {
          label: 'Goal (145 lbs)',
          data: Array(values.length).fill(145),
          borderColor: isDark ? '#5ff0a0' : '#0f7a4e',
          borderWidth: 1.5,
          borderDash: [6, 4],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: isDark ? '#1c1f1d' : '#ffffff',
          borderColor: isDark ? '#2a2e2c' : '#d8dcd6',
          borderWidth: 1,
          titleColor: isDark ? '#6b7570' : '#6b7570',
          bodyColor: isDark ? '#e8ede9' : '#1a1e1b',
          callbacks: { label: c => c.parsed.y + ' lbs' }
        }
      },
      scales: {
        x: {
          ticks: { color: '#6b7570', font: { family: 'DM Mono', size: 11 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 8 },
          grid: { color: isDark ? '#1e2220' : '#eef0ec' }
        },
        y: {
          ticks: { color: '#6b7570', font: { family: 'DM Mono', size: 11 }, callback: v => v + ' lbs' },
          grid: { color: isDark ? '#1e2220' : '#eef0ec' },
          min: minVal,
          max: maxVal
        }
      }
    }
  });
});

// ── Auto-refresh Apple Watch data every 5 minutes ─────────────
setInterval(async function() {
  try {
    const data = await api('GET', '/api/watch/today');
    if (data && data.active_calories !== undefined) {
      const activeEl = document.getElementById('watch-active');
      const restingEl = document.getElementById('watch-resting');
      const totalEl = document.getElementById('watch-total');
      const statActive = document.getElementById('stat-active');
      const statResting = document.getElementById('stat-resting');
      if (activeEl) activeEl.textContent = data.active_calories;
      if (restingEl) restingEl.textContent = data.resting_calories;
      if (totalEl) totalEl.textContent = data.active_calories + data.resting_calories;
      if (statActive) statActive.textContent = data.active_calories;
      if (statResting) statResting.textContent = data.resting_calories;
    }
  } catch(e) {}
}, 5 * 60 * 1000);

// ── Enter key submits active form ─────────────────────────────
document.addEventListener('keydown', function(e) {
  if (e.key !== 'Enter') return;
  const active = document.querySelector('.tab.active');
  if (!active) return;
  const tab = active.textContent.trim().toLowerCase();
  const fns = { food: logFood, workout: logWorkout, sleep: logSleep, weight: logWeight };
  if (fns[tab]) fns[tab]();
});
