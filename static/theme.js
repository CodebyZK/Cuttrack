(function () {
  const saved = localStorage.getItem("cuttrack_theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
})();

function updateThemeBtn() {
  const btn = document.getElementById("theme-toggle");
  if (!btn) return;
  btn.textContent = document.documentElement.getAttribute("data-theme") === "dark" ? "☀" : "☾";
}

function toggleTheme() {
  const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("cuttrack_theme", next);
  updateThemeBtn();
}

document.addEventListener("DOMContentLoaded", updateThemeBtn);
