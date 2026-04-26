import { expect, test } from "@playwright/test";

const createdAt = "2026-04-25T12:00:00Z";

function presentationSummary() {
  return {
    id: "pres_timeline",
    session_id: "ses_timeline",
    current_file_id: "sf_timeline_v2",
    presentation_type: "slides",
    title: "Timeline Deck",
    status: "ready",
    created_at: createdAt,
    updated_at: "2026-04-25T12:10:00Z",
    current_file: {
      id: "sf_timeline_v2",
      kind: "artifact",
      file_type: "pptx",
      mime_type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      title: "Timeline Deck",
      original_filename: "timeline-v2.pptx",
      checksum_sha256: null,
      size_bytes: 8192,
      created_at: "2026-04-25T12:10:00Z",
      updated_at: "2026-04-25T12:10:00Z",
    },
    latest_version: {
      id: "presver_timeline_v2",
      version_number: 2,
      file_id: "sf_timeline_v2",
      parent_version_id: "presver_timeline_v1",
      change_summary: "Timeline revision",
      created_at: "2026-04-25T12:10:00Z",
    },
  };
}

const versions = [
  {
    id: "presver_timeline_v1",
    version_number: 1,
    file_id: "sf_timeline_v1",
    parent_version_id: null,
    change_summary: "Initial timeline deck",
    created_at: createdAt,
  },
  {
    id: "presver_timeline_v2",
    version_number: 2,
    file_id: "sf_timeline_v2",
    parent_version_id: "presver_timeline_v1",
    change_summary: "Timeline revision",
    created_at: "2026-04-25T12:10:00Z",
  },
];

const selectedPlan = {
  snapshot_id: "plansnap_timeline_v2",
  presentation_id: "pres_timeline",
  presentation_version_id: "presver_timeline_v2",
  created_from_task_id: "task_timeline_v2",
  change_summary: "Timeline revision",
  created_at: "2026-04-25T12:10:00Z",
  plan: {
    schema_version: 1,
    deck_title: "Timeline Deck",
    target_slide_count: 2,
    slides: [
      {
        slide_id: "slide_001",
        slide_type: "title",
        story_arc_stage: "opening",
        title: "Timeline opening",
        bullets: ["Introduce the timeline"],
      },
      {
        slide_id: "slide_002",
        slide_type: "content",
        story_arc_stage: "analysis",
        title: "Timeline analysis",
        bullets: ["Show the revised plan"],
      },
    ],
  },
};

const selectedDiff = {
  presentation_id: "pres_timeline",
  base_version_id: "presver_timeline_v1",
  compared_version_id: "presver_timeline_v2",
  base_snapshot_id: "plansnap_timeline_v1",
  compared_snapshot_id: "plansnap_timeline_v2",
  changed_slide_count: 1,
  slide_deltas: [
    {
      slide_id: "slide_002",
      change_type: "modified",
      before_index: 1,
      after_index: 1,
      title_before: "Old analysis",
      title_after: "Timeline analysis",
      story_arc_stage_before: "analysis",
      story_arc_stage_after: "analysis",
      layout_hint_before: null,
      layout_hint_after: null,
      bullets_added: ["Show the revised plan"],
      bullets_removed: ["Show the old plan"],
      speaker_notes_changed: false,
    },
  ],
};

test.beforeEach(async ({ page }) => {
  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();

    if (method === "GET" && url.pathname === "/sessions/ses_timeline/presentations") {
      await route.fulfill({ json: [presentationSummary()] });
      return;
    }

    if (method === "GET" && url.pathname === "/presentations/pres_timeline/versions") {
      await route.fulfill({ json: versions });
      return;
    }

    if (method === "GET" && url.pathname === "/presentations/pres_timeline/versions/presver_timeline_v2/plan") {
      await route.fulfill({ json: selectedPlan });
      return;
    }

    if (method === "GET" && url.pathname === "/presentations/pres_timeline/revisions/presver_timeline_v2/diff") {
      await route.fulfill({ json: selectedDiff });
      return;
    }

    await route.fulfill({
      status: 404,
      json: { detail: `Unexpected ${method} ${url.pathname}` },
    });
  });
});

test("version timeline loads versions, selected plan, and selected version diff", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("Session id").fill("ses_timeline");
  await page.getByRole("button", { name: "Load presentations" }).click();

  await expect(page.getByRole("heading", { name: "Timeline Deck" }).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Version timeline" })).toBeVisible();

  await page.getByRole("button", { name: "Load version timeline" }).click();

  await expect(page.getByRole("button", { name: "Select version v2" })).toBeVisible();
  await expect(page.getByText("presver_timeline_v2", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Load selected version plan" }).click();

  await expect(page.getByText("Selected version plan snapshot")).toBeVisible();
  await expect(page.getByText("Timeline analysis", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Load selected version diff" }).click();

  await expect(page.getByRole("heading", { name: "Selected version diff" })).toBeVisible();
  await expect(page.getByText("slide_002")).toBeVisible();
  await expect(page.getByText("Added bullets: Show the revised plan")).toBeVisible();
});
