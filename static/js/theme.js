// Detect system preference first
function getSystemTheme() {
  if (window.matchMedia("(prefers-color-scheme: dark)").matches) return "dark";
  return "light";
}

function applyTheme(theme) {
  document.body.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);
}

// Load saved theme or fallback to system
function loadTheme() {
  const saved = localStorage.getItem("theme");
  if (saved) {
    applyTheme(saved);
  } else {
    applyTheme(getSystemTheme());
  }
}

// Toggle between themes
function toggleTheme() {
  const current = document.body.getAttribute("data-theme");
  let next;
  if (current === "light") next = "dark";
  else if (current === "dark") next = "gradient";
  else next = "light"; // cycle back
  applyTheme(next);
}

// On page load
document.addEventListener("DOMContentLoaded", () => {
  loadTheme();
  document.getElementById("theme-toggle").addEventListener("click", toggleTheme);
});
