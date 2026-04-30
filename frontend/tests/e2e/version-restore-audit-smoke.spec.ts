import { expect, test } from "@playwright/test";

const createdAt = "2026-04-25T12:00:00Z";
let restored = false;
let restorePayload: Record<string, unknown> | null = null;

function presentationSummary() {
  return {
    id: "pres_restore_audit",
    session_id: "ses_restore_audit",
    current_file_id: restored ? "sf_restore_audit_v1" : "sf_restore_audit_v2",
    presentation_type: "slides",
    title: "Restore Audit Deck",
    status: "ready",
    created_at: createdAt,
    updated_at: restored ? "2026-04-25T12:20:00Z" : "2026-04-25T12:10:00Z",
    current_file: {
      id: restored ? "sf_restore_audit_v1" : "sf_restore_audit_v2",
      kind: "artifact",
      file_type: "pptx",
      mime_type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      title: "Restore Audit Deck",
      original_filename: restored ? "restore-audit-v1.pptx" : "restore-audit-v2.pptx",
      checksum_sha256: null,
      size_bytes: 8192,
      created_at: createdAt,
      updated_at: restored ? "2026-04-25T12:20:00Z" : "2026-04-25T12:10:00Z",
    },
    latest_version: restored
      ? {
          id: "presver_restore_audit_v3",
          version_number: 3,
          file_id: "sf_restore_audit_v1",
          parent_version_id: "presver_restore_audit_v2",
          change_summary: "Restore to v1: Operator requested rollback after review.",
          created_at: "2026-04-25T12:20:00Z",
        }
      : {
          id: "presver_restore_audit_v2",
          version_number: 2,
          file_id: "sf_restore_audit_v2",
          parent_version_id: "presver_restore_audit_v1",
          change_summary: "Revision",
          created_at: "2026-04-25T12:10:00Z",
        },
  };
}

function versions() {
  const base = [
    {
      id: "presver_restore_audit_v1",
      version_number: 1,
      file_id: "sf_restore_audit_v1",
      parent_version_id: null,
      change_summary: "Initial restore audit deck",
      created_at: createdAt,
    },
    {
      id: "presver_restore_audit_v2",
      version_number: 2,
      file_id: "sf_restore_audit_v2",
      parent_version_id: "presver_restore_audit_v1",
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
      id: "presver_restore_audit_v3",
      version_number: 3,
      file_id: "sf_restore_audit_v1",
      parent_version_id: "presver_restore_audit_v2",
      change_summary: "Restore to v1: Operator requested rollback after review.",
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

    if (method === "GET" && url.pathname === "/sessions/ses_restore_audit/presentations") {
      await route.fulfill({ json: [presentationSummary()] });
      return;
    }

    if (method === "GET" && url.pathname === "/presentations/pres_restore_audit") {
      await route.fulfill({ json: presentationSummary() });
      return;
    }

    if (method === "GET" && url.pathname === "/presentations/pres_restore_audit/versions") {
      await route.fulfill({ json: versions() });
      return;
    }

    if (method === "POST" && url.pathname === "/presentations/pres_restore_audit/versions/presver_restore_audit_v1/restore") {
      restorePayload = route.request().postDataJSON() as Record<string, unknown>;
      restored = true;
      await route.fulfill({
        json: {
          presentation_id: "pres_restore_audit",
          restored_version_id: "presver_restore_audit_v3",
          restored_version_number: 3,
          target_version_id: "presver_restore_audit_v1",
          target_version_number: 1,
          parent_version_id: "presver_restore_audit_v2",
          current_file_id: "sf_restore_audit_v1",
          previous_file_id: "sf_restore_audit_v2",
          change_summary: "Restore to v1: Operator requested rollback after review.",
          created_at: "2026-04-25T12:20:00Z",
          restored_by_user_id: "user_local_default",
          restore_reason: "Operator requested rollback after review.",
          audit_summary: "user_local_default restored presver_restore_audit_v1 after presver_restore_audit_v2",
        },
      });
      return;
    }

    await route.fulfill({ status: 404, json: { detail: `Unexpected ${method} ${url.pathname}` } });
  });
});

test("restore requires target id and reason before sending audit metadata", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("Session id").fill("ses_restore_audit");
  await page.getByRole("button", { name: "Load presentations" }).click();

  await expect(page.getByRole("heading", { name: "Restore Audit Deck" }).first()).toBeVisible();

  await page.getByRole("button", { name: "Load version timeline" }).click();
  await page.getByRole("button", { name: "Select version v1" }).click();

  const restoreButton = page.getByRole("button", { name: "Restore selected version" });
  await expect(restoreButton).toBeDisabled();

  await page.getByLabel("Restore confirmation").fill("RESTORE");
  await expect(restoreButton).toBeDisabled();

  await page.getByLabel("Restore target version id").fill("presver_restore_audit_v1");
  await expect(restoreButton).toBeDisabled();

  await page.getByLabel("Restore reason").fill("Operator requested rollback after review.");
  await expect(restoreButton).toBeEnabled();

  await restoreButton.click();

  await expect(page.getByText("Restored v1 as v3")).toBeVisible();
  await expect(page.getByText("Restore audit: user_local_default restored presver_restore_audit_v1 after presver_restore_audit_v2")).toBeVisible();
  await expect(page.getByText("Restore reason: Operator requested rollback after review.")).toBeVisible();

  expect(restorePayload).not.toBeNull();
  expect(restorePayload?.confirmation).toBe("RESTORE");
  expect(restorePayload?.confirmation_target_version_id).toBe("presver_restore_audit_v1");
  expect(restorePayload?.restore_reason).toBe("Operator requested rollback after review.");
  expect(Object.prototype.hasOwnProperty.call(restorePayload, "plan")).toBe(false);
});
