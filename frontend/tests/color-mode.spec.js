import { test, expect } from "@playwright/test";

for (const mode of ["light", "dark"]) {
  test(`uses the system ${mode} mode with an icon-only footer switch`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: mode });
    await page.goto("/");
    const toggle = page.getByRole("switch", { name: "Dark mode" });
    await expect(page.locator("html")).toHaveAttribute("data-theme", mode);
    await expect(page.locator("footer #theme-toggle")).toBeVisible();
    await expect(page.locator("header #theme-toggle")).toHaveCount(0);
    await expect(toggle).toHaveText("");
    await expect(toggle).toHaveAttribute("aria-checked", String(mode === "dark"));
    await expect(toggle.locator(mode === "dark" ? ".mode-to-light" : ".mode-to-dark")).toBeVisible();
    const box = await toggle.boundingBox();
    expect(box.width).toBeGreaterThanOrEqual(44);
    expect(box.height).toBeGreaterThanOrEqual(44);
  });
}

test("follows system changes until a manual choice, then preserves it", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/");
  await page.emulateMedia({ colorScheme: "dark" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  const toggle = page.getByRole("switch", { name: "Dark mode" });
  await toggle.focus();
  await page.keyboard.press("Space");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.emulateMedia({ colorScheme: "light" });
  await page.emulateMedia({ colorScheme: "dark" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.goto("/art/photography/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.getByRole("switch", { name: "Dark mode" })).toHaveAttribute("aria-checked", "false");
});

test("supports existing saved choices and ignores invalid storage values", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await page.goto("/");
  await page.evaluate(() => localStorage.setItem("theme", "light"));
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.evaluate(() => localStorage.setItem("theme", "invalid"));
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});

test("system default and toggling still work when browser storage is unavailable", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await page.addInitScript(() => {
    for (const key of ["localStorage", "sessionStorage"]) {
      Object.defineProperty(window, key, { get() { throw new DOMException("Storage blocked", "SecurityError"); } });
    }
  });
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("switch", { name: "Dark mode" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.locator("#motion-toggle").click();
  await expect(page.locator("html")).toHaveAttribute("data-motion", "off");
  expect(errors).toEqual([]);
});

test("synchronizes mode across tabs and returns to system when preference is cleared", async ({ page, context }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/");
  const other = await context.newPage();
  await other.goto("/contact/");
  await other.evaluate(() => localStorage.setItem("theme", "dark"));
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await other.evaluate(() => localStorage.removeItem("theme"));
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await other.close();
});

test("without JavaScript the page follows system dark mode and hides the inactive switch", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, colorScheme: "dark" });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4322/");
  await expect(page.locator("body")).toHaveCSS("background-color", "rgb(33, 31, 28)");
  await expect(page.locator("#theme-toggle")).toBeHidden();
  await context.close();
});
