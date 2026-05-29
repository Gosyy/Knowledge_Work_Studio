#!/usr/bin/env node
/**
 * KR-7H.6 in-memory PptxGenJS construction preflight.
 *
 * This script performs the first controlled PptxGenJS API-level smoke inside
 * the isolated renderer_worker package. It imports the pinned dependency and
 * constructs a presentation object in memory only. It intentionally does not
 * add slide content, map PresentationIR, call write/output APIs, write .pptx
 * files, run LibreOffice, create artifact/proof bundles, or claim production
 * renderer readiness.
 */

import PptxGenJS from "pptxgenjs";

const SCHEMA_VERSION = "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1";
const EXPECTED_PACKAGE_NAME = "pptxgenjs";
const EXPECTED_PACKAGE_VERSION = "4.0.1";

const BLOCKED_RUNTIME_ACTIONS = Object.freeze([
  "map_presentation_ir_to_slides",
  "add_slide_content",
  "generate_editable_pptx",
  "call_pptxgenjs_write_or_output_api",
  "write_pptx_file",
  "run_libreoffice_pdf_export",
  "render_slide_png_proofs",
  "write_artifact_bundle",
  "write_proof_bundle",
  "claim_visual_quality_score",
]);

function issue(code, message, target = null) {
  return { code, message, target };
}

function response(status, issues, construction = {}) {
  return {
    schema_version: SCHEMA_VERSION,
    phase: "KR-7H.6 in-memory PptxGenJS construction preflight",
    status,
    dependency_name: EXPECTED_PACKAGE_NAME,
    expected_dependency_version: EXPECTED_PACKAGE_VERSION,
    dependency_available: status === "ready",
    dependency_version: EXPECTED_PACKAGE_VERSION,
    module_default_export_type: typeof PptxGenJS,
    module_default_export_name: PptxGenJS && PptxGenJS.name ? String(PptxGenJS.name) : null,
    in_memory_preflight_implemented: true,
    presentation_object_created: Boolean(construction.presentationObjectCreated),
    presentation_object_type: construction.presentationObjectType || null,
    slide_count: Number.isInteger(construction.slideCount) ? construction.slideCount : null,
    slide_content_added: false,
    write_api_called: false,
    filesystem_output_written: false,
    renderer_runtime_implemented: false,
    production_pptx_output_implemented: false,
    pptx_generation_executed: false,
    artifact_bundle_produced: false,
    proof_bundle_produced: false,
    output_mode: "in_memory_construction_preflight_only",
    blocked_runtime_actions: [...BLOCKED_RUNTIME_ACTIONS],
    non_goals: [
      "no_pptx_generation",
      "no_presentation_ir_mapping",
      "no_slide_content_generation",
      "no_pptxgenjs_write_or_output_calls",
      "no_filesystem_output",
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

async function checkInMemoryConstruction() {
  const issues = [];
  if (typeof PptxGenJS !== "function") {
    return response("blocked", [issue("pptxgenjs_default_export_unexpected", "PptxGenJS default export must be a constructor function for in-memory preflight.", EXPECTED_PACKAGE_NAME)]);
  }

  let presentation;
  try {
    presentation = new PptxGenJS();
  } catch (error) {
    issues.push(issue("pptxgenjs_construction_failed", `Could not construct in-memory PptxGenJS presentation object: ${error.message}`, EXPECTED_PACKAGE_NAME));
  }

  let slideCount = null;
  let presentationObjectType = null;
  if (presentation) {
    presentationObjectType = presentation.constructor && presentation.constructor.name ? String(presentation.constructor.name) : typeof presentation;
    if (Array.isArray(presentation._slides)) {
      slideCount = presentation._slides.length;
    } else if (Array.isArray(presentation.slides)) {
      slideCount = presentation.slides.length;
    } else {
      issues.push(issue("pptxgenjs_slide_collection_unexpected", "Constructed presentation object does not expose a recognized in-memory slide collection.", EXPECTED_PACKAGE_NAME));
    }
    if (slideCount !== 0) {
      issues.push(issue("pptxgenjs_in_memory_slide_count_unexpected", `In-memory construction preflight must not add slides; got ${slideCount}.`, EXPECTED_PACKAGE_NAME));
    }
    for (const method of ["writeFile", "write", "writeFileToBrowser", "stream"]) {
      if (method in presentation && typeof presentation[method] !== "function") {
        issues.push(issue("pptxgenjs_write_api_shape_unexpected", `Expected ${method} to be a function when present.`, method));
      }
    }
  }

  const construction = {
    presentationObjectCreated: Boolean(presentation),
    presentationObjectType,
    slideCount,
  };
  return response(issues.length === 0 ? "ready" : "blocked", issues, construction);
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
  console.log("Usage: node renderer_worker/kw_renderer_worker_pptxgenjs_in_memory_preflight.mjs [--json]\n\nConstructs a PptxGenJS presentation object in memory only. Does not write PPTX, add slide content, run LibreOffice, or write artifacts.");
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

  const result = await checkInMemoryConstruction();
  console.log(JSON.stringify(result, null, 2));
  if (result.status !== "ready") {
    process.exitCode = 1;
  }
}

await main();
