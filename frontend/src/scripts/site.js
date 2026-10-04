export {};
const root = document.documentElement;
const reduced = matchMedia("(prefers-reduced-motion:reduce)");
const theme = document.querySelector("#theme-toggle");
const motion = document.querySelector("#motion-toggle");
const tilt = document.querySelector("#tilt-toggle");
const status = document.querySelector("#motion-status");
const store = (key, value) => {
  try {
    localStorage.setItem(key, value);
  } catch (_) {}
};
const enabled = () => !reduced.matches && root.dataset.motion !== "off";
function labels() {
  theme.textContent = root.dataset.theme === "dark" ? "Light mode" : "Dark mode";
  motion.textContent = enabled() ? "Motion on" : "Motion off";
  motion.setAttribute("aria-pressed", String(enabled()));
}
labels();
reduced.addEventListener("change", labels);
theme.addEventListener("click", () => {
  root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
  store("theme", root.dataset.theme);
  labels();
});
motion.addEventListener("click", () => {
  root.dataset.motion = enabled() ? "off" : "on";
  store("motion", root.dataset.motion);
  labels();
  document.dispatchEvent(new Event("motionchange"));
  if (!enabled()) {
    root.style.setProperty("--mx", "0");
    root.style.setProperty("--my", "0");
  }
});
let frame = 0;
const move = (x, y) => {
  if (!enabled() || document.hidden) return;
  cancelAnimationFrame(frame);
  frame = requestAnimationFrame(() => {
    root.style.setProperty("--mx", String(Math.max(-1, Math.min(1, x))));
    root.style.setProperty("--my", String(Math.max(-1, Math.min(1, y))));
  });
};
document.addEventListener(
  "pointermove",
  (event) => {
    if (event.pointerType !== "mouse") return;
    move((event.clientX / innerWidth) * 2 - 1, (event.clientY / innerHeight) * 2 - 1);
  },
  { passive: true },
);
let tiltOn = false;
const orientation = (event) =>
  move((event.gamma || 0) / 25, ((event.beta || 0) - 45) / 25);
tilt.addEventListener("click", async () => {
  if (tiltOn) {
    window.removeEventListener("deviceorientation", orientation);
    tiltOn = false;
    tilt.textContent = "Enable tilt";
    move(0, 0);
    return;
  }
  if (!window.DeviceOrientationEvent || !enabled()) {
    status.textContent = "Tilt is unavailable or reduced motion is enabled.";
    return;
  }
  try {
    const API = window.DeviceOrientationEvent;
    if (
      typeof API.requestPermission === "function" &&
      (await API.requestPermission()) !== "granted"
    )
      throw new Error();
    window.addEventListener("deviceorientation", orientation, { passive: true });
    tiltOn = true;
    tilt.textContent = "Disable tilt";
  } catch (_) {
    status.textContent = "Tilt permission was not granted.";
  }
});
if ("IntersectionObserver" in window && enabled()) {
  const observer = new IntersectionObserver(
    (entries) =>
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.removeAttribute("data-pending");
          observer.unobserve(entry.target);
        }
      }),
    { threshold: 0.08 },
  );
  document.querySelectorAll(".reveal").forEach((el) => {
    if (el.getBoundingClientRect().top > innerHeight)
      el.setAttribute("data-pending", "");
    observer.observe(el);
  });
}
const loader = document.querySelector("#page-loader");
let timer, failSafe;
const resetLoader = () => {
  clearTimeout(timer);
  clearTimeout(failSafe);
  loader.hidden = true;
};
document.addEventListener("click", (event) => {
  const link = event.target.closest("a[href]");
  if (
    !link ||
    event.button !== 0 ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    link.hasAttribute("download") ||
    link.target === "_blank"
  )
    return;
  const url = new URL(link.href);
  if (
    url.origin !== location.origin ||
    (url.pathname === location.pathname && url.hash)
  )
    return;
  timer = setTimeout(() => {
    loader.hidden = false;
  }, 150);
  failSafe = setTimeout(resetLoader, 10000);
});
window.addEventListener("pageshow", resetLoader);
if (
  !navigator.doNotTrack?.includes("1") &&
  !navigator.globalPrivacyControl &&
  !location.pathname.startsWith("/subscribe/")
) {
  const body = JSON.stringify({
    event_id: crypto.randomUUID(),
    path: location.pathname,
    referrer: document.referrer,
  });
  navigator.sendBeacon("/api/track/", new Blob([body], { type: "application/json" }));
}