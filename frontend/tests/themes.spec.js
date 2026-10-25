import { test, expect } from "@playwright/test";

test("all preloaded themes work in both modes without network requests", async ({ page }, testInfo) => {
  await page.goto("/");
  const select = page.getByRole("combobox", { name: "Theme", exact: true });
  await expect(select).toBeVisible();
  const config = await page.locator("#theme-config").textContent().then(JSON.parse);
  await page.waitForLoadState("networkidle");
  const requests = [];
  page.on("request", request => requests.push(request.url()));
  for (const theme of config.themes) {
    await select.selectOption(theme.id);
    for (const mode of ["light", "dark"]) {
      if (await page.locator("html").getAttribute("data-theme") !== mode) {
        await page.getByRole("switch", { name: "Dark mode" }).click();
      }
      for (const [token, color] of Object.entries(theme[mode])) {
        await expect(page.locator("html")).toHaveCSS(`--${token}`, color);
      }
    }
  }
  expect(requests).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(await page.evaluate(() => innerWidth));
  await page.evaluate(() => scrollTo(0, 0));
  await page.screenshot({ path: testInfo.outputPath("themes.png"), fullPage: true, animations: "disabled" });
});

test("theme choice persists independently of color mode and navigation", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/");
  await page.getByRole("combobox", { name: "Theme", exact: true }).selectOption("ocean");
  await page.getByRole("switch", { name: "Dark mode" }).click();
  await page.goto("/art/photography/");
  await expect(page.locator("html")).toHaveAttribute("data-palette", "ocean");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("combobox", { name: "Theme", exact: true })).toHaveValue("ocean");
  await page.reload();
  await expect(page.locator("body")).toHaveCSS("background-color", "rgb(16, 35, 45)");
});

test("a removed or unknown saved theme falls back to the configured default", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("portfolio-theme", "removed-theme"));
  await page.goto("/");
  await expect(page.getByRole("combobox", { name: "Theme", exact: true })).toHaveValue("marginalia");
  await expect(page.locator("html")).toHaveAttribute("data-palette", "marginalia");
});

test("theme switching works with blocked storage", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", { get() { throw new DOMException("Blocked", "SecurityError"); } });
  });
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/");
  await page.getByRole("combobox", { name: "Theme", exact: true }).selectOption("forest");
  await expect(page.locator("html")).toHaveAttribute("data-palette", "forest");
  expect(errors).toEqual([]);
});

test("theme changes synchronize across tabs and clearing returns to the default", async ({ page, context }) => {
  await page.goto("/");
  await expect(page.getByRole("combobox", { name: "Theme", exact: true })).toBeVisible();
  const other = await context.newPage();
  await other.goto("/contact/");
  await other.getByRole("combobox", { name: "Theme", exact: true }).selectOption("forest");
  await expect(page.getByRole("combobox", { name: "Theme", exact: true })).toHaveValue("forest");
  await other.evaluate(() => localStorage.removeItem("portfolio-theme"));
  await expect(page.getByRole("combobox", { name: "Theme", exact: true })).toHaveValue("marginalia");
  await other.close();
});

test("saved appearance applies even before the footer controls script loads", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("portfolio-theme", "forest");
    localStorage.setItem("theme", "dark");
  });
  await page.route(url => url.pathname.endsWith("/src/scripts/site.js"), route => route.abort());
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-palette", "forest");
  await expect(page.locator("body")).toHaveCSS("background-color", "rgb(25, 37, 29)");
});

test("Studio imports and exports a custom theme that reaches the public site", async ({ page, browser }) => {
  const backend = "http://127.0.0.1:8001";
  const original = (await (await page.request.get(`${backend}/api/site/`)).json()).theme_config;
  const custom = structuredClone(original);
  custom.themes.push({ ...structuredClone(custom.themes[0]), id: "studio-custom", name: "Studio custom" });
  custom.themes.at(-1).light.paper = "#fff4dd";
  custom.default = "studio-custom";
  await page.goto(`${backend}/studio-admin/login/`);
  await page.getByLabel("Username", { exact: false }).fill("browser-editor");
  await page.getByLabel("Password", { exact: false }).fill("browser-tests-only");
  await page.getByRole("button", { name: "Log in" }).click();

  const upload = async config => {
    await page.goto(`${backend}/studio-admin/content/sitesettings/1/change/`);
    await page.getByLabel("Import themes JSON", { exact: false }).setInputFiles({
      name: "themes.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify(config)),
    });
    await page.getByRole("button", { name: "Save", exact: true }).click();
    await expect(page.locator(".success")).toContainText("changed successfully");
  };
  try {
    await upload(custom);
    const exported = await page.request.get(`${backend}/studio-admin/content/sitesettings/1/themes.json`);
    expect(await exported.json()).toEqual(custom);
    await page.emulateMedia({ colorScheme: "light" });
    await page.goto("/");
    await expect(page.getByRole("combobox", { name: "Theme", exact: true })).toHaveValue("studio-custom");
    await expect(page.locator("body")).toHaveCSS("background-color", "rgb(255, 244, 221)");
    const context = await browser.newContext({ javaScriptEnabled: false, colorScheme: "light" });
    try {
      const plain = await context.newPage();
      await plain.goto("http://127.0.0.1:4322/");
      await expect(plain.locator("body")).toHaveCSS("background-color", "rgb(255, 244, 221)");
    } finally {
      await context.close();
    }
  } finally {
    await upload(original);
  }
});
