import { expect, test } from "@playwright/test";

const createdAt = "2026-04-25T12:00:00Z";

const editablePlanSnapshot = {
  snapshot_id: "plansnap_plan_editor_v1",
  presentation_id: "pres_plan_editor",
  presentation_version_id: "presver_plan_editor_v1",
  created_from_task_id: "task_plan_editor_v1",
  change_summary: "Initial plan-first deck",
  created_at: createdAt,
  plan: {
    schema_version: 1,
    deck_title: "Plan Editor Deck",
    deck_goal: "Review the editable outline before generation.",
    audience: "operator",
    tone: "clear_professional",
    target_slide_count: 2,
    story_arc: ["opening", "analysis"],
    slides: [
      {
        slide_id: "slide_001",
        slide_type: "title",
        story_arc_stage: "opening",
        title: "Plan editor opening",
        bullets: ["Start from saved plan"],
      },
      {
        slide_id: "slide_002",
        slide_type: "content",
        story_arc_stage: "analysis",
        title: "Plan editor analysis",
        bullets: ["Review the baseline outline"],
      },
    ],
  },
};

test.beforeEach(async ({ page }) => {
  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();

    if (method === "GET" && url.pathname === "/presentations/pres_plan_editor/plan") {
      await route.fulfill({ json: editablePlanSnapshot });
      return;
    }

    await route.fulfill({
      status: 404,
      json: { detail: `Unexpected ${method} ${url.pathname}` },
    });
  });
});

test("slides plan editor edits saved plan and prepares retry payload", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Slides plan editor" })).toBeVisible();

  await page.getByLabel("Plan editor presentation id").fill("pres_plan_editor");
  await page.getByRole("button", { name: "Load editable plan" }).click();

  await expect(page.getByRole("heading", { name: "Editable saved plan" })).toBeVisible();
  await expect(page.getByText("plansnap_plan_editor_v1")).toBeVisible();

  await page.getByLabel("Editable deck title").fill("Edited Plan-First Deck");
  await page.getByLabel("Slide 2 title").fill("Edited analysis from saved plan");
  await page.getByLabel("Slide 2 bullets").fill("Preserve saved plan provenance\nRetry only after operator review");
  await page.getByLabel("Template mode").check();
  await page.getByLabel("Retry instruction").fill("Retry this saved plan with the selected template mode.");

  await page.getByRole("button", { name: "Save editable plan draft" }).click();
  await expect(page.getByText("Saved editable plan draft.")).toBeVisible();

  await page.getByRole("button", { name: "Prepare retry from saved plan" }).click();

  await expect(page.getByRole("heading", { name: "Retry from saved plan ready" })).toBeVisible();
  await expect(page.getByText("template mode · plansnap_plan_editor_v1 · 2 slide(s)")).toBeVisible();
  await expect(page.getByText("Edited Plan-First Deck")).toBeVisible();
  await expect(page.getByText("Edited analysis from saved plan")).toBeVisible();
  await expect(page.getByText("slides.retry.from_saved_plan.requested")).toBeVisible();
});
