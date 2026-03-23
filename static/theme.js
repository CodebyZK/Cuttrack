(function () {
  const saved = localStorage.getItem("cuttrack_theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
})();

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("cuttrack_theme", next);

  const btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.textContent = next === "dark" ? "O" : "C";
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const btn = document.getElementById("theme-toggle");
  if (!btn) {
    return;
  }
  const theme = document.documentElement.getAttribute("data-theme");
  btn.textContent = theme === "dark" ? "O" : "C";
});
