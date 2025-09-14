// script.js

// Example: show a loading spinner when logging in
document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  if (form) {
    form.addEventListener("submit", () => {
      const btn = form.querySelector("button[type='submit']");
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Logging in...";
      }
    });
  }
});
