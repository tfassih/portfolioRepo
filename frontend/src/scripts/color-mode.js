export function initColorMode() {
  const root = document.documentElement;
  const toggle = document.querySelector("#theme-toggle");
  const system = matchMedia("(prefers-color-scheme:dark)");
  const valid = value => ["light", "dark"].includes(value) ? value : null;
  let preference = null;
  try {
    preference = valid(localStorage.getItem("theme"));
  } catch (_) {}

  const apply = () => {
    const mode = preference || (system.matches ? "dark" : "light");
    root.dataset.theme = mode;
    toggle.setAttribute("aria-checked", String(mode === "dark"));
    toggle.title = mode === "dark" ? "Switch to light mode" : "Switch to dark mode";
    document.dispatchEvent(new Event("colormodechange"));
  };
  apply();
  toggle.hidden = false;
  toggle.addEventListener("click", () => {
    preference = root.dataset.theme === "dark" ? "light" : "dark";
    try {
      localStorage.setItem("theme", preference);
    } catch (_) {}
    apply();
  });
  system.addEventListener("change", () => {
    if (!preference) apply();
  });
  window.addEventListener("storage", event => {
    if (event.key === "theme" || event.key === null) {
      preference = valid(event.newValue);
      apply();
    }
  });
}
