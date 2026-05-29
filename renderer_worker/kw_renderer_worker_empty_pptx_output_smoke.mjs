#!/usr/bin/env node
/**
 * KR-7H.7 controlled empty PPTX file output smoke.
 *
 * This script performs the first controlled PptxGenJS file-output smoke inside
 * the isolated renderer_worker package. It writes a temporary empty .pptx file
 * to an ephemeral directory, verifies that the file exists and has non-zero
 * size, then removes the file and directory before returning a deterministic
 * JSON report. It intentionally does not map PresentationIR, add slide content,
 * persist artifacts, run LibreOffice, create proof bundles, or claim production
 * renderer readiness.
 */

import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import PptxGenJS from "pptxgenjs";

const SCHEMA_VERSION = "presentation_renderer_worker_empty_pptx_output_smoke.v1";
const EXPECTED_PACKAGE_NAME = "pptxgenjs";
const EXPECTED_PACKAGE_VERSION = "4.0.1";
const OUTPUT_BASENAME = "kr7h7-empty-output-smoke.pptx";

const BLOCKED_RUNTIME_ACTIONS = Object.freeze([
  "map_presentation_ir_to_slides",
  "add_slide_content",
  "generate_user_visible_deck",
  "persist_pptx_artifact",
  "run_libreoffice_pdf_export",
  "render_slide_png_proofs",
  "write_artifact_bundle",
  "write_proof_bundle",
  "claim_visual_quality_score",
]);

function issue(code, message, target = null) {
  return { code, message, target };
}

function response(status, issues, smoke = {}) {
  return {
    schema_version: SCHEMA_VERSION,
    phase: "KR-7H.7 controlled empty PPTX file output smoke",
    status,
    dependency_name: EXPECTED_PACKAGE_NAME,
    expected_dependency_version: EXPECTED_PACKAGE_VERSION,
    dependency_available: status === "ready",
    dependency_version: EXPECTED_PACKAGE_VERSION,
    module_default_export_type: typeof PptxGenJS,
    module_default_export_name: PptxGenJS && PptxGenJS.name ? String(PptxGenJS.name) : null,
    empty_pptx_output_smoke_implemented: true,
    temporary_pptx_write_api_called: Boolean(smoke.temporaryPptxWriteApiCalled),
    temporary_pptx_written: Boolean(smoke.temporaryPptxWritten),
    temporary_pptx_deleted: Boolean(smoke.temporaryPptxDeleted),
    temporary_directory_removed: Boolean(smoke.temporaryDirectoryRemoved),
    temporary_output_basename: OUTPUT_BASENAME,
    temporary_pptx_file_size_bytes: Number.isInteger(smoke.temporaryPptxFileSizeBytes)
      ? smoke.temporaryPptxFileSizeBytes
      : null,
    temporary_pptx_file_size_nonzero: Boolean(smoke.temporaryPptxFileSizeNonzero),
    slide_count: Number.isInteger(smoke.slideCount) ? smoke.slideCount : null,
    slide_content_added: false,
    presentation_ir_mapping_implemented: false,
    production_pptx_output_implemented: false,
    renderer_runtime_implemented: false,
    persistent_artifact_written: false,
    filesystem_output_written: false,
    pptx_generation_executed: false,
    artifact_bundle_produced: false,
    proof_bundle_produced: false,
    libreoffice_executed: false,
    visual_qa_executed: false,
    output_mode: "temporary_empty_pptx_output_smoke_only",
    blocked_runtime_actions: [...BLOCKED_RUNTIME_ACTIONS],
    non_goals: [
      "no_production_pptx_generation",
      "no_presentation_ir_mapping",
      "no_slide_content_generation",
      "no_persistent_filesystem_output",
      "no_libreoffice_execution",
      "no_artifact_bundle_storage",
      "no_proof_bundle_generation",
      "no_visual_qa_scoring",
      "no_frontend_package_changes",
      "no_production_quality_output_claims",
    ],
    issues,
  };
}

async function pathExists(candidate) {
  try {
    await fs.access(candidate);
    return true;
  } catch (_error) {
    return false;
  }
}

async function runEmptyPptxOutputSmoke() {
  const issues = [];
  if (typeof PptxGenJS !== "function") {
    return response("blocked", [issue("pptxgenjs_default_export_unexpected", "PptxGenJS default export must be a constructor function for output smoke.", EXPECTED_PACKAGE_NAME)]);
  }

  let tempDir = null;
  let outputPath = null;
  const smoke = {
    temporaryPptxWriteApiCalled: false,
    temporaryPptxWritten: false,
    temporaryPptxDeleted: false,
    temporaryDirectoryRemoved: false,
    temporaryPptxFileSizeBytes: null,
    temporaryPptxFileSizeNonzero: false,
    slideCount: null,
  };

  try {
    const presentation = new PptxGenJS();
    if (Array.isArray(presentation._slides)) {
      smoke.slideCount = presentation._slides.length;
    } else if (Array.isArray(presentation.slides)) {
      smoke.slideCount = presentation.slides.length;
    } else {
      issues.push(issue("pptxgenjs_slide_collection_unexpected", "Constructed presentation object does not expose a recognized slide collection.", EXPECTED_PACKAGE_NAME));
    }
    if (smoke.slideCount !== 0) {
      issues.push(issue("pptxgenjs_empty_output_slide_count_unexpected", `Empty output smoke must not add slides; got ${smoke.slideCount}.`, EXPECTED_PACKAGE_NAME));
    }

    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "kw-kr7h7-empty-pptx-"));
    outputPath = path.join(tempDir, OUTPUT_BASENAME);
    smoke.temporaryPptxWriteApiCalled = true;
    const returnedPath = await presentation.writeFile({ fileName: outputPath });
    if (returnedPath !== outputPath) {
      issues.push(issue("pptxgenjs_writefile_return_path_unexpected", "PptxGenJS writeFile returned an unexpected path for the temporary smoke output.", OUTPUT_BASENAME));
    }

    const stat = await fs.stat(outputPath);
    smoke.temporaryPptxWritten = stat.isFile();
    smoke.temporaryPptxFileSizeBytes = stat.size;
    smoke.temporaryPptxFileSizeNonzero = stat.size > 0;
    if (!smoke.temporaryPptxWritten || !smoke.temporaryPptxFileSizeNonzero) {
      issues.push(issue("temporary_pptx_output_missing_or_empty", "Temporary empty PPTX smoke output must exist and have non-zero size before cleanup.", OUTPUT_BASENAME));
    }
  } catch (error) {
    issues.push(issue("temporary_pptx_output_smoke_failed", `Could not complete temporary empty PPTX output smoke: ${error.message}`, OUTPUT_BASENAME));
  } finally {
    if (outputPath) {
      try {
        await fs.rm(outputPath, { force: true });
        smoke.temporaryPptxDeleted = !(await pathExists(outputPath));
      } catch (error) {
        issues.push(issue("temporary_pptx_cleanup_failed", `Could not delete temporary PPTX output: ${error.message}`, OUTPUT_BASENAME));
      }
    }
    if (tempDir) {
      try {
        await fs.rm(tempDir, { recursive: true, force: true });
        smoke.temporaryDirectoryRemoved = !(await pathExists(tempDir));
      } catch (error) {
        issues.push(issue("temporary_directory_cleanup_failed", `Could not remove temporary PPTX smoke directory: ${error.message}`, null));
      }
    }
  }

  if (!smoke.temporaryPptxDeleted) {
    issues.push(issue("temporary_pptx_not_deleted", "Temporary PPTX smoke output must be deleted before returning ready.", OUTPUT_BASENAME));
  }
  if (!smoke.temporaryDirectoryRemoved) {
    issues.push(issue("temporary_directory_not_removed", "Temporary PPTX smoke directory must be removed before returning ready.", null));
  }

  return response(issues.length === 0 ? "ready" : "blocked", issues, smoke);
}

function parseArgs(argv) {
  const args = { json: false, help: false };
  for (const arg of argv) {
    if (arg === "--json") {
      args.json = true;
    } else if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
}

function printHelp() {
  console.log("Usage: node renderer_worker/kw_renderer_worker_empty_pptx_output_smoke.mjs [--json]\n\nWrites a temporary empty PPTX for capability smoke only, verifies non-zero size, deletes it, and returns a fail-closed JSON report. Does not persist artifacts, map PresentationIR, run LibreOffice, or claim production rendering.");
}

async function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    console.log(JSON.stringify(response("blocked", [issue("invalid_cli_arguments", String(error.message), null)]), null, 2));
    process.exitCode = 2;
    return;
  }

  if (args.help) {
    printHelp();
    return;
  }

  const result = await runEmptyPptxOutputSmoke();
  console.log(JSON.stringify(result, null, 2));
  if (result.status !== "ready") {
    process.exitCode = 1;
  }
}

await main();
