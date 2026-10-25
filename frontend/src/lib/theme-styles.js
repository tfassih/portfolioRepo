const tokens = ["paper", "ink", "muted", "rule", "panel", "accent"];

export function themeStyles(config) {
  if (!Array.isArray(config?.themes)) return "";
  return config.themes.map(theme => {
    // Only identifiers and literal colors can enter this inline stylesheet.
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(theme.id) ||
      !["light", "dark"].every(mode => tokens.every(token =>
        /^#[0-9a-f]{6}$/i.test(theme[mode]?.[token])))) return "";
    const colors = mode => tokens.map(token => `--${token}:${theme[mode][token]};`).join("");
    const selector = `:root[data-palette="${theme.id}"]`;
    return `${selector}{${colors("light")}}` +
      `${selector}[data-theme="dark"]{${colors("dark")}}` +
      `@media(prefers-color-scheme:dark){${selector}:not([data-theme]){${colors("dark")}}}`;
  }).join("\n");
}
