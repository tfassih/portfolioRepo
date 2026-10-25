export function initThemes() {
  const selector = document.querySelector("#theme-select");
  if (!selector) return;
  const config = JSON.parse(document.querySelector("#theme-config").textContent);
  const root = document.documentElement;
  const apply = value => {
    const id = config.themes.some(theme => theme.id === value) ? value : config.default;
    root.dataset.palette = id;
    selector.value = id;
  };
  apply(root.dataset.palette);
  document.querySelector("#theme-picker").hidden = false;
  selector.addEventListener("change", () => {
    apply(selector.value);
    try {
      localStorage.setItem("portfolio-theme", root.dataset.palette);
    } catch (_) {}
  });
  window.addEventListener("storage", event => {
    if (event.key === "portfolio-theme" || event.key === null) apply(event.newValue);
  });
}
