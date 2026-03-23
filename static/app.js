(function () {
  const now = new Date();
  const dateEl = document.getElementById("display-date");
  const dayEl = document.getElementById("display-day");

  if (dateEl) {
    dateEl.textContent = now.toLocaleDateString("en-CA", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  if (dayEl) {
    dayEl.textContent = now.toLocaleDateString("en-CA", { weekday: "long" });
  }
})();

function switchTab(tab) {
  ["food", "workout", "sleep", "weight"].forEach(function (name) {
    const section = document.getElementById("form-" + name);
    if (section) {
      section.style.display = name === tab ? "grid" : "none";
    }
  });

  const tabs = document.querySelectorAll(".tab");
  ["food", "workout", "sleep", "weight"].forEach(function (name, idx) {
    if (tabs[idx]) {
      tabs[idx].classList.toggle("active", name === tab);
    }
  });
}

async function api(method, path, body) {
  const response = await fetch(path, {
    method: method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await response.text();
  let parsed = {};

  try {
    parsed = text ? JSON.parse(text) : {};
  } catch (_err) {
    parsed = {};
  }

  if (!response.ok || parsed.ok === false) {
    const message = parsed.error || "Request failed.";
    throw new Error(message);
  }

  return parsed;
}

async function logFood() {
  const name = document.getElementById("food-name").value.trim();
  const calories = parseInt(document.getElementById("food-cals").value, 10) || 0;
  const protein = parseInt(document.getElementById("food-protein").value, 10) || 0;

  if (!name) {
    return;
  }

  await api("POST", "/api/food", { name: name, calories: calories, protein: protein });
  location.reload();
}

async function logWorkout() {
  const exercise = document.getElementById("workout-ex").value;
  const sets = parseInt(document.getElementById("workout-sets").value, 10) || 0;
  const reps = parseInt(document.getElementById("workout-reps").value, 10) || 0;

  await api("POST", "/api/workout", { exercise: exercise, sets: sets, reps: reps });
  location.reload();
}

async function logSleep() {
  const bedtime = document.getElementById("sleep-bed").value;
  const waketime = document.getElementById("sleep-wake").value;

  if (!bedtime || !waketime) {
    return;
  }

  await api("POST", "/api/sleep", { bedtime: bedtime, waketime: waketime });
  location.reload();
}

async function logWeight() {
  const value = parseFloat(document.getElementById("weight-val").value);
  if (!value) {
    return;
  }

  await api("POST", "/api/weight", { value: value });
  location.reload();
}

async function deleteFood(id, btn) {
  await api("DELETE", "/api/food/" + id);
  btn.closest("tr").remove();
}

async function deleteWorkout(id, btn) {
  await api("DELETE", "/api/workout/" + id);
  btn.closest("tr").remove();
}

async function deleteSleep(id, btn) {
  await api("DELETE", "/api/sleep/" + id);
  btn.closest("tr").remove();
}

document.addEventListener("DOMContentLoaded", function () {
  const canvas = document.getElementById("weightChart");
  if (!canvas) {
    return;
  }

  const ctx = canvas.getContext("2d");
  const data = Array.isArray(weightData) ? weightData : [];

  if (!data.length) {
    ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--muted").trim() || "#6b7570";
    ctx.font = "14px DM Sans, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Log your weight to see the trend", canvas.offsetWidth / 2, 100);
    return;
  }

  const isDark = document.documentElement.getAttribute("data-theme") !== "light";
  const labels = data.map(function (item) {
    const date = new Date(item.date + "T00:00:00");
    return date.toLocaleDateString("en-CA", { month: "short", day: "numeric" });
  });
  const values = data.map(function (item) {
    return item.value;
  });
  const minVal = Math.max(130, Math.min.apply(null, values) - 3);
  const maxVal = Math.max.apply(null, values) + 3;

  new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Weight",
          data: values,
          borderColor: isDark ? "#b8f566" : "#4a8f1f",
          backgroundColor: isDark ? "rgba(184,245,102,0.08)" : "rgba(74,143,31,0.08)",
          borderWidth: 2,
          pointBackgroundColor: isDark ? "#b8f566" : "#4a8f1f",
          pointRadius: 4,
          pointHoverRadius: 6,
          fill: true,
          tension: 0.35,
        },
        {
          label: "Goal (145 lbs)",
          data: Array(values.length).fill(145),
          borderColor: isDark ? "#5ff0a0" : "#0f7a4e",
          borderWidth: 1.5,
          borderDash: [6, 4],
          pointRadius: 0,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: isDark ? "#1c1f1d" : "#ffffff",
          borderColor: isDark ? "#2a2e2c" : "#d8dcd6",
          borderWidth: 1,
          titleColor: "#6b7570",
          bodyColor: isDark ? "#e8ede9" : "#1a1e1b",
          callbacks: {
            label: function (context) {
              return context.parsed.y + " lbs";
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: "#6b7570",
            font: { family: "DM Mono", size: 11 },
            maxRotation: 0,
            autoSkip: true,
            maxTicksLimit: 8,
          },
          grid: { color: isDark ? "#1e2220" : "#eef0ec" },
        },
        y: {
          ticks: {
            color: "#6b7570",
            font: { family: "DM Mono", size: 11 },
            callback: function (value) {
              return value + " lbs";
            },
          },
          grid: { color: isDark ? "#1e2220" : "#eef0ec" },
          min: minVal,
          max: maxVal,
        },
      },
    },
  });
});

setInterval(async function () {
  try {
    const data = await api("GET", "/api/watch/today");
    const active = data.active_calories || 0;
    const resting = data.resting_calories || 0;

    const activeEl = document.getElementById("watch-active");
    const restingEl = document.getElementById("watch-resting");
    const totalEl = document.getElementById("watch-total");
    const statActive = document.getElementById("stat-active");
    const statResting = document.getElementById("stat-resting");

    if (activeEl) activeEl.textContent = active;
    if (restingEl) restingEl.textContent = resting;
    if (totalEl) totalEl.textContent = active + resting;
    if (statActive) statActive.textContent = active;
    if (statResting) statResting.textContent = resting;
  } catch (_err) {
    // Polling is best-effort; no UI interruption on transient errors.
  }
}, 5 * 60 * 1000);

document.addEventListener("keydown", function (event) {
  if (event.key !== "Enter") {
    return;
  }

  const activeTab = document.querySelector(".tab.active");
  if (!activeTab) {
    return;
  }

  const tab = activeTab.textContent.trim().toLowerCase();
  const actions = {
    food: logFood,
    workout: logWorkout,
    sleep: logSleep,
    weight: logWeight,
  };

  if (actions[tab]) {
    actions[tab]();
  }
});
