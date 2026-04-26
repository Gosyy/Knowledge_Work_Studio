import { expect, test } from "@playwright/test";

const createdAt = "2026-04-25T12:00:00Z";
let revisionCreated = false;
let slideRevisionPayload: Record<string, unknown> | null = null;

function presentationSummary() {
  return {
    id: "pres_e2e",
    session_id: "ses_e2e",
    current_file_id: revisionCreated ? "sf_e2e_v2" : "sf_e2e_v1",
    presentation_type: "slides",
    title: "E2E Deck Revision Smoke",
    status: "ready",
    created_at: createdAt,
    updated_at: revisionCreated ? "2026-04-25T12:10:00Z" : createdAt,
    current_file: {
      id: revisionCreated ? "sf_e2e_v2" : "sf_e2e_v1",
      kind: "artifact",
      file_type: "pptx",
      mime_type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      title: "E2E Deck Revision Smoke",
      original_filename: revisionCreated ? "e2e-deck-v2.pptx" : "e2e-deck-v1.pptx",
      checksum_sha256: null,
      size_bytes: 4096,
      created_at: createdAt,
      updated_at: revisionCreated ? "2026-04-25T12:10:00Z" : createdAt,
    },
    latest_version: {
      id: revisionCreated ? "presver_e2e_v2" : "presver_e2e_v1",
      version_number: revisionCreated ? 2 : 1,
      file_id: revisionCreated ? "sf_e2e_v2" : "sf_e2e_v1",
      parent_version_id: revisionCreated ? "presver_e2e_v1" : null,
      change_summary: revisionCreated ? "Sharpen analysis slide" : "Initial deck",
      created_at: revisionCreated ? "2026-04-25T12:10:00Z" : createdAt,
    },
  };
}

const planSnapshot = {
  snapshot_id: "plansnap_e2e_v1",
  presentation_id: "pres_e2e",
  presentation_version_id: "presver_e2e_v1",
  created_from_task_id: "task_e2e",
  change_summary: "Initial deck",
  created_at: createdAt,
  plan: {
    schema_version: 1,
    deck_title: "E2E Deck Revision Smoke",
    target_slide_count: 2,
    slides: [
      {
        slide_id: "slide_001",
        slide_type: "title",
        story_arc_stage: "opening",
        title: "Opening",
        bullets: ["Start with context"],
      },
      {
        slide_id: "slide_002",
        slide_type: "content",
        story_arc_stage: "analysis",
        title: "Analysis",
        bullets: ["Explain the current tradeoff"],
      },
    ],
  },
};

test.beforeEach(async ({ page }) => {
  revisionCreated = false;
  slideRevisionPayload = null;

  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();

    if (method === "GET" && url.pathname === "/sessions/ses_e2e/presentations") {
      await route.fulfill({ json: [presentationSummary()] });
      return;
    }

    if (method === "GET" && url.pathname === "/presentations/pres_e2e") {
      await route.fulfill({ json: presentationSummary() });
      return;
    }

    if (method === "GET" && url.pathname === "/presentations/pres_e2e/plan") {
      await route.fulfill({ json: planSnapshot });
      return;
    }

    if (method === "POST" && url.pathname === "/presentations/pres_e2e/revisions/slide") {
      slideRevisionPayload = route.request().postDataJSON() as Record<string, unknown>;
      revisionCreated = true;
      await route.fulfill({
        json: {
          presentation_id: "pres_e2e",
          version_id: "presver_e2e_v2",
          version_number: 2,
          parent_version_id: "presver_e2e_v1",
          stored_file_id: "sf_e2e_v2",
          revised_slide_ids: ["slide_002"],
          scope: "slide",
          change_summary: "Sharpen analysis slide",
          created_at: "2026-04-25T12:10:00Z",
          current_file_id: "sf_e2e_v2",
          previous_file_id: "sf_e2e_v1",
        },
      });
      return;
    }

    await route.fulfill({
      status: 404,
      json: { detail: `Unexpected ${method} ${url.pathname}` },
    });
  });
});

test("presentation registry, plan inspect, and slide revision omit explicit plan payload", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Presentations" })).toBeVisible();

  await page.getByLabel("Session id").fill("ses_e2e");
  await page.getByRole("button", { name: "Load presentations" }).click();

  await expect(page.getByRole("heading", { name: "E2E Deck Revision Smoke" }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Load current plan" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Load latest diff" })).toBeVisible();

  await page.getByRole("button", { name: "Load current plan" }).click();

  await expect(page.getByText("Current plan snapshot")).toBeVisible();
  await expect(page.getByText("Analysis", { exact: true })).toBeVisible();

  await page.getByLabel("Revision instruction").fill("Make the analysis slide sharper and more executive.");
  await page.getByLabel("Revision change summary").fill("Sharpen analysis slide");
  await page.getByLabel("Target slide index").fill("1");
  await page.getByRole("button", { name: "Create revision" }).click();

  await expect(page.getByText(/Created revision v2/)).toBeVisible();
  await expect(page.getByText("sf_e2e_v2", { exact: true })).toBeVisible();

  expect(slideRevisionPayload).not.toBeNull();
  expect(slideRevisionPayload?.instruction).toBe("Make the analysis slide sharper and more executive.");
  expect(slideRevisionPayload?.change_summary).toBe("Sharpen analysis slide");
  expect(slideRevisionPayload?.target_slide_index).toBe(1);
  expect(Object.prototype.hasOwnProperty.call(slideRevisionPayload, "plan")).toBe(false);
});
