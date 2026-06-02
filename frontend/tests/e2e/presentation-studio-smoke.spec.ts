import { expect, test } from "@playwright/test";

const studioSnapshot = {
  schema_version: "presentation_studio_ui.v1",
  presentation_id: "pres_studio_ui",
  deck_title: "Presentation Studio Board Review",
  backend_url: "http://localhost:8000",
  openapi_schema_path: "/openapi.json",
  export_backend_side: true,
  frontend_side_generation_allowed: false,
  arbitrary_model_selector_allowed: false,
  slides: [
    {
      slide_id: "slide_001",
      slide_index: 1,
      title: "Executive opening",
      role: "opening",
      layout_family: "title_body",
      thumbnail_label: "01",
      blocks: [
        { block_id: "block_title", block_type: "title", text: "Executive opening", source_refs: ["src_board_001"] },
        { block_id: "block_body", block_type: "body", text: "Operator-reviewed narrative", source_refs: ["src_board_002"] },
      ],
      quality_warnings: ["Review density before export"],
      source_refs: ["src_board_001", "src_board_002"],
    },
    {
      slide_id: "slide_002",
      slide_index: 2,
      title: "Data-backed chart",
      role: "analysis",
      layout_family: "chart_right",
      thumbnail_label: "02",
      blocks: [
        { block_id: "block_chart", block_type: "chart", text: "Revenue trend", source_refs: ["table_001"] },
      ],
      quality_warnings: [],
      source_refs: ["table_001"],
    },
  ],
  assets: [
    {
      asset_id: "asset_image_001",
      kind: "image",
      filename: "board-photo.png",
      checksum_sha256: "sha256:board-photo",
      provenance_ref: "src_board_001",
    },
  ],
  quality_warnings: ["Deck requires backend-side export proof before release"],
};

let savedDraftBody: unknown = null;
let exportRequestBody: unknown = null;

test.beforeEach(async ({ page }) => {
  savedDraftBody = null;
  exportRequestBody = null;

  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();

    if (method === "GET" && url.pathname === "/presentations/pres_studio_ui/studio") {
      await route.fulfill({ json: studioSnapshot });
      return;
    }

    if (method === "PUT" && url.pathname === "/presentations/pres_studio_ui/studio/draft") {
      savedDraftBody = await route.request().postDataJSON();
      await route.fulfill({
        json: {
          presentation_id: "pres_studio_ui",
          draft_id: "studiodraft_001",
          persisted_through_backend_api: true,
          updated_at: "2026-06-01T09:00:00Z",
        },
      });
      return;
    }

    if (method === "POST" && url.pathname === "/presentations/pres_studio_ui/exports") {
      exportRequestBody = await route.request().postDataJSON();
      await route.fulfill({
        json: {
          presentation_id: "pres_studio_ui",
          artifact_id: "artifact_studio_export",
          export_format: "pptx",
          backend_side_export: true,
          download_url: "/artifacts/artifact_studio_export/download",
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

test("Presentation Studio loads API-first editing shell and persists draft through backend API", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Presentation Studio" })).toBeVisible();
  await expect(page.getByText("Frontend-side generation: disabled")).toBeVisible();
  await expect(page.getByText("OpenAPI: http://localhost:8000/openapi.json")).toBeVisible();

  await page.getByLabel("Presentation Studio id").fill("pres_studio_ui");
  await page.getByRole("button", { name: "Load Presentation Studio" }).click();

  await expect(page.getByRole("heading", { name: "Presentation Studio Board Review" })).toBeVisible();
  await expect(page.getByLabel("Slide thumbnails")).toContainText("01 · Executive opening");
  await expect(page.getByLabel("Slide canvas preview")).toContainText("Operator-reviewed narrative");
  await expect(page.getByLabel("Block inspector")).toContainText("Review density before export");
  await expect(page.getByLabel("Asset tray")).toContainText("board-photo.png");
  await expect(page.getByLabel("Deck quality warnings")).toContainText("backend-side export proof");

  await page.getByLabel("Selected slide title").fill("Edited executive opening");
  await page.getByRole("button", { name: "Save studio draft via backend API" }).click();

  await expect(page.getByText("Saved draft studiodraft_001 through backend API.")).toBeVisible();
  expect(savedDraftBody).toMatchObject({
    schema_version: "presentation_studio_ui.v1",
    selected_slide_id: "slide_001",
    edited_slide_title: "Edited executive opening",
  });
  expect(JSON.stringify(savedDraftBody)).toContain("presentation_studio.draft_saved_via_backend_api");

  await page.getByRole("button", { name: "Request backend PPTX export" }).click();
  await expect(page.getByText("Backend export ready: artifact_studio_export")).toBeVisible();
  expect(exportRequestBody).toEqual({
    export_format: "pptx",
    backend_side_export: true,
    presentation_studio_ui_schema_version: "presentation_studio_ui.v1",
  });
});
