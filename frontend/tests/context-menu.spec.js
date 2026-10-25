import { test, expect } from "@playwright/test";

async function observeContextMenus(page) {
  await page.evaluate(() => {
    const events = [];
    document.documentElement.dataset.contextMenus = "[]";
    window.addEventListener("contextmenu", event => {
      events.push({ prevented: event.defaultPrevented, trusted: event.isTrusted });
      document.documentElement.dataset.contextMenus = JSON.stringify(events);
    });
  });
}

async function expectPrevented(page, count) {
  await expect.poll(() => page.evaluate(() => JSON.parse(document.documentElement.dataset.contextMenus))).toEqual(
    Array.from({ length: count }, () => ({ prevented: true, trusted: true })),
  );
}

test("right-click on text and links is suppressed without activating navigation", async ({ page }) => {
  await page.goto("/art/");
  await expect(page.getByRole("switch", { name: "Dark mode" })).toBeVisible();
  await observeContextMenus(page);
  await page.locator("h1").click({ button: "right" });
  const photography = page.locator("main").getByRole("link", { name: "Photography" });
  await photography.click({ button: "right" });
  await expectPrevented(page, 2);
  await expect(page).toHaveURL(/\/art\/$/);
  await expect(page.locator("#page-loader")).toBeHidden();
  await photography.click();
  await expect(page).toHaveURL(/\/art\/photography\/$/);
});

for (const [kind, title] of [["photography", "River light"], ["images", "Studio render"]]) {
  test(`${kind} suppresses right-click after hydration and in fullscreen`, async ({ page }) => {
    await page.goto(`/art/${kind}/`);
    const opener = page.getByRole("button", { name: `Open ${title} fullscreen` });
    await expect(opener).toBeVisible();
    await observeContextMenus(page);
    await opener.locator("img").click({ button: "right" });
    await expectPrevented(page, 1);
    await expect(page.getByRole("dialog")).toBeHidden();
    await opener.click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await dialog.locator("img").click({ button: "right" });
    await expectPrevented(page, 2);
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect(opener).toBeFocused();
    if (kind === "photography") {
      await page.getByRole("button", { name: "Next item" }).click();
      const next = page.getByRole("button", { name: "Open Evening street fullscreen" });
      await next.locator("img").click({ button: "right" });
      await expectPrevented(page, 3);
      await next.focus();
      await page.keyboard.press("Enter");
      await expect(dialog).toBeVisible();
      await page.getByRole("button", { name: "Close fullscreen image" }).click();
      await expect(next).toBeFocused();
    }
  });
}

test("video context menu is suppressed and playback remains available", async ({ page }) => {
  await page.goto("/art/videos/");
  const video = page.locator("video");
  await expect(video).toBeVisible();
  await observeContextMenus(page);
  await video.click({ button: "right", position: { x: 20, y: 20 } });
  await expectPrevented(page, 1);
  await expect(video).toHaveAttribute("controls", "");
  await video.evaluate(element => { element.muted = true; return element.play(); });
  await expect.poll(() => video.evaluate(element => element.currentTime)).toBeGreaterThan(0);
  await video.evaluate(element => { if (element instanceof HTMLVideoElement) element.pause(); });
});

test("search still accepts typing, selection, keyboard shortcuts and submission", async ({ page }) => {
  await page.goto("/search/");
  await expect(page.getByRole("switch", { name: "Dark mode" })).toBeVisible();
  const query = page.getByRole("searchbox");
  await query.fill("temporary query");
  await observeContextMenus(page);
  await query.click({ button: "right" });
  await expectPrevented(page, 1);
  await query.press("ControlOrMeta+A");
  await page.keyboard.type("Example");
  await expect(query).toHaveValue("Example");
  await query.press("Tab");
  await expect(page.getByRole("button", { name: "Search", exact: true })).toBeFocused();
  await page.keyboard.press("Enter");
  const result = page.getByRole("link", { name: "Example project", exact: true });
  await expect(result).toBeVisible();
  await result.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByText("Project details", { exact: true })).toBeVisible();
});

test("Studio keeps its native context menu", async ({ page }) => {
  await page.goto("http://127.0.0.1:8001/studio-admin/login/");
  await observeContextMenus(page);
  await page.getByLabel("Username", { exact: false }).click({ button: "right" });
  await expect.poll(() => page.evaluate(() => JSON.parse(document.documentElement.dataset.contextMenus))).toEqual([
    { prevented: false, trusted: true },
  ]);
});
