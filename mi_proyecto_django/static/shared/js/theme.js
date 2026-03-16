(function () {
  var storageKey = "parkinghub-theme";
  var root = document.documentElement;

  function systemTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    var toggles = document.querySelectorAll("[data-theme-toggle]");
    toggles.forEach(function (toggle) {
      toggle.setAttribute("aria-pressed", String(theme === "dark"));
      toggle.dataset.theme = theme;
      var label = toggle.querySelector("[data-theme-label]");
      if (label) {
        label.textContent = theme === "dark" ? "Modo oscuro" : "Modo claro";
      }
      var icon = toggle.querySelector("[data-theme-icon]");
      if (icon) {
        icon.textContent = theme === "dark" ? "☾" : "☀";
      }
    });
  }

  function initialTheme() {
    var saved = window.localStorage.getItem(storageKey);
    if (saved === "light" || saved === "dark") {
      return saved;
    }
    return systemTheme();
  }

  document.addEventListener("DOMContentLoaded", function () {
    applyTheme(initialTheme());
    document.querySelectorAll("[data-theme-toggle]").forEach(function (toggle) {
      toggle.addEventListener("click", function () {
        var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
        window.localStorage.setItem(storageKey, next);
        applyTheme(next);
      });
    });
  });
})();
