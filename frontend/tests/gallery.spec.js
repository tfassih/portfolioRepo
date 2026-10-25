import { test, expect } from "@playwright/test";

test("art index links all three galleries and includes photography in sitemap", async ({ page, request }) => {
  await page.goto("/art/");
  for (const [name, path] of [["Images", "images"], ["Videos", "videos"], ["Photography", "photography"]]) {
    await expect(page.locator("main").getByRole("link", { name })).toHaveAttribute("href", `/art/${path}/`);
  }
  const sitemap = await request.get("/sitemap.xml");
  expect(await sitemap.text()).toContain("/art/photography/");
});

for (const [kind, title] of [["photography", "River light"], ["images", "Studio render"]]) {
  test(`${kind} opens fullscreen with keyboard and restores focus`, async ({ page }) => {
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(`/art/${kind}/`);
    const opener = page.getByRole("button", { name: `Open ${title} fullscreen` });
    await expect(opener).toBeVisible();
    await opener.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).not.toBeVisible();
    await expect(opener).toBeFocused();
    if (kind === "photography") {
      await page.getByRole("button", { name: "Next item" }).click();
      await expect(page.getByRole("heading", { name: "Evening street" })).toBeVisible();
      await page.getByRole("button", { name: "Next item" }).click();
      await expect(page.getByRole("heading", { name: title })).toBeVisible();
      await page.getByRole("button", { name: "Previous item" }).click();
      await expect(page.getByRole("heading", { name: "Evening street" })).toBeVisible();
    }
    expect(errors).toEqual([]);
  });
}

test("photography retries a failed image load", async ({ page }) => {
  await page.route("**/media/**", route => route.abort());
  await page.goto("/art/photography/");
  await expect(page.getByRole("alert")).toContainText("could not finish loading");
  await page.unroute("**/media/**");
  await page.getByRole("button", { name: "Retry gallery" }).click();
  await expect(page.getByRole("button", { name: "Open River light fullscreen" })).toBeVisible();
});

test("existing video player loads and plays", async ({ page }) => {
  await page.goto("/art/videos/");
  const video = page.locator("video");
  await expect(video).toBeVisible();
  await expect(video).toHaveAttribute("controls", "");
  await video.evaluate(element => { element.muted = true; return element.play(); });
  await expect.poll(() => video.evaluate(element => element.currentTime)).toBeGreaterThan(0);
  await video.evaluate(element => { if (element instanceof HTMLVideoElement) element.pause(); });
});

test("photography remains readable without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4322/art/photography/");
  await expect(page.getByRole("heading", { name: "River light" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Evening street" })).toBeVisible();
  await context.close();
});

test("existing routes, search, navigation and motion controls", async ({ page }) => {
  for (const path of ["/", "/resume/", "/writing/", "/software/", "/blog/", "/contact/", "/privacy/", "/subscribe/"]) {
    const response = await page.goto(path);
    expect(response.status(), path).toBe(200);
    await expect(page.locator("main")).toBeVisible();
  }
  await page.goto("/search/");
  await page.getByRole("searchbox").fill("Example");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.getByRole("link", { name: "Example project" })).toBeVisible();
  await page.getByRole("link", { name: "Example project" }).click();
  await expect(page.getByText("Project details", { exact: true })).toBeVisible();
  await page.locator("#motion-toggle").click();
  await expect(page.locator("html")).toHaveAttribute("data-motion", "off");
  await page.reload();
  await expect(page.locator("#motion-toggle")).toHaveAttribute("aria-pressed", "false");
  expect((await page.goto("/art/unknown/")).status()).toBe(404);
});
