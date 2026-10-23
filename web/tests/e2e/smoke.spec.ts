import { expect, test } from "@playwright/test";

/**
 * Smoke e2e (CI runs these after `npx playwright install --with-deps chromium`).
 * The dashboard must render, switch language, and expose every nav view.
 */
test("dashboard renders and navigates", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("banner")).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Primary" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Titan|टाइटन/ })).toBeVisible();

  for (const label of ["QC Report", "Differential Expression", "Variant Explorer", "Job History", "Settings"]) {
    await page.getByRole("button", { name: label }).click();
    await expect(page.locator("main section.panel")).toBeVisible();
  }
});

test("language toggle switches to Hindi", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page.getByRole("button", { name: "जॉब इतिहास" })).toBeVisible();
});

test("variant explorer filters are keyboard accessible", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Variant Explorer" }).click();
  await page.getByLabel("QUAL ≥").fill("40");
  await expect(page.getByText(/\/ \d+ rows/)).toBeVisible();
});
