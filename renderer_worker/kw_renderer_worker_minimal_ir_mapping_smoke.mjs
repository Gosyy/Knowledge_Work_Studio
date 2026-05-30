#!/usr/bin/env node
/**
 * KR-7H.9 minimal PresentationIR mapping + temporary PPTX smoke.
 *
 * This script is the first controlled renderer mapping smoke. It accepts either
 * a KR-7H.2 dry-run report or a renderer-worker input payload, maps only
 * minimal title/body text fields into temporary single-slide and multi-slide
 * PPTX files, verifies non-zero file sizes, then deletes all temporary output
 * before returning a deterministic JSON report. It intentionally does not
 * persist artifacts, run LibreOffice, create proof bundles, map charts/tables/
 * images, use arbitrary prompt passthrough, or claim production renderer
 * readiness.
 */

import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import PptxGenJS from "pptxgenjs";

const SCHEMA_VERSION = "presentation_renderer_worker_minimal_ir_mapping_smoke.v1";
const DRY_RUN_SCHEMA_VERSION = "presentation_renderer_worker_dry_run.v1";
const RENDERER_INPUT_SCHEMA_VERSION = "presentation_renderer_worker_input.v1";
const EXPECTED_PACKAGE_NAME = "pptxgenjs";
const EXPECTED_PACKAGE_VERSION = "4.0.1";
const SINGLE_OUTPUT_BASENAME = "kr7h9-minimal-ir-single-slide-smoke.pptx";
const MULTI_OUTPUT_BASENAME = "kr7h9-minimal-ir-multi-slide-smoke.pptx";
const MAX_TEXT_LENGTH = 220;

const BLOCKED_RUNTIME_ACTIONS = Object.freeze([
  "persist_pptx_artifact",
  "run_libreoffice_pdf_export",
  "render_slide_png_proofs",
  "write_artifact_bundle",
  "write_proof_bundle",
  "claim_visual_quality_score",
  "map_charts_tables_images",
  "run_professional_layout_engine",
  "use_arbitrary_prompt_passthrough",
  "generate_user_visible_deck",
]);

function issue(code, message, target = null) {
  return { code, message, target };
}

function baseResponse(status, issues, smoke = {}) {
  return {
    schema_version: SCHEMA_VERSION,
    phase: "KR-7H.9 minimal PresentationIR mapping + single/multi-slide temporary PPTX smoke",
    status,
    dependency_name: EXPECTED_PACKAGE_NAME,
    expected_dependency_version: EXPECTED_PACKAGE_VERSION,
    dependency_available: status === "ready",
    dependency_version: EXPECTED_PACKAGE_VERSION,
    module_default_export_type: typeof PptxGenJS,
    module_default_export_name: PptxGenJS && PptxGenJS.name ? String(PptxGenJS.name) : null,
    minimal_ir_mapping_smoke_implemented: true,
    renderer_input_schema_version: RENDERER_INPUT_SCHEMA_VERSION,
    input_schema_version: smoke.inputSchemaVersion ?? null,
    input_status: smoke.inputStatus ?? null,
    mapped_fields: ["title", "body"],
    mapped_block_types: ["text"],
    mapped_slide_ids: smoke.mappedSlideIds ?? [],
    mapped_slide_count: Number.isInteger(smoke.mappedSlideCount) ? smoke.mappedSlideCount : 0,
    single_slide_smoke_executed: Boolean(smoke.singleSlideSmokeExecuted),
    multi_slide_smoke_executed: Boolean(smoke.multiSlideSmokeExecuted),
    single_slide_pptx_written: Boolean(smoke.singleSlidePptxWritten),
    single_slide_pptx_deleted: Boolean(smoke.singleSlidePptxDeleted),
    single_slide_file_size_bytes: Number.isInteger(smoke.singleSlideFileSizeBytes) ? smoke.singleSlideFileSizeBytes : null,
    single_slide_file_size_nonzero: Boolean(smoke.singleSlideFileSizeNonzero),
    multi_slide_pptx_written: Boolean(smoke.multiSlidePptxWritten),
    multi_slide_pptx_deleted: Boolean(smoke.multiSlidePptxDeleted),
    multi_slide_file_size_bytes: Number.isInteger(smoke.multiSlideFileSizeBytes) ? smoke.multiSlideFileSizeBytes : null,
    multi_slide_file_size_nonzero: Boolean(smoke.multiSlideFileSizeNonzero),
    temporary_directory_removed: Boolean(smoke.temporaryDirectoryRemoved),
    temporary_output_basenames: [SINGLE_OUTPUT_BASENAME, MULTI_OUTPUT_BASENAME],
    title_body_mapping_implemented: true,
    chart_mapping_implemented: false,
    table_mapping_implemented: false,
    image_mapping_implemented: false,
    theme_mapping_implemented: false,
    professional_layout_engine_implemented: false,
    user_prompt_passthrough_allowed: false,
    presentation_ir_mapping_implemented: true,
    production_pptx_output_implemented: false,
    renderer_runtime_implemented: false,
    persistent_artifact_written: false,
    filesystem_output_written: false,
    artifact_bundle_produced: false,
    proof_bundle_produced: false,
    libreoffice_executed: false,
    visual_qa_executed: false,
    output_mode: "temporary_minimal_ir_mapping_smoke_only",
    blocked_runtime_actions: [...BLOCKED_RUNTIME_ACTIONS],
    non_goals: [
      "no_production_pptx_generation",
      "no_persistent_pptx_artifact",
      "no_artifact_bundle_storage",
      "no_libreoffice_execution",
      "no_proof_bundle_generation",
      "no_visual_qa_scoring",
      "no_charts_tables_images_mapping",
      "no_professional_layout_engine",
      "no_frontend_package_changes",
      "no_gigachat_runtime_changes",
      "no_production_quality_output_claims",
    ],
    issues,
  };
}

function minimalRendererInputFixture() {
  return {
    schema_version: RENDERER_INPUT_SCHEMA_VERSION,
    status: "ready",
    request_id: "kr7h9_fixture",
    renderer_runtime_implemented: false,
    artifact_bundle_produced: false,
    proof_bundle_produced: false,
    production_pptx_output_implemented: false,
    presentation_ir: {
      schema_version: "presentation_ir.v1",
      deck: {
        presentation_id: "kr7h9_fixture_deck",
        title: "KR-7H.9 Renderer Worker Smoke",
        objective: "Minimal title and body mapping smoke",
        slide_count: 2,
      },
      quality_contract: {
        renderer_runtime_implemented: false,
        production_pptx_output_implemented: false,
        source_images_only: true,
      },
      slides: [
        {
          slide_id: "s001",
          slide_number: 1,
          role: "cover",
          title: "Renderer Worker Mapping Smoke",
          takeaway: "This temporary slide maps only deterministic title and body text.",
          blocks: [],
          visual_plan: { layout_family: "title_body", requires_chart: false, requires_image: false },
        },
        {
          slide_id: "s002",
          slide_number: 2,
          role: "body",
          title: "Second Smoke Slide",
          takeaway: "Multi-slide smoke verifies repeated minimal mapping without persistent artifacts.",
          blocks: [],
          visual_plan: { layout_family: "title_body", requires_chart: false, requires_image: false },
        },
      ],
    },
  };
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf8").trim();
}

function resolveRendererInput(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return { rendererInput: null, issues: [issue("input_must_be_object", "Renderer mapping smoke input must be a JSON object.", null)] };
  }
  if (payload.schema_version === DRY_RUN_SCHEMA_VERSION) {
    if (payload.status !== "ready") {
      return { rendererInput: null, issues: [issue("dry_run_not_ready", "KR-7H.9 requires a ready KR-7H.2 dry-run report.", "status")] };
    }
    if (payload.renderer_runtime_implemented === true || payload.artifact_bundle_produced === true || payload.proof_bundle_produced === true) {
      return { rendererInput: null, issues: [issue("dry_run_runtime_or_bundle_claim_not_allowed", "Dry-run input must not claim renderer runtime or bundle production.", null)] };
    }
    return { rendererInput: payload.renderer_input, issues: [] };
  }
  if (payload.schema_version === RENDERER_INPUT_SCHEMA_VERSION) {
    return { rendererInput: payload, issues: [] };
  }
  return {
    rendererInput: null,
    issues: [issue("unsupported_input_schema", `Expected ${DRY_RUN_SCHEMA_VERSION} or ${RENDERER_INPUT_SCHEMA_VERSION}.`, "schema_version")],
  };
}

function validateRendererInput(rendererInput) {
  const issues = [];
  if (!rendererInput || typeof rendererInput !== "object" || Array.isArray(rendererInput)) {
    return [issue("renderer_input_missing", "Renderer input payload is required for KR-7H.9 mapping smoke.", "renderer_input")];
  }
  if (rendererInput.schema_version !== RENDERER_INPUT_SCHEMA_VERSION) {
    issues.push(issue("renderer_input_schema_unsupported", `Renderer input schema_version must be ${RENDERER_INPUT_SCHEMA_VERSION}.`, "renderer_input.schema_version"));
  }
  if (rendererInput.status !== "ready") {
    issues.push(issue("renderer_input_not_ready", "Renderer input status must be ready for mapping smoke.", "renderer_input.status"));
  }
  for (const [key, label] of [
    ["renderer_runtime_implemented", "renderer runtime"],
    ["production_pptx_output_implemented", "production PPTX output"],
    ["artifact_bundle_produced", "artifact bundle"],
    ["proof_bundle_produced", "proof bundle"],
  ]) {
    if (rendererInput[key] === true) {
      issues.push(issue("renderer_input_runtime_or_bundle_claim_not_allowed", `Renderer input must not claim ${label} in KR-7H.9 smoke.`, `renderer_input.${key}`));
    }
  }
  const presentationIR = rendererInput.presentation_ir;
  if (!presentationIR || typeof presentationIR !== "object" || Array.isArray(presentationIR)) {
    issues.push(issue("presentation_ir_missing", "Renderer input must contain presentation_ir object.", "renderer_input.presentation_ir"));
    return issues;
  }
  const slides = presentationIR.slides;
  if (!Array.isArray(slides) || slides.length < 2) {
    issues.push(issue("presentation_ir_needs_two_slides", "KR-7H.9 smoke requires at least two slides to execute both single-slide and multi-slide temporary PPTX checks.", "presentation_ir.slides"));
    return issues;
  }
  slides.forEach((slide, index) => {
    const pathPrefix = `presentation_ir.slides[${index}]`;
    if (!slide || typeof slide !== "object" || Array.isArray(slide)) {
      issues.push(issue("slide_must_be_object", "Each slide must be an object for KR-7H.9 mapping smoke.", pathPrefix));
      return;
    }
    if (!String(slide.slide_id || "").trim()) {
      issues.push(issue("slide_id_required", "Each slide needs a stable slide_id for mapping smoke reporting.", `${pathPrefix}.slide_id`));
    }
    if (!String(slide.title || "").trim()) {
      issues.push(issue("slide_title_required", "Each mapped slide needs a title string.", `${pathPrefix}.title`));
    }
    const body = String(slide.takeaway || slide.body || slide.summary || "").trim();
    if (!body) {
      issues.push(issue("slide_body_required", "Each mapped slide needs takeaway/body text for minimal title/body mapping.", `${pathPrefix}.takeaway`));
    }
  });
  return issues;
}

function normalizeText(value, fallback) {
  const text = String(value || "").replace(/\s+/g, " ").trim() || fallback;
  if (text.length <= MAX_TEXT_LENGTH) {
    return text;
  }
  return `${text.slice(0, MAX_TEXT_LENGTH - 1)}…`;
}

function toMappedSlides(rendererInput, mode) {
  const sourceSlides = rendererInput.presentation_ir.slides;
  const selected = mode === "single" ? sourceSlides.slice(0, 1) : sourceSlides.slice(0, Math.min(3, sourceSlides.length));
  return selected.map((slide, index) => ({
    slide_id: String(slide.slide_id || `slide_${index + 1}`),
    title: normalizeText(slide.title, `Slide ${index + 1}`),
    body: normalizeText(slide.takeaway || slide.body || slide.summary, "Minimal renderer worker smoke body."),
  }));
}

async function pathExists(candidate) {
  try {
    await fs.access(candidate);
    return true;
  } catch (_error) {
    return false;
  }
}

async function writeTemporaryDeck(mappedSlides, outputPath) {
  const presentation = new PptxGenJS();
  presentation.layout = "LAYOUT_WIDE";
  for (const mapped of mappedSlides) {
    const slide = presentation.addSlide();
    slide.addText(mapped.title, { x: 0.7, y: 0.65, w: 11.7, h: 0.6, fontFace: "Arial", fontSize: 24, bold: true });
    slide.addText(mapped.body, { x: 0.7, y: 1.55, w: 11.7, h: 1.4, fontFace: "Arial", fontSize: 15, breakLine: false, fit: "shrink" });
    slide.addNotes(`KR-7H.9 minimal mapping smoke only. Source slide_id=${mapped.slide_id}`);
  }
  await presentation.writeFile({ fileName: outputPath });
  const stat = await fs.stat(outputPath);
  return { written: stat.isFile(), sizeBytes: stat.size, sizeNonzero: stat.size > 0 };
}

async function runMappingSmoke(rendererInput) {
  const issues = [];
  if (typeof PptxGenJS !== "function") {
    return baseResponse("blocked", [issue("pptxgenjs_default_export_unexpected", "PptxGenJS default export must be a constructor function for KR-7H.9 mapping smoke.", EXPECTED_PACKAGE_NAME)]);
  }

  const validationIssues = validateRendererInput(rendererInput);
  if (validationIssues.length) {
    return baseResponse("blocked", validationIssues, {
      inputSchemaVersion: rendererInput?.schema_version ?? null,
      inputStatus: rendererInput?.status ?? null,
    });
  }

  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "kw-kr7h9-minimal-ir-mapping-"));
  const singleOutputPath = path.join(tempDir, SINGLE_OUTPUT_BASENAME);
  const multiOutputPath = path.join(tempDir, MULTI_OUTPUT_BASENAME);
  const singleSlides = toMappedSlides(rendererInput, "single");
  const multiSlides = toMappedSlides(rendererInput, "multi");
  const smoke = {
    inputSchemaVersion: rendererInput.schema_version,
    inputStatus: rendererInput.status,
    mappedSlideIds: multiSlides.map((slide) => slide.slide_id),
    mappedSlideCount: multiSlides.length,
    singleSlideSmokeExecuted: false,
    multiSlideSmokeExecuted: false,
    singleSlidePptxWritten: false,
    singleSlidePptxDeleted: false,
    singleSlideFileSizeBytes: null,
    singleSlideFileSizeNonzero: false,
    multiSlidePptxWritten: false,
    multiSlidePptxDeleted: false,
    multiSlideFileSizeBytes: null,
    multiSlideFileSizeNonzero: false,
    temporaryDirectoryRemoved: false,
  };

  try {
    const single = await writeTemporaryDeck(singleSlides, singleOutputPath);
    smoke.singleSlideSmokeExecuted = true;
    smoke.singleSlidePptxWritten = single.written;
    smoke.singleSlideFileSizeBytes = single.sizeBytes;
    smoke.singleSlideFileSizeNonzero = single.sizeNonzero;
    if (!single.written || !single.sizeNonzero) {
      issues.push(issue("single_slide_output_missing_or_empty", "Single-slide temporary PPTX smoke output must exist and have non-zero size before cleanup.", SINGLE_OUTPUT_BASENAME));
    }

    const multi = await writeTemporaryDeck(multiSlides, multiOutputPath);
    smoke.multiSlideSmokeExecuted = true;
    smoke.multiSlidePptxWritten = multi.written;
    smoke.multiSlideFileSizeBytes = multi.sizeBytes;
    smoke.multiSlideFileSizeNonzero = multi.sizeNonzero;
    if (!multi.written || !multi.sizeNonzero) {
      issues.push(issue("multi_slide_output_missing_or_empty", "Multi-slide temporary PPTX smoke output must exist and have non-zero size before cleanup.", MULTI_OUTPUT_BASENAME));
    }
  } catch (error) {
    issues.push(issue("minimal_ir_mapping_smoke_failed", `Could not complete KR-7H.9 minimal mapping smoke: ${error.message}`, null));
  } finally {
    for (const [outputPath, label] of [[singleOutputPath, "single"], [multiOutputPath, "multi"]]) {
      try {
        await fs.rm(outputPath, { force: true });
        const deleted = !(await pathExists(outputPath));
        if (label === "single") {
          smoke.singleSlidePptxDeleted = deleted;
        } else {
          smoke.multiSlidePptxDeleted = deleted;
        }
      } catch (error) {
        issues.push(issue(`${label}_slide_output_cleanup_failed`, `Could not delete ${label}-slide temporary PPTX: ${error.message}`, path.basename(outputPath)));
      }
    }
    try {
      await fs.rm(tempDir, { recursive: true, force: true });
      smoke.temporaryDirectoryRemoved = !(await pathExists(tempDir));
    } catch (error) {
      issues.push(issue("temporary_directory_cleanup_failed", `Could not remove KR-7H.9 temporary smoke directory: ${error.message}`, null));
    }
  }

  if (!smoke.singleSlidePptxDeleted) {
    issues.push(issue("single_slide_output_not_deleted", "Single-slide temporary PPTX smoke output must be deleted before returning ready.", SINGLE_OUTPUT_BASENAME));
  }
  if (!smoke.multiSlidePptxDeleted) {
    issues.push(issue("multi_slide_output_not_deleted", "Multi-slide temporary PPTX smoke output must be deleted before returning ready.", MULTI_OUTPUT_BASENAME));
  }
  if (!smoke.temporaryDirectoryRemoved) {
    issues.push(issue("temporary_directory_not_removed", "KR-7H.9 temporary smoke directory must be removed before returning ready.", null));
  }

  return baseResponse(issues.length === 0 ? "ready" : "blocked", issues, smoke);
}

function parseArgs(argv) {
  const args = { json: false, help: false, stdin: false, fixture: false };
  for (const arg of argv) {
    if (arg === "--json") {
      args.json = true;
    } else if (arg === "--stdin") {
      args.stdin = true;
    } else if (arg === "--fixture") {
      args.fixture = true;
    } else if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
}

function printHelp() {
  console.log("Usage: node renderer_worker/kw_renderer_worker_minimal_ir_mapping_smoke.mjs [--json] [--fixture|--stdin]\n\nRuns KR-7H.9 minimal title/body mapping smoke. With --fixture it uses a deterministic renderer input fixture. With --stdin it reads a KR-7H.2 dry-run report or renderer-worker input JSON from stdin. It writes only temporary PPTX smoke files and deletes them before returning.");
}

async function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    console.log(JSON.stringify(baseResponse("blocked", [issue("invalid_cli_arguments", String(error.message), null)]), null, 2));
    process.exitCode = 2;
    return;
  }

  if (args.help) {
    printHelp();
    return;
  }

  let payload = minimalRendererInputFixture();
  if (args.stdin) {
    const input = await readStdin();
    try {
      payload = JSON.parse(input);
    } catch (error) {
      console.log(JSON.stringify(baseResponse("blocked", [issue("invalid_json_input", `Could not parse stdin JSON: ${error.message}`, null)]), null, 2));
      process.exitCode = 1;
      return;
    }
  }

  const { rendererInput, issues } = resolveRendererInput(payload);
  const result = issues.length ? baseResponse("blocked", issues) : await runMappingSmoke(rendererInput);
  console.log(JSON.stringify(result, null, 2));
  if (result.status !== "ready") {
    process.exitCode = 1;
  }
}

await main();
