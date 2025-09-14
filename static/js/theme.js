// theme.js

function toggleTheme() {
  const body = document.body;
  body.classList.toggle("dark-mode");

  // save preference
  const isDark = body.classList.contains("dark-mode");
  localStorage.setItem("Facebook-theme", isDark ? "dark" : "light");
}

document.addEventListener("DOMContentLoaded", () => {
  // load saved preference
  const saved = localStorage.getItem("Facebook-theme");
  if (saved === "dark") {
    document.body.classList.add("dark-mode");
  }

  // add a toggle button listener if one exists
  const toggleBtn = document.getElementById("theme-toggle");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", toggleTheme);
  }
});
