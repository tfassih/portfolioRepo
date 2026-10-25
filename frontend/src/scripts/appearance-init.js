// Runs in the document head before the first paint.
(() => {
  const root = document.documentElement;
  const read = (storage, key) => {
    try {
      return window[storage].getItem(key);
    } catch (_) {
      return null;
    }
  };
  const saved = read("localStorage", "theme");
  root.dataset.theme = ["light", "dark"].includes(saved)
    ? saved
    : matchMedia("(prefers-color-scheme:dark)").matches ? "dark" : "light";
  root.dataset.motion = read("localStorage", "motion") || "on";
  if (
    location.pathname === "/" &&
    !read("sessionStorage", "introduced") &&
    !matchMedia("(prefers-reduced-motion:reduce)").matches &&
    root.dataset.motion !== "off"
  ) {
    root.dataset.intro = "on";
    try {
      sessionStorage.setItem("introduced", "1");
    } catch (_) {}
  }
})();
