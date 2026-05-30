#!/usr/bin/env node
/**
 * KR-7H.10 persistent PPTX artifact bundle + render report contract.
 *
 * This script accepts either a KR-7H.2 dry-run report or a renderer-worker
 * input payload, maps only minimal title/body text fields into a controlled
 * persistent PPTX artifact bundle directory, writes a deterministic render
 * report JSON, verifies both files, and returns a JSON report. It intentionally
 * does not run LibreOffice, create proof bundles, perform visual QA, map
 * charts/tables/images, or claim production-quality renderer output.
 */

import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import PptxGenJS from "pptxgenjs";

const SCHEMA_VERSION = "presentation_renderer_worker_pptx_artifact_bundle.v1";
const RENDER_REPORT_SCHEMA_VERSION = "presentation_renderer_worker_render_report.v1";
const DRY_RUN_SCHEMA_VERSION = "presentation_renderer_worker_dry_run.v1";
const RENDERER_INPUT_SCHEMA_VERSION = "presentation_renderer_worker_input.v1";
const EXPECTED_PACKAGE_NAME = "pptxgenjs";
const EXPECTED_PACKAGE_VERSION = "4.0.1";
const ARTIFACT_BASENAME = "kr7h10-minimal-ir-rendered.pptx";
const RENDER_REPORT_BASENAME = "kr7h10-render-report.json";
const MAX_TEXT_LENGTH = 220;

const BLOCKED_RUNTIME_ACTIONS = Object.freeze([
  "run_libreoffice_pdf_export",
  "render_slide_png_proofs",
  "write_proof_bundle",
  "claim_visual_quality_score",
  "map_charts_tables_images",
  "run_professional_layout_engine",
  "use_arbitrary_prompt_passthrough",
  "use_frontend_package_dependency",
  "invoke_gigachat_runtime",
]);

function issue(code, message, target = null) {
  return { code, message, target };
}

function baseResponse(status, issues, bundle = {}) {
  return {
    schema_version: SCHEMA_VERSION,
    phase: "KR-7H.10 persistent PPTX artifact bundle + render report contract",
    status,
    dependency_name: EXPECTED_PACKAGE_NAME,
    expected_dependency_version: EXPECTED_PACKAGE_VERSION,
    dependency_available: status === "ready",
    dependency_version: EXPECTED_PACKAGE_VERSION,
    module_default_export_type: typeof PptxGenJS,
    renderer_input_schema_version: RENDERER_INPUT_SCHEMA_VERSION,
    input_schema_version: bundle.inputSchemaVersion ?? null,
    input_status: bundle.inputStatus ?? null,
    render_report_schema_version: RENDER_REPORT_SCHEMA_VERSION,
    artifact_bundle_schema_version: SCHEMA_VERSION,
    pptx_artifact_basename: ARTIFACT_BASENAME,
    render_report_basename: RENDER_REPORT_BASENAME,
    output_directory: bundle.outputDirectory ?? null,
    output_directory_created: Boolean(bundle.outputDirectoryCreated),
    output_directory_exists: Boolean(bundle.outputDirectoryExists),
    output_directory_cleanup_requested: Boolean(bundle.outputDirectoryCleanupRequested),
    output_directory_cleanup_performed: Boolean(bundle.outputDirectoryCleanupPerformed),
    artifact_bundle_produced: Boolean(bundle.artifactBundleProduced),
    artifact_bundle_verified: Boolean(bundle.artifactBundleVerified),
    persistent_artifact_written: Boolean(bundle.persistentArtifactWritten),
    persistent_artifact_exists: Boolean(bundle.persistentArtifactExists),
    persistent_artifact_size_bytes: Number.isInteger(bundle.persistentArtifactSizeBytes) ? bundle.persistentArtifactSizeBytes : null,
    persistent_artifact_file_size_nonzero: Boolean(bundle.persistentArtifactFileSizeNonzero),
    render_report_written: Boolean(bundle.renderReportWritten),
    render_report_exists: Boolean(bundle.renderReportExists),
    render_report_size_bytes: Number.isInteger(bundle.renderReportSizeBytes) ? bundle.renderReportSizeBytes : null,
    render_report_file_size_nonzero: Boolean(bundle.renderReportFileSizeNonzero),
    render_report_deterministic: Boolean(bundle.renderReportDeterministic),
    mapped_fields: ["title", "body"],
    mapped_block_types: ["text"],
    mapped_slide_ids: bundle.mappedSlideIds ?? [],
    mapped_slide_count: Number.isInteger(bundle.mappedSlideCount) ? bundle.mappedSlideCount : 0,
    title_body_mapping_implemented: true,
    presentation_ir_mapping_implemented: true,
    chart_mapping_implemented: false,
    table_mapping_implemented: false,
    image_mapping_implemented: false,
    theme_mapping_implemented: false,
    professional_layout_engine_implemented: false,
    user_prompt_passthrough_allowed: false,
    production_pptx_output_implemented: false,
    renderer_runtime_implemented: false,
    filesystem_output_written: true,
    proof_bundle_produced: false,
    libreoffice_executed: false,
    visual_qa_executed: false,
    output_mode: "persistent_pptx_artifact_bundle_and_render_report_contract_only",
    blocked_runtime_actions: [...BLOCKED_RUNTIME_ACTIONS],
    non_goals: [
      "no_libreoffice_execution",
      "no_pdf_png_proof_generation",
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
    request_id: "kr7h10_fixture",
    renderer_runtime_implemented: false,
    artifact_bundle_produced: false,
    proof_bundle_produced: false,
    production_pptx_output_implemented: false,
    presentation_ir: {
      schema_version: "presentation_ir.v1",
      deck: {
        presentation_id: "kr7h10_fixture_deck",
        title: "KR-7H.10 Renderer Worker Artifact Bundle Smoke",
        objective: "Minimal persistent PPTX artifact bundle and render report contract",
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
          title: "Renderer Worker Artifact Bundle Smoke",
          takeaway: "This persistent artifact bundle maps only deterministic title and body text.",
          blocks: [],
          visual_plan: { layout_family: "title_body", requires_chart: false, requires_image: false },
        },
        {
          slide_id: "s002",
          slide_number: 2,
          role: "body",
          title: "Render Report Contract",
          takeaway: "The render report records metadata without LibreOffice proof or visual QA.",
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
    return { rendererInput: null, issues: [issue("input_must_be_object", "Renderer artifact bundle input must be a JSON object.", null)] };
  }
  if (payload.schema_version === DRY_RUN_SCHEMA_VERSION) {
    if (payload.status !== "ready") {
      return { rendererInput: null, issues: [issue("dry_run_not_ready", "KR-7H.10 requires a ready KR-7H.2 dry-run report.", "status")] };
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
    return [issue("renderer_input_missing", "Renderer input payload is required for KR-7H.10 artifact bundle smoke.", "renderer_input")];
  }
  if (rendererInput.schema_version !== RENDERER_INPUT_SCHEMA_VERSION) {
    issues.push(issue("renderer_input_schema_unsupported", `Renderer input schema_version must be ${RENDERER_INPUT_SCHEMA_VERSION}.`, "renderer_input.schema_version"));
  }
  if (rendererInput.status !== "ready") {
    issues.push(issue("renderer_input_not_ready", "Renderer input status must be ready for artifact bundle smoke.", "renderer_input.status"));
  }
  for (const [key, label] of [
    ["renderer_runtime_implemented", "renderer runtime"],
    ["production_pptx_output_implemented", "production PPTX output"],
    ["artifact_bundle_produced", "artifact bundle"],
    ["proof_bundle_produced", "proof bundle"],
  ]) {
    if (rendererInput[key] === true) {
      issues.push(issue("renderer_input_runtime_or_bundle_claim_not_allowed", `Renderer input must not already claim ${label} before KR-7H.10 smoke.`, `renderer_input.${key}`));
    }
  }
  const presentationIR = rendererInput.presentation_ir;
  if (!presentationIR || typeof presentationIR !== "object" || Array.isArray(presentationIR)) {
    issues.push(issue("presentation_ir_missing", "Renderer input must contain presentation_ir object.", "renderer_input.presentation_ir"));
    return issues;
  }
  const slides = presentationIR.slides;
  if (!Array.isArray(slides) || slides.length < 2) {
    issues.push(issue("presentation_ir_needs_two_slides", "KR-7H.10 artifact bundle smoke requires at least two slides.", "presentation_ir.slides"));
    return issues;
  }
  slides.forEach((slide, index) => {
    const pathPrefix = `presentation_ir.slides[${index}]`;
    if (!slide || typeof slide !== "object" || Array.isArray(slide)) {
      issues.push(issue("slide_must_be_object", "Each slide must be an object for KR-7H.10 artifact bundle smoke.", pathPrefix));
      return;
    }
    if (!String(slide.slide_id || "").trim()) {
      issues.push(issue("slide_id_required", "Each slide needs a stable slide_id for render report metadata.", `${pathPrefix}.slide_id`));
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

function toMappedSlides(rendererInput) {
  const sourceSlides = rendererInput.presentation_ir.slides.slice(0, Math.min(3, rendererInput.presentation_ir.slides.length));
  return sourceSlides.map((slide, index) => ({
    slide_id: String(slide.slide_id || `slide_${index + 1}`),
    title: normalizeText(slide.title, `Slide ${index + 1}`),
    body: normalizeText(slide.takeaway || slide.body || slide.summary, "Minimal renderer worker artifact bundle smoke body."),
  }));
}

async function ensureDirectory(directory) {
  await fs.mkdir(directory, { recursive: true });
  const stat = await fs.stat(directory);
  return stat.isDirectory();
}

async function pathExists(candidate) {
  try {
    await fs.access(candidate);
    return true;
  } catch (_error) {
    return false;
  }
}

async function writeDeck(mappedSlides, outputPath) {
  const presentation = new PptxGenJS();
  presentation.layout = "LAYOUT_WIDE";
  presentation.author = "KW Studio Renderer Worker";
  presentation.subject = "KR-7H.10 persistent PPTX artifact bundle smoke";
  presentation.title = "KR-7H.10 Renderer Worker Artifact Bundle Smoke";
  presentation.company = "KW Studio";
  presentation.lang = "en-US";

  for (const mapped of mappedSlides) {
    const slide = presentation.addSlide();
    slide.background = { color: "FFFFFF" };
    slide.addText(mapped.title, { x: 0.7, y: 0.65, w: 11.7, h: 0.6, fontFace: "Arial", fontSize: 24, bold: true, color: "111827" });
    slide.addText(mapped.body, { x: 0.7, y: 1.55, w: 11.7, h: 1.4, fontFace: "Arial", fontSize: 15, color: "1F2937", breakLine: false, fit: "shrink" });
    slide.addNotes(`KR-7H.10 persistent PPTX artifact bundle smoke only. Source slide_id=${mapped.slide_id}`);
  }
  await presentation.writeFile({ fileName: outputPath });
  const stat = await fs.stat(outputPath);
  return { written: stat.isFile(), sizeBytes: stat.size, sizeNonzero: stat.size > 0 };
}

function deterministicRenderReport(rendererInput, mappedSlides, pptxInfo) {
  return {
    schema_version: RENDER_REPORT_SCHEMA_VERSION,
    phase: "KR-7H.10 persistent PPTX artifact bundle + render report contract",
    status: "ready",
    renderer_input_schema_version: RENDERER_INPUT_SCHEMA_VERSION,
    input_schema_version: rendererInput.schema_version,
    input_status: rendererInput.status,
    artifact_bundle_schema_version: SCHEMA_VERSION,
    pptx_artifact_basename: ARTIFACT_BASENAME,
    mapped_fields: ["title", "body"],
    mapped_block_types: ["text"],
    mapped_slide_ids: mappedSlides.map((slide) => slide.slide_id),
    mapped_slide_count: mappedSlides.length,
    pptx_artifact_size_bytes: pptxInfo.sizeBytes,
    pptx_artifact_file_size_nonzero: pptxInfo.sizeNonzero,
    persistent_artifact_written: true,
    artifact_bundle_produced: true,
    presentation_ir_mapping_implemented: true,
    title_body_mapping_implemented: true,
    chart_mapping_implemented: false,
    table_mapping_implemented: false,
    image_mapping_implemented: false,
    theme_mapping_implemented: false,
    professional_layout_engine_implemented: false,
    production_pptx_output_implemented: false,
    proof_bundle_produced: false,
    libreoffice_executed: false,
    visual_qa_executed: false,
    output_mode: "persistent_pptx_artifact_bundle_and_render_report_contract_only",
    quality_claims: [],
  };
}

async function writeJson(pathname, payload) {
  const text = `${JSON.stringify(payload, null, 2)}\n`;
  await fs.writeFile(pathname, text, "utf8");
  const stat = await fs.stat(pathname);
  return { written: stat.isFile(), sizeBytes: stat.size, sizeNonzero: stat.size > 0 };
}

async function runArtifactBundle(rendererInput, outputDir, cleanupOutput) {
  const issues = [];
  if (typeof PptxGenJS !== "function") {
    return baseResponse("blocked", [issue("pptxgenjs_default_export_unexpected", "PptxGenJS default export must be a constructor function for KR-7H.10 artifact bundle smoke.", EXPECTED_PACKAGE_NAME)]);
  }

  const validationIssues = validateRendererInput(rendererInput);
  if (validationIssues.length) {
    return baseResponse("blocked", validationIssues, {
      inputSchemaVersion: rendererInput?.schema_version ?? null,
      inputStatus: rendererInput?.status ?? null,
    });
  }

  const resolvedOutputDir = path.resolve(outputDir);
  const pptxPath = path.join(resolvedOutputDir, ARTIFACT_BASENAME);
  const renderReportPath = path.join(resolvedOutputDir, RENDER_REPORT_BASENAME);
  const mappedSlides = toMappedSlides(rendererInput);
  const bundle = {
    inputSchemaVersion: rendererInput.schema_version,
    inputStatus: rendererInput.status,
    outputDirectory: resolvedOutputDir,
    outputDirectoryCreated: false,
    outputDirectoryExists: false,
    outputDirectoryCleanupRequested: cleanupOutput,
    outputDirectoryCleanupPerformed: false,
    artifactBundleProduced: false,
    artifactBundleVerified: false,
    persistentArtifactWritten: false,
    persistentArtifactExists: false,
    persistentArtifactSizeBytes: null,
    persistentArtifactFileSizeNonzero: false,
    renderReportWritten: false,
    renderReportExists: false,
    renderReportSizeBytes: null,
    renderReportFileSizeNonzero: false,
    renderReportDeterministic: false,
    mappedSlideIds: mappedSlides.map((slide) => slide.slide_id),
    mappedSlideCount: mappedSlides.length,
  };

  try {
    bundle.outputDirectoryCreated = await ensureDirectory(resolvedOutputDir);
    bundle.outputDirectoryExists = await pathExists(resolvedOutputDir);
    if (!bundle.outputDirectoryCreated || !bundle.outputDirectoryExists) {
      issues.push(issue("output_directory_unavailable", "Controlled output directory must exist before writing KR-7H.10 artifacts.", resolvedOutputDir));
    }

    const pptx = await writeDeck(mappedSlides, pptxPath);
    bundle.persistentArtifactWritten = pptx.written;
    bundle.persistentArtifactSizeBytes = pptx.sizeBytes;
    bundle.persistentArtifactFileSizeNonzero = pptx.sizeNonzero;
    bundle.persistentArtifactExists = await pathExists(pptxPath);
    if (!pptx.written || !pptx.sizeNonzero || !bundle.persistentArtifactExists) {
      issues.push(issue("pptx_artifact_missing_or_empty", "Persistent PPTX artifact must exist and have non-zero size.", ARTIFACT_BASENAME));
    }

    const renderReport = deterministicRenderReport(rendererInput, mappedSlides, pptx);
    const renderReportInfo = await writeJson(renderReportPath, renderReport);
    bundle.renderReportWritten = renderReportInfo.written;
    bundle.renderReportSizeBytes = renderReportInfo.sizeBytes;
    bundle.renderReportFileSizeNonzero = renderReportInfo.sizeNonzero;
    bundle.renderReportExists = await pathExists(renderReportPath);
    bundle.renderReportDeterministic = renderReport.schema_version === RENDER_REPORT_SCHEMA_VERSION && renderReport.pptx_artifact_basename === ARTIFACT_BASENAME;
    if (!renderReportInfo.written || !renderReportInfo.sizeNonzero || !bundle.renderReportExists) {
      issues.push(issue("render_report_missing_or_empty", "Render report JSON must exist and have non-zero size.", RENDER_REPORT_BASENAME));
    }
    if (!bundle.renderReportDeterministic) {
      issues.push(issue("render_report_not_deterministic", "Render report metadata must be deterministic for KR-7H.10.", RENDER_REPORT_BASENAME));
    }

    bundle.artifactBundleProduced = bundle.persistentArtifactWritten && bundle.renderReportWritten;
    bundle.artifactBundleVerified = bundle.persistentArtifactExists && bundle.persistentArtifactFileSizeNonzero && bundle.renderReportExists && bundle.renderReportFileSizeNonzero;
  } catch (error) {
    issues.push(issue("artifact_bundle_smoke_failed", `Could not complete KR-7H.10 artifact bundle smoke: ${error.message}`, null));
  } finally {
    if (cleanupOutput) {
      try {
        await fs.rm(resolvedOutputDir, { recursive: true, force: true });
        bundle.outputDirectoryCleanupPerformed = !(await pathExists(resolvedOutputDir));
      } catch (error) {
        issues.push(issue("output_directory_cleanup_failed", `Could not cleanup KR-7H.10 output directory: ${error.message}`, resolvedOutputDir));
      }
      if (!bundle.outputDirectoryCleanupPerformed) {
        issues.push(issue("output_directory_cleanup_not_performed", "Requested output cleanup must remove the controlled output directory before returning ready.", resolvedOutputDir));
      }
    }
  }

  return baseResponse(issues.length === 0 ? "ready" : "blocked", issues, bundle);
}

function parseArgs(argv) {
  const args = { json: false, help: false, stdin: false, fixture: false, outputDir: null, cleanupOutput: false };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--json") {
      args.json = true;
    } else if (arg === "--stdin") {
      args.stdin = true;
    } else if (arg === "--fixture") {
      args.fixture = true;
    } else if (arg === "--output-dir") {
      index += 1;
      if (index >= argv.length) {
        throw new Error("--output-dir requires a path argument");
      }
      args.outputDir = argv[index];
    } else if (arg === "--cleanup-output") {
      args.cleanupOutput = true;
    } else if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
}

function printHelp() {
  console.log("Usage: node renderer_worker/kw_renderer_worker_pptx_artifact_bundle_smoke.mjs --json [--fixture|--stdin] --output-dir <dir> [--cleanup-output]\n\nRuns KR-7H.10 persistent PPTX artifact bundle + render report smoke. It maps only title/body text into a controlled output directory, writes a PPTX artifact and render_report.json, and does not run LibreOffice or visual QA.");
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

  if (!args.outputDir) {
    console.log(JSON.stringify(baseResponse("blocked", [issue("output_dir_required", "KR-7H.10 requires an explicit controlled --output-dir.", "--output-dir")]), null, 2));
    process.exitCode = 1;
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
  const result = issues.length ? baseResponse("blocked", issues) : await runArtifactBundle(rendererInput, args.outputDir, args.cleanupOutput);
  console.log(JSON.stringify(result, null, 2));
  if (result.status !== "ready") {
    process.exitCode = 1;
  }
}

await main();
