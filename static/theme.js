(function () {
  const saved = localStorage.getItem("cuttrack_theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
})();

function updateThemeBtn() {
  const icon = document.getElementById("theme-icon");
  const label = document.getElementById("theme-label");
  if (!icon || !label) return;
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  icon.textContent = isDark ? "☀" : "☾";
  label.textContent = isDark ? "Light" : "Dark";
}

function toggleTheme() {
  const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("cuttrack_theme", next);
  updateThemeBtn();
}

document.addEventListener("DOMContentLoaded", updateThemeBtn);
