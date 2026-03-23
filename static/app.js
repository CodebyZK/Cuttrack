async function api(method, path, body) {
  const response = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await response.text();
  let parsed = {};
  try { parsed = text ? JSON.parse(text) : {}; } catch (_) {}
  if (!response.ok || parsed.ok === false) throw new Error(parsed.error || "Request failed.");
  return parsed;
}

async function logFood() {
  const name = document.getElementById("food-name").value.trim();
  const calories = parseInt(document.getElementById("food-cals").value, 10) || 0;
  const protein = parseInt(document.getElementById("food-protein").value, 10) || 0;
  if (!name) return;
  await api("POST", "/api/food", { name, calories, protein });
  location.reload();
}

async function logWorkout() {
  const exercise = document.getElementById("workout-ex").value;
  const sets = parseInt(document.getElementById("workout-sets").value, 10) || 0;
  const reps = parseInt(document.getElementById("workout-reps").value, 10) || 0;
  await api("POST", "/api/workout", { exercise, sets, reps });
  location.reload();
}

async function logSleep() {
  const bedtime = document.getElementById("sleep-bed").value;
  const waketime = document.getElementById("sleep-wake").value;
  if (!bedtime || !waketime) return;
  await api("POST", "/api/sleep", { bedtime, waketime });
  location.reload();
}

async function logWeight() {
  const value = parseFloat(document.getElementById("weight-val").value);
  if (!value) return;
  await api("POST", "/api/weight", { value });
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

async function deleteWeight(id, btn) {
  await api("DELETE", "/api/weight/" + id);
  btn.closest("tr").remove();
}

async function lookupFood() {
  const name = document.getElementById("food-name").value.trim();
  if (!name) return;
  const btn = document.getElementById("lookup-btn");
  const hint = document.getElementById("lookup-hint");
  btn.textContent = "…";
  btn.disabled = true;
  try {
    const data = await api("POST", "/api/food/lookup", { name });
    document.getElementById("food-cals").value = data.calories;
    document.getElementById("food-protein").value = data.protein;
    if (hint) hint.textContent = `Estimated: ${data.calories} cal · ${data.protein}g protein`;
  } catch (e) {
    if (hint) hint.textContent = e.message;
  } finally {
    btn.textContent = "Estimate ✦";
    btn.disabled = false;
  }
}
