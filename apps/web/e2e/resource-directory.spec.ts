import { expect, test } from "@playwright/test";

test("search, filter, open details, and return with state", async ({
  page,
}) => {
  await page.goto("/resources");
  await expect(page.getByText("Call 911 for immediate danger.")).toBeVisible();
  await page.getByLabel("What do you need?").fill("food");
  await page.getByLabel("City").fill("Exampleville");
  await page.getByRole("button", { name: "Search resources" }).click();
  await expect(page.getByText("1 resources found")).toBeVisible({
    timeout: 15_000,
  });
  await page.getByRole("link", { name: "View details" }).click();
  await expect(
    page.getByRole("heading", { name: /Example Food Support/ }),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "Contact" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Sources" })).toBeVisible();
  await page.goBack();
  await expect(page.getByLabel("What do you need?")).toHaveValue("food");
  await expect(page.getByLabel("City")).toHaveValue("Exampleville");
});
