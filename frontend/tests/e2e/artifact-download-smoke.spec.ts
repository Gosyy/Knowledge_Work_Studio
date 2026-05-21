import { expect, test } from "@playwright/test";

const createdAt = "2026-04-25T12:30:00Z";

const artifactSummary = {
  id: "art_e2e_deck",
  session_id: "ses_artifacts",
  task_id: "task_e2e_artifact",
  filename: "board-review-deck.pptx",
  content_type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  size_bytes: 1048576,
  created_at: createdAt,
  download_url: "/artifacts/art_e2e_deck/download",
};

test.beforeEach(async ({ page }) => {
  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();

    if (method === "GET" && url.pathname === "/sessions/ses_artifacts/artifacts") {
      await route.fulfill({ json: [artifactSummary] });
      return;
    }

    await route.fulfill({
      status: 404,
      json: { detail: `Unexpected ${method} ${url.pathname}` },
    });
  });
});

test("artifact export history lists safe download metadata", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Artifact history" })).toBeVisible();

  await page.getByLabel("Artifact history key").fill("ses_artifacts");
  await page.getByRole("button", { name: "Load artifacts" }).click();

  await expect(page.getByRole("heading", { name: "board-review-deck.pptx" })).toBeVisible();
  await expect(page.getByText("application/vnd.openxmlformats-officedocument.presentationml.presentation")).toBeVisible();
  await expect(page.getByText("1.0 MB")).toBeVisible();
  await expect(page.getByText("task_e2e_artifact")).toBeVisible();

  const download = page.getByRole("link", { name: "Download artifact" });
  await expect(download).toHaveAttribute("href", "http://localhost:8000/artifacts/art_e2e_deck/download");

  await expect(page.getByText("storage_key")).toHaveCount(0);
  await expect(page.getByText("storage_uri")).toHaveCount(0);
  await expect(page.getByText("local://")).toHaveCount(0);
});

test("artifact export history handles empty state", async ({ page }) => {
  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();

    if (method === "GET" && url.pathname === "/sessions/ses_empty_artifacts/artifacts") {
      await route.fulfill({ json: [] });
      return;
    }

    await route.fulfill({
      status: 404,
      json: { detail: `Unexpected ${method} ${url.pathname}` },
    });
  });

  await page.goto("/");

  await page.getByLabel("Artifact history key").fill("ses_empty_artifacts");
  await page.getByRole("button", { name: "Load artifacts" }).click();

  await expect(page.getByText("No artifacts were found for this session.")).toBeVisible();
});

test("artifact export history surfaces load errors", async ({ page }) => {
  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();

    if (method === "GET" && url.pathname === "/sessions/ses_error_artifacts/artifacts") {
      await route.fulfill({ status: 500, json: { detail: "Artifact service unavailable" } });
      return;
    }

    await route.fulfill({
      status: 404,
      json: { detail: `Unexpected ${method} ${url.pathname}` },
    });
  });

  await page.goto("/");

  await page.getByLabel("Artifact history key").fill("ses_error_artifacts");
  await page.getByRole("button", { name: "Load artifacts" }).click();

  await expect(page.getByText("Artifact service unavailable")).toBeVisible();
});
