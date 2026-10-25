export function disableContextMenu() {
  // Capture also covers gallery content added after the page has loaded.
  document.addEventListener("contextmenu", (event) => event.preventDefault(), {
    capture: true,
  });
}
