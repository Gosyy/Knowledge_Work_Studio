import { expect, test } from "@playwright/test";

const createdAt = "2026-04-25T12:00:00Z";
let restored = false;
let restorePayload: Record<string, unknown> | null = null;

function presentationSummary() {
  return {
    id: "pres_restore",
    session_id: "ses_restore",
    current_file_id: restored ? "sf_restore_v1" : "sf_restore_v2",
    presentation_type: "slides",
    title: "Restore Deck",
    status: "ready",
    created_at: createdAt,
    updated_at: restored ? "2026-04-25T12:20:00Z" : "2026-04-25T12:10:00Z",
    current_file: {
      id: restored ? "sf_restore_v1" : "sf_restore_v2",
      kind: "artifact",
      file_type: "pptx",
      mime_type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      title: "Restore Deck",
      original_filename: restored ? "restore-v1.pptx" : "restore-v2.pptx",
      checksum_sha256: null,
      size_bytes: 8192,
      created_at: createdAt,
      updated_at: restored ? "2026-04-25T12:20:00Z" : "2026-04-25T12:10:00Z",
    },
    latest_version: restored
      ? {
          id: "presver_restore_v3",
          version_number: 3,
          file_id: "sf_restore_v1",
          parent_version_id: "presver_restore_v2",
          change_summary: "Restore to v1",
          created_at: "2026-04-25T12:20:00Z",
        }
      : {
          id: "presver_restore_v2",
          version_number: 2,
          file_id: "sf_restore_v2",
          parent_version_id: "presver_restore_v1",
          change_summary: "Revision",
          created_at: "2026-04-25T12:10:00Z",
        },
  };
}

function versions() {
  const base = [
    {
      id: "presver_restore_v1",
      version_number: 1,
      file_id: "sf_restore_v1",
      parent_version_id: null,
      change_summary: "Initial restore deck",
      created_at: createdAt,
    },
    {
      id: "presver_restore_v2",
      version_number: 2,
      file_id: "sf_restore_v2",
      parent_version_id: "presver_restore_v1",
      change_summary: "Revision",
      created_at: "2026-04-25T12:10:00Z",
    },
  ];
  if (!restored) {
    return base;
  }
  return [
    ...base,
    {
      id: "presver_restore_v3",
      version_number: 3,
      file_id: "sf_restore_v1",
      parent_version_id: "presver_restore_v2",
      change_summary: "Restore to v1",
      created_at: "2026-04-25T12:20:00Z",
    },
  ];
}

test.beforeEach(async ({ page }) => {
  restored = false;
  restorePayload = null;

  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();

    if (method === "GET" && url.pathname === "/sessions/ses_restore/presentations") {
      await route.fulfill({ json: [presentationSummary()] });
      return;
    }

    if (method === "GET" && url.pathname === "/presentations/pres_restore") {
      await route.fulfill({ json: presentationSummary() });
      return;
    }

    if (method === "GET" && url.pathname === "/presentations/pres_restore/versions") {
      await route.fulfill({ json: versions() });
      return;
    }

    if (method === "POST" && url.pathname === "/presentations/pres_restore/versions/presver_restore_v1/restore") {
      restorePayload = route.request().postDataJSON() as Record<string, unknown>;
      restored = true;
      await route.fulfill({
        json: {
          presentation_id: "pres_restore",
          restored_version_id: "presver_restore_v3",
          restored_version_number: 3,
          target_version_id: "presver_restore_v1",
          target_version_number: 1,
          parent_version_id: "presver_restore_v2",
          current_file_id: "sf_restore_v1",
          previous_file_id: "sf_restore_v2",
          change_summary: "Restore to v1",
          created_at: "2026-04-25T12:20:00Z",
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

test("version timeline restores selected historical version with deliberate confirmation", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("Session id").fill("ses_restore");
  await page.getByRole("button", { name: "Load presentations" }).click();

  await expect(page.getByRole("heading", { name: "Restore Deck" }).first()).toBeVisible();

  await page.getByRole("button", { name: "Load version timeline" }).click();
  await page.getByRole("button", { name: "Select version v1" }).click();

  await page.getByLabel("Restore confirmation").fill("RESTORE");
  await page.getByRole("button", { name: "Restore selected version" }).click();

  await expect(page.getByText("Restored v1 as v3")).toBeVisible();
  await expect(page.getByText("presver_restore_v3", { exact: true })).toBeVisible();

  expect(restorePayload).not.toBeNull();
  expect(restorePayload?.confirmation).toBe("RESTORE");
  expect(Object.prototype.hasOwnProperty.call(restorePayload, "plan")).toBe(false);
});
