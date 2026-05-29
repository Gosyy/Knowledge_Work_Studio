#!/usr/bin/env node
/**
 * KR-7H.8 controlled static single-slide PPTX output smoke.
 *
 * This script performs the next controlled PptxGenJS file-output smoke inside
 * the isolated renderer_worker package. It writes a temporary .pptx containing
 * one fixed technical smoke slide, verifies that the file exists and has
 * non-zero size, then removes the file and directory before returning a
 * deterministic JSON report. It intentionally does not map PresentationIR,
 * use user prompt/evidence content, persist artifacts, run LibreOffice, create
 * proof bundles, or claim production renderer readiness.
 */

import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import PptxGenJS from "pptxgenjs";

const SCHEMA_VERSION = "presentation_renderer_worker_static_slide_output_smoke.v1";
const EXPECTED_PACKAGE_NAME = "pptxgenjs";
const EXPECTED_PACKAGE_VERSION = "4.0.1";
const OUTPUT_BASENAME = "kr7h8-static-slide-output-smoke.pptx";
const STATIC_TITLE = "KW Studio Renderer Worker Smoke";
const STATIC_SUBTITLE = "KR-7H.8 static slide output smoke only";

const BLOCKED_RUNTIME_ACTIONS = Object.freeze([
  "map_presentation_ir_to_slides",
  "use_user_prompt_content",
  "use_evidence_content",
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
    phase: "KR-7H.8 controlled static single-slide PPTX output smoke",
    status,
    dependency_name: EXPECTED_PACKAGE_NAME,
    expected_dependency_version: EXPECTED_PACKAGE_VERSION,
    dependency_available: status === "ready",
    dependency_version: EXPECTED_PACKAGE_VERSION,
    module_default_export_type: typeof PptxGenJS,
    module_default_export_name: PptxGenJS && PptxGenJS.name ? String(PptxGenJS.name) : null,
    static_slide_output_smoke_implemented: true,
    temporary_pptx_write_api_called: Boolean(smoke.temporaryPptxWriteApiCalled),
    temporary_pptx_written: Boolean(smoke.temporaryPptxWritten),
    temporary_pptx_deleted: Boolean(smoke.temporaryPptxDeleted),
    temporary_directory_removed: Boolean(smoke.temporaryDirectoryRemoved),
    temporary_output_basename: OUTPUT_BASENAME,
    temporary_pptx_file_size_bytes: Number.isInteger(smoke.temporaryPptxFileSizeBytes)
      ? smoke.temporaryPptxFileSizeBytes
      : null,
    temporary_pptx_file_size_nonzero: Boolean(smoke.temporaryPptxFileSizeNonzero),
    static_slide_count: Number.isInteger(smoke.staticSlideCount) ? smoke.staticSlideCount : null,
    static_slide_content_added: Boolean(smoke.staticSlideContentAdded),
    static_slide_title: STATIC_TITLE,
    static_slide_subtitle: STATIC_SUBTITLE,
    static_slide_uses_user_content: false,
    static_slide_uses_presentation_ir: false,
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
    output_mode: "temporary_static_single_slide_output_smoke_only",
    blocked_runtime_actions: [...BLOCKED_RUNTIME_ACTIONS],
    non_goals: [
      "no_production_pptx_generation",
      "no_presentation_ir_mapping",
      "no_user_prompt_content",
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

function detectSlideCount(presentation) {
  if (Array.isArray(presentation._slides)) {
    return presentation._slides.length;
  }
  if (Array.isArray(presentation.slides)) {
    return presentation.slides.length;
  }
  return null;
}

async function runStaticSlideOutputSmoke() {
  const issues = [];
  if (typeof PptxGenJS !== "function") {
    return response("blocked", [issue("pptxgenjs_default_export_unexpected", "PptxGenJS default export must be a constructor function for static slide output smoke.", EXPECTED_PACKAGE_NAME)]);
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
    staticSlideCount: null,
    staticSlideContentAdded: false,
  };

  try {
    const presentation = new PptxGenJS();
    presentation.layout = "LAYOUT_WIDE";
    const slide = presentation.addSlide();
    slide.addText(STATIC_TITLE, { x: 0.7, y: 0.7, w: 11.8, h: 0.6, fontFace: "Arial", fontSize: 24, bold: true });
    slide.addText(STATIC_SUBTITLE, { x: 0.7, y: 1.55, w: 11.8, h: 0.45, fontFace: "Arial", fontSize: 14 });
    smoke.staticSlideContentAdded = true;
    smoke.staticSlideCount = detectSlideCount(presentation);
    if (smoke.staticSlideCount !== 1) {
      issues.push(issue("pptxgenjs_static_slide_count_unexpected", `Static slide output smoke must create exactly one technical slide; got ${smoke.staticSlideCount}.`, EXPECTED_PACKAGE_NAME));
    }

    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "kw-kr7h8-static-slide-pptx-"));
    outputPath = path.join(tempDir, OUTPUT_BASENAME);
    smoke.temporaryPptxWriteApiCalled = true;
    const returnedPath = await presentation.writeFile({ fileName: outputPath });
    if (returnedPath !== outputPath) {
      issues.push(issue("pptxgenjs_writefile_return_path_unexpected", "PptxGenJS writeFile returned an unexpected path for the temporary static slide smoke output.", OUTPUT_BASENAME));
    }

    const stat = await fs.stat(outputPath);
    smoke.temporaryPptxWritten = stat.isFile();
    smoke.temporaryPptxFileSizeBytes = stat.size;
    smoke.temporaryPptxFileSizeNonzero = stat.size > 0;
    if (!smoke.temporaryPptxWritten || !smoke.temporaryPptxFileSizeNonzero) {
      issues.push(issue("temporary_static_slide_pptx_output_missing_or_empty", "Temporary static slide PPTX smoke output must exist and have non-zero size before cleanup.", OUTPUT_BASENAME));
    }
  } catch (error) {
    issues.push(issue("temporary_static_slide_output_smoke_failed", `Could not complete temporary static slide PPTX output smoke: ${error.message}`, OUTPUT_BASENAME));
  } finally {
    if (outputPath) {
      try {
        await fs.rm(outputPath, { force: true });
        smoke.temporaryPptxDeleted = !(await pathExists(outputPath));
      } catch (error) {
        issues.push(issue("temporary_pptx_cleanup_failed", `Could not delete temporary static slide PPTX output: ${error.message}`, OUTPUT_BASENAME));
      }
    }
    if (tempDir) {
      try {
        await fs.rm(tempDir, { recursive: true, force: true });
        smoke.temporaryDirectoryRemoved = !(await pathExists(tempDir));
      } catch (error) {
        issues.push(issue("temporary_directory_cleanup_failed", `Could not remove temporary static slide PPTX smoke directory: ${error.message}`, null));
      }
    }
  }

  if (!smoke.temporaryPptxDeleted) {
    issues.push(issue("temporary_pptx_not_deleted", "Temporary static slide PPTX smoke output must be deleted before returning ready.", OUTPUT_BASENAME));
  }
  if (!smoke.temporaryDirectoryRemoved) {
    issues.push(issue("temporary_directory_not_removed", "Temporary static slide PPTX smoke directory must be removed before returning ready.", null));
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
  console.log("Usage: node renderer_worker/kw_renderer_worker_static_slide_output_smoke.mjs [--json]\n\nWrites a temporary single-slide static PPTX for capability smoke only, verifies non-zero size, deletes it, and returns a fail-closed JSON report. Does not persist artifacts, map PresentationIR, run LibreOffice, or claim production rendering.");
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

  const result = await runStaticSlideOutputSmoke();
  console.log(JSON.stringify(result, null, 2));
  if (result.status !== "ready") {
    process.exitCode = 1;
  }
}

await main();
