#!/usr/bin/env node
/**
 * KR-7H.11 LibreOffice + pdftoppm proof bundle smoke.
 *
 * This controlled smoke builds on the KR-7H.10 persistent PPTX artifact bundle
 * path. It first asks the existing artifact-bundle smoke to write the PPTX and
 * render report into an explicit output directory, then fail-closed runs only
 * LibreOffice PDF export and pdftoppm PNG proof rendering. It writes a proof
 * bundle JSON with file evidence and keeps visual QA/scoring, production
 * renderer closure, and chart/table/image/theme/pro-layout mapping out of scope.
 */

import fs from "node:fs/promises";
import fsConstants from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

const SCHEMA_VERSION = "presentation_renderer_worker_libreoffice_proof_bundle.v1";
const ARTIFACT_SCHEMA_VERSION = "presentation_renderer_worker_pptx_artifact_bundle.v1";
const RENDER_REPORT_SCHEMA_VERSION = "presentation_renderer_worker_render_report.v1";
const DRY_RUN_SCHEMA_VERSION = "presentation_renderer_worker_dry_run.v1";
const RENDERER_INPUT_SCHEMA_VERSION = "presentation_renderer_worker_input.v1";
const ARTIFACT_SCRIPT_BASENAME = "kw_renderer_worker_pptx_artifact_bundle_smoke.mjs";
const ARTIFACT_BASENAME = "kr7h10-minimal-ir-rendered.pptx";
const RENDER_REPORT_BASENAME = "kr7h10-render-report.json";
const PROOF_BUNDLE_BASENAME = "kr7h11-proof-bundle.json";
const PDF_PROOF_BASENAME = "kr7h11-rendered-proof.pdf";
const PNG_PROOF_DIR_BASENAME = "kr7h11-png-proof";
const PROOF_DPI = 144;
const COMMAND_TIMEOUT_MS = 120000;

const BLOCKED_RUNTIME_ACTIONS = Object.freeze([
  "claim_visual_quality_score",
  "run_visual_qa_scoring",
  "map_charts_tables_images",
  "map_theme_brand_or_professional_layout",
  "use_arbitrary_prompt_passthrough",
  "use_frontend_package_dependency",
  "invoke_gigachat_runtime",
  "use_python_pptx_or_fake_renderer_as_proof",
]);

function issue(code, message, target = null) {
  return { code, message, target };
}

function baseResponse(status, issues, bundle = {}) {
  return {
    schema_version: SCHEMA_VERSION,
    phase: "KR-7H.11 LibreOffice proof bundle smoke",
    status,
    renderer_input_schema_version: RENDERER_INPUT_SCHEMA_VERSION,
    input_schema_version: bundle.inputSchemaVersion ?? null,
    input_status: bundle.inputStatus ?? null,
    artifact_bundle_schema_version: ARTIFACT_SCHEMA_VERSION,
    render_report_schema_version: RENDER_REPORT_SCHEMA_VERSION,
    proof_bundle_schema_version: SCHEMA_VERSION,
    output_directory: bundle.outputDirectory ?? null,
    output_directory_created: Boolean(bundle.outputDirectoryCreated),
    output_directory_exists: Boolean(bundle.outputDirectoryExists),
    output_directory_cleanup_requested: Boolean(bundle.outputDirectoryCleanupRequested),
    output_directory_cleanup_performed: Boolean(bundle.outputDirectoryCleanupPerformed),
    artifact_bundle_produced: Boolean(bundle.artifactBundleProduced),
    artifact_bundle_verified: Boolean(bundle.artifactBundleVerified),
    upstream_artifact_bundle_status: bundle.upstreamArtifactBundleStatus ?? null,
    pptx_artifact_basename: ARTIFACT_BASENAME,
    pptx_artifact_exists: Boolean(bundle.pptxArtifactExists),
    pptx_artifact_size_bytes: Number.isInteger(bundle.pptxArtifactSizeBytes) ? bundle.pptxArtifactSizeBytes : null,
    pptx_artifact_sha256: bundle.pptxArtifactSha256 ?? null,
    render_report_basename: RENDER_REPORT_BASENAME,
    render_report_exists: Boolean(bundle.renderReportExists),
    render_report_size_bytes: Number.isInteger(bundle.renderReportSizeBytes) ? bundle.renderReportSizeBytes : null,
    proof_bundle_basename: PROOF_BUNDLE_BASENAME,
    proof_bundle_written: Boolean(bundle.proofBundleWritten),
    proof_bundle_exists: Boolean(bundle.proofBundleExists),
    proof_bundle_size_bytes: Number.isInteger(bundle.proofBundleSizeBytes) ? bundle.proofBundleSizeBytes : null,
    proof_bundle_file_size_nonzero: Boolean(bundle.proofBundleFileSizeNonzero),
    proof_bundle_produced: Boolean(bundle.proofBundleProduced),
    proof_bundle_verified: Boolean(bundle.proofBundleVerified),
    proof_bundle_deterministic: Boolean(bundle.proofBundleDeterministic),
    libreoffice_required: true,
    pdftoppm_required: true,
    libreoffice_available: Boolean(bundle.libreofficeAvailable),
    pdftoppm_available: Boolean(bundle.pdftoppmAvailable),
    libreoffice_executed: Boolean(bundle.libreofficeExecuted),
    pdftoppm_executed: Boolean(bundle.pdftoppmExecuted),
    pdf_proof_basename: PDF_PROOF_BASENAME,
    pdf_proof_written: Boolean(bundle.pdfProofWritten),
    pdf_proof_exists: Boolean(bundle.pdfProofExists),
    pdf_proof_size_bytes: Number.isInteger(bundle.pdfProofSizeBytes) ? bundle.pdfProofSizeBytes : null,
    pdf_proof_file_size_nonzero: Boolean(bundle.pdfProofFileSizeNonzero),
    pdf_proof_sha256: bundle.pdfProofSha256 ?? null,
    png_proof_directory: PNG_PROOF_DIR_BASENAME,
    png_proofs_written: Boolean(bundle.pngProofsWritten),
    png_proof_count: Number.isInteger(bundle.pngProofCount) ? bundle.pngProofCount : 0,
    png_proof_basenames: bundle.pngProofBasenames ?? [],
    png_proof_size_bytes: bundle.pngProofSizeBytes ?? [],
    png_proof_sha256: bundle.pngProofSha256 ?? [],
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
    visual_qa_executed: false,
    visual_quality_score: null,
    fake_proof_used: false,
    fallback_renderer_used: false,
    python_pptx_proof_used: false,
    output_mode: "persistent_pptx_artifact_bundle_plus_libreoffice_pdftoppm_proof_smoke_only",
    blocked_runtime_actions: [...BLOCKED_RUNTIME_ACTIONS],
    non_goals: [
      "no_visual_qa_scoring",
      "no_charts_tables_images_mapping",
      "no_theme_brand_or_professional_layout_mapping",
      "no_frontend_package_changes",
      "no_gigachat_runtime_changes",
      "no_production_quality_output_claims",
      "no_fallback_renderer_as_success",
      "no_fake_proof_artifacts",
    ],
    issues,
  };
}

function minimalRendererInputFixture() {
  return {
    schema_version: RENDERER_INPUT_SCHEMA_VERSION,
    status: "ready",
    request_id: "kr7h11_fixture",
    renderer_runtime_implemented: false,
    artifact_bundle_produced: false,
    proof_bundle_produced: false,
    production_pptx_output_implemented: false,
    presentation_ir: {
      schema_version: "presentation_ir.v1",
      deck: {
        presentation_id: "kr7h11_fixture_deck",
        title: "KR-7H.11 Renderer Worker Proof Bundle Smoke",
        objective: "Controlled LibreOffice and pdftoppm proof bundle smoke",
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
          title: "LibreOffice Proof Bundle Smoke",
          takeaway: "This proof bundle renders the existing controlled PPTX artifact to PDF and PNG proof files.",
          blocks: [],
          visual_plan: { layout_family: "title_body", requires_chart: false, requires_image: false },
        },
        {
          slide_id: "s002",
          slide_number: 2,
          role: "body",
          title: "Fail-Closed Proof Evidence",
          takeaway: "The smoke fails closed if LibreOffice, pdftoppm, the PDF, or the PNG proof files are missing.",
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

async function pathExists(candidate) {
  try {
    await fs.access(candidate);
    return true;
  } catch (_error) {
    return false;
  }
}

async function fileInfo(candidate) {
  if (!(await pathExists(candidate))) {
    return { exists: false, sizeBytes: null, sizeNonzero: false, sha256: null };
  }
  const stat = await fs.stat(candidate);
  if (!stat.isFile()) {
    return { exists: false, sizeBytes: null, sizeNonzero: false, sha256: null };
  }
  const bytes = await fs.readFile(candidate);
  return {
    exists: true,
    sizeBytes: stat.size,
    sizeNonzero: stat.size > 0,
    sha256: `sha256:${createHash("sha256").update(bytes).digest("hex")}`,
  };
}

async function ensureDirectory(directory) {
  await fs.mkdir(directory, { recursive: true });
  const stat = await fs.stat(directory);
  return stat.isDirectory();
}

async function removeIfExists(candidate) {
  await fs.rm(candidate, { recursive: true, force: true });
}

async function isExecutable(candidate) {
  if (!candidate) {
    return false;
  }
  try {
    const stat = await fs.stat(candidate);
    if (!stat.isFile()) {
      return false;
    }
    await fs.access(candidate, fsConstants.constants.X_OK);
    return true;
  } catch (_error) {
    return false;
  }
}

function executableNames(name) {
  if (process.platform !== "win32") {
    return [name];
  }
  const lower = name.toLowerCase();
  return lower.endsWith(".exe") ? [name] : [name, `${name}.exe`];
}

async function resolveExecutable({ explicit, envValue, candidates, label }) {
  const requested = explicit || envValue || null;
  if (requested) {
    const resolved = path.resolve(requested);
    if (await isExecutable(resolved)) {
      return { available: true, path: resolved, issue: null };
    }
    return {
      available: false,
      path: resolved,
      issue: issue(`${label}_unavailable`, `${label} executable is required and was not executable.`, resolved),
    };
  }
  const pathDirs = String(process.env.PATH || "").split(path.delimiter).filter(Boolean);
  for (const dir of pathDirs) {
    for (const candidate of candidates.flatMap(executableNames)) {
      const resolved = path.join(dir, candidate);
      if (await isExecutable(resolved)) {
        return { available: true, path: resolved, issue: null };
      }
    }
  }
  return {
    available: false,
    path: null,
    issue: issue(`${label}_unavailable`, `${label} executable is required but was not found on PATH.`, candidates.join("|")),
  };
}

function runCommand(command, args, options = {}) {
  const completed = spawnSync(command, args, {
    cwd: options.cwd,
    input: options.input,
    env: options.env,
    encoding: "utf8",
    timeout: options.timeoutMs ?? COMMAND_TIMEOUT_MS,
    maxBuffer: 1024 * 1024 * 10,
  });
  const output = [completed.stdout || "", completed.stderr || "", completed.error ? String(completed.error.message) : ""].filter(Boolean).join("");
  return {
    returncode: typeof completed.status === "number" ? completed.status : 1,
    stdout: output,
    timedOut: completed.error?.code === "ETIMEDOUT",
  };
}

async function runArtifactBundle({ workerRoot, payload, outputDir, cleanupOutput }) {
  const script = path.join(workerRoot, ARTIFACT_SCRIPT_BASENAME);
  const args = [script, "--json", "--output-dir", outputDir];
  let input = null;
  if (payload === null) {
    args.push("--fixture");
  } else {
    args.push("--stdin");
    input = JSON.stringify(payload);
  }
  if (cleanupOutput) {
    args.push("--cleanup-output");
  }
  const completed = runCommand(process.execPath, args, { cwd: workerRoot, input });
  let parsed = null;
  try {
    parsed = JSON.parse(completed.stdout);
  } catch (_error) {
    parsed = null;
  }
  return { completed, parsed };
}

async function findPdfCandidates(...roots) {
  const out = [];
  const seen = new Set();
  async function walk(root) {
    if (!(await pathExists(root))) {
      return;
    }
    const entries = await fs.readdir(root, { withFileTypes: true });
    for (const entry of entries) {
      const candidate = path.join(root, entry.name);
      if (entry.isDirectory()) {
        await walk(candidate);
      } else if (entry.isFile() && entry.name.toLowerCase().endsWith(".pdf")) {
        const resolved = path.resolve(candidate);
        if (!seen.has(resolved)) {
          seen.add(resolved);
          const stat = await fs.stat(candidate);
          out.push({ path: candidate, mtimeMs: stat.mtimeMs });
        }
      }
    }
  }
  for (const root of roots) {
    await walk(root);
  }
  return out.sort((a, b) => b.mtimeMs - a.mtimeMs || a.path.localeCompare(b.path)).map((item) => item.path);
}

async function runLibreOfficePdfConvert({ soffice, pptxPath, pdfDir, workDir, profileDir }) {
  const profileUri = pathToFileURL(path.resolve(profileDir)).href;
  const localInput = path.join(workDir, "input.pptx");
  await fs.copyFile(pptxPath, localInput);
  const baseFlags = [
    soffice,
    `-env:UserInstallation=${profileUri}`,
    "--headless",
    "--invisible",
    "--nodefault",
    "--nofirststartwizard",
    "--nolockcheck",
    "--norestore",
  ];
  const minimalFlags = [soffice, "--headless"];
  const attempts = [
    ["profile_relative_input_workdir_pdf", [...baseFlags, "--convert-to", "pdf", "--outdir", workDir, "input.pptx"], workDir],
    ["profile_relative_input_workdir_impress_pdf", [...baseFlags, "--convert-to", "pdf:impress_pdf_Export", "--outdir", workDir, "input.pptx"], workDir],
    ["minimal_relative_input_workdir_pdf", [...minimalFlags, "--convert-to", "pdf", "--outdir", workDir, "input.pptx"], workDir],
    ["profile_relative_input_default_outdir", [...baseFlags, "--convert-to", "pdf", "input.pptx"], workDir],
    ["profile_absolute_input_pdfdir_pdf", [...baseFlags, "--convert-to", "pdf", "--outdir", pdfDir, localInput], workDir],
    ["profile_original_input_pdfdir_pdf", [...baseFlags, "--convert-to", "pdf", "--outdir", pdfDir, pptxPath], workDir],
    ["minimal_absolute_input_pdfdir_pdf", [...minimalFlags, "--convert-to", "pdf", "--outdir", pdfDir, localInput], workDir],
  ];
  const transcripts = [];
  let last = { returncode: 1, stdout: "LibreOffice was not executed." };
  for (const [label, command, cwd] of attempts) {
    const before = new Set((await findPdfCandidates(pdfDir, workDir)).map((candidate) => path.resolve(candidate)));
    const env = { ...process.env, HOME: profileDir, TMPDIR: workDir, SAL_USE_VCLPLUGIN: process.env.SAL_USE_VCLPLUGIN || "svp" };
    const [cmd, ...args] = command;
    last = runCommand(cmd, args, { cwd, env });
    const after = await findPdfCandidates(pdfDir, workDir);
    const newCandidates = after.filter((candidate) => !before.has(path.resolve(candidate)));
    transcripts.push([
      `attempt=${label}`,
      `returncode=${last.returncode}`,
      `stdout_tail=${last.stdout.slice(-1200)}`,
      `pdf_candidates=${after.join(", ")}`,
    ].join("\n"));
    if (last.returncode === 0 && (newCandidates.length > 0 || after.length > 0)) {
      return { returncode: 0, stdout: transcripts.join("\n--- libreoffice-attempt ---\n"), pdfPath: newCandidates[0] || after[0] };
    }
  }
  return { returncode: last.returncode, stdout: transcripts.join("\n--- libreoffice-attempt ---\n"), pdfPath: null };
}

async function runProofRender({ soffice, pdftoppm, pptxPath, outputDir }) {
  const tmpParent = path.join(outputDir, ".kw-kr7h11-office-tmp");
  await ensureDirectory(tmpParent);
  const tmp = await fs.mkdtemp(path.join(tmpParent, "proof-"));
  try {
    const workDir = path.join(tmp, "work");
    const pdfDir = path.join(tmp, "pdf");
    const rawPngDir = path.join(tmp, "png");
    const profileDir = path.join(tmp, "lo-profile");
    for (const dir of [workDir, pdfDir, rawPngDir, profileDir]) {
      await ensureDirectory(dir);
    }
    const convert = await runLibreOfficePdfConvert({ soffice, pptxPath, pdfDir, workDir, profileDir });
    if (convert.returncode !== 0 || !convert.pdfPath) {
      return { ok: false, issue: issue("libreoffice_pdf_export_failed", `LibreOffice PDF export failed or produced no PDF: ${convert.stdout.slice(-1600)}`, PDF_PROOF_BASENAME) };
    }
    const pdfOut = path.join(outputDir, PDF_PROOF_BASENAME);
    await fs.copyFile(convert.pdfPath, pdfOut);
    const pdfInfo = await fileInfo(pdfOut);
    if (!pdfInfo.exists || !pdfInfo.sizeNonzero) {
      return { ok: false, issue: issue("pdf_proof_missing_or_empty", "LibreOffice PDF export must produce a non-empty PDF proof.", PDF_PROOF_BASENAME) };
    }

    const rawBase = path.join(rawPngDir, "slide");
    const render = runCommand(pdftoppm, ["-png", "-r", String(PROOF_DPI), pdfOut, rawBase]);
    if (render.returncode !== 0) {
      return { ok: false, issue: issue("pdftoppm_png_render_failed", `pdftoppm failed: ${render.stdout.slice(-1600)}`, PNG_PROOF_DIR_BASENAME), pdfInfo };
    }
    const rawPngs = (await fs.readdir(rawPngDir))
      .filter((name) => name.toLowerCase().endsWith(".png"))
      .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))
      .map((name) => path.join(rawPngDir, name));
    if (rawPngs.length === 0) {
      return { ok: false, issue: issue("png_proofs_missing", "pdftoppm must produce at least one PNG proof file.", PNG_PROOF_DIR_BASENAME), pdfInfo };
    }
    const pngOutDir = path.join(outputDir, PNG_PROOF_DIR_BASENAME);
    await removeIfExists(pngOutDir);
    await ensureDirectory(pngOutDir);
    const pngBasenames = [];
    const pngSizeBytes = [];
    const pngSha256 = [];
    for (let index = 0; index < rawPngs.length; index += 1) {
      const basename = `slide_${String(index + 1).padStart(2, "0")}.png`;
      const dst = path.join(pngOutDir, basename);
      await fs.copyFile(rawPngs[index], dst);
      const info = await fileInfo(dst);
      if (!info.exists || !info.sizeNonzero) {
        return { ok: false, issue: issue("png_proof_missing_or_empty", "Every PNG proof must exist and have non-zero size.", basename), pdfInfo };
      }
      pngBasenames.push(basename);
      pngSizeBytes.push(info.sizeBytes);
      pngSha256.push(info.sha256);
    }
    return { ok: true, pdfInfo, pngBasenames, pngSizeBytes, pngSha256 };
  } finally {
    await removeIfExists(tmpParent);
  }
}

function resolvePayloadInfo(payload) {
  if (payload === null) {
    return { inputSchemaVersion: RENDERER_INPUT_SCHEMA_VERSION, inputStatus: "ready" };
  }
  if (payload && typeof payload === "object" && payload.schema_version === DRY_RUN_SCHEMA_VERSION) {
    return { inputSchemaVersion: payload.schema_version, inputStatus: payload.status ?? null };
  }
  if (payload && typeof payload === "object") {
    return { inputSchemaVersion: payload.schema_version ?? null, inputStatus: payload.status ?? null };
  }
  return { inputSchemaVersion: null, inputStatus: null };
}

async function writeJson(pathname, payload) {
  const text = `${JSON.stringify(payload, null, 2)}\n`;
  await fs.writeFile(pathname, text, "utf8");
  return fileInfo(pathname);
}

async function finalizeProofBundleResponse(status, issues, bundle, cleanupOutput, resolvedOutputDir) {
  if (cleanupOutput) {
    try {
      await removeIfExists(resolvedOutputDir);
      bundle.outputDirectoryCleanupPerformed = !(await pathExists(resolvedOutputDir));
    } catch (_error) {
      bundle.outputDirectoryCleanupPerformed = false;
      issues.push(issue("output_directory_cleanup_failed", "Requested output cleanup failed for KR-7H.11 proof bundle smoke.", resolvedOutputDir));
      status = "blocked";
    }
  }
  return baseResponse(status, issues, bundle);
}

async function runProofBundle({ workerRoot, payload, outputDir, cleanupOutput, sofficeBin, pdftoppmBin }) {
  const issues = [];
  const resolvedOutputDir = path.resolve(outputDir);
  const inputInfo = resolvePayloadInfo(payload);
  const bundle = {
    inputSchemaVersion: inputInfo.inputSchemaVersion,
    inputStatus: inputInfo.inputStatus,
    outputDirectory: resolvedOutputDir,
    outputDirectoryCreated: false,
    outputDirectoryExists: false,
    outputDirectoryCleanupRequested: cleanupOutput,
    outputDirectoryCleanupPerformed: false,
    artifactBundleProduced: false,
    artifactBundleVerified: false,
    upstreamArtifactBundleStatus: null,
    pptxArtifactExists: false,
    pptxArtifactSizeBytes: null,
    pptxArtifactSha256: null,
    renderReportExists: false,
    renderReportSizeBytes: null,
    proofBundleWritten: false,
    proofBundleExists: false,
    proofBundleSizeBytes: null,
    proofBundleFileSizeNonzero: false,
    proofBundleProduced: false,
    proofBundleVerified: false,
    proofBundleDeterministic: false,
    libreofficeAvailable: false,
    pdftoppmAvailable: false,
    libreofficeExecuted: false,
    pdftoppmExecuted: false,
    pdfProofWritten: false,
    pdfProofExists: false,
    pdfProofSizeBytes: null,
    pdfProofFileSizeNonzero: false,
    pdfProofSha256: null,
    pngProofsWritten: false,
    pngProofCount: 0,
    pngProofBasenames: [],
    pngProofSizeBytes: [],
    pngProofSha256: [],
    mappedSlideIds: [],
    mappedSlideCount: 0,
  };

  try {
    const soffice = await resolveExecutable({
      explicit: sofficeBin,
      envValue: process.env.KWS_LIBREOFFICE_BIN || null,
      candidates: ["soffice", "libreoffice"],
      label: "libreoffice",
    });
    const pdftoppm = await resolveExecutable({
      explicit: pdftoppmBin,
      envValue: process.env.KWS_PDFTOPPM_BIN || null,
      candidates: ["pdftoppm"],
      label: "pdftoppm",
    });
    bundle.libreofficeAvailable = soffice.available;
    bundle.pdftoppmAvailable = pdftoppm.available;
    if (soffice.issue) {
      issues.push(soffice.issue);
    }
    if (pdftoppm.issue) {
      issues.push(pdftoppm.issue);
    }
    if (issues.length) {
      return await finalizeProofBundleResponse("blocked", issues, bundle, cleanupOutput, resolvedOutputDir);
    }

    bundle.outputDirectoryCreated = await ensureDirectory(resolvedOutputDir);
    bundle.outputDirectoryExists = await pathExists(resolvedOutputDir);
    if (!bundle.outputDirectoryCreated || !bundle.outputDirectoryExists) {
      issues.push(issue("output_directory_unavailable", "Controlled output directory must exist before writing KR-7H.11 proof artifacts.", resolvedOutputDir));
      return await finalizeProofBundleResponse("blocked", issues, bundle, cleanupOutput, resolvedOutputDir);
    }

    const artifact = await runArtifactBundle({ workerRoot, payload, outputDir: resolvedOutputDir, cleanupOutput: false });
    if (artifact.completed.returncode !== 0 || !artifact.parsed || artifact.parsed.status !== "ready") {
      issues.push(issue("upstream_artifact_bundle_not_ready", `KR-7H.10 artifact bundle smoke must return ready before proof rendering: ${artifact.completed.stdout.slice(-1600)}`, ARTIFACT_SCRIPT_BASENAME));
      return await finalizeProofBundleResponse("blocked", issues, bundle, cleanupOutput, resolvedOutputDir);
    }
    bundle.upstreamArtifactBundleStatus = artifact.parsed.status;
    bundle.artifactBundleProduced = artifact.parsed.artifact_bundle_produced === true;
    bundle.artifactBundleVerified = artifact.parsed.artifact_bundle_verified === true;
    bundle.mappedSlideIds = Array.isArray(artifact.parsed.mapped_slide_ids) ? artifact.parsed.mapped_slide_ids : [];
    bundle.mappedSlideCount = Number.isInteger(artifact.parsed.mapped_slide_count) ? artifact.parsed.mapped_slide_count : 0;

    const pptxPath = path.join(resolvedOutputDir, ARTIFACT_BASENAME);
    const renderReportPath = path.join(resolvedOutputDir, RENDER_REPORT_BASENAME);
    const pptxInfo = await fileInfo(pptxPath);
    const reportInfo = await fileInfo(renderReportPath);
    bundle.pptxArtifactExists = pptxInfo.exists;
    bundle.pptxArtifactSizeBytes = pptxInfo.sizeBytes;
    bundle.pptxArtifactSha256 = pptxInfo.sha256;
    bundle.renderReportExists = reportInfo.exists;
    bundle.renderReportSizeBytes = reportInfo.sizeBytes;
    if (!pptxInfo.exists || !pptxInfo.sizeNonzero) {
      issues.push(issue("pptx_artifact_missing_or_empty", "KR-7H.11 requires the KR-7H.10 PPTX artifact to exist and be non-empty.", ARTIFACT_BASENAME));
    }
    if (!reportInfo.exists || !reportInfo.sizeNonzero) {
      issues.push(issue("render_report_missing_or_empty", "KR-7H.11 requires the KR-7H.10 render report to exist and be non-empty.", RENDER_REPORT_BASENAME));
    }
    if (issues.length) {
      return await finalizeProofBundleResponse("blocked", issues, bundle, cleanupOutput, resolvedOutputDir);
    }

    bundle.libreofficeExecuted = true;
    const proof = await runProofRender({ soffice: soffice.path, pdftoppm: pdftoppm.path, pptxPath, outputDir: resolvedOutputDir });
    if (!proof.ok) {
      if (proof.pdfInfo) {
        bundle.pdfProofExists = proof.pdfInfo.exists;
        bundle.pdfProofSizeBytes = proof.pdfInfo.sizeBytes;
        bundle.pdfProofFileSizeNonzero = proof.pdfInfo.sizeNonzero;
        bundle.pdfProofSha256 = proof.pdfInfo.sha256;
      }
      issues.push(proof.issue);
      return await finalizeProofBundleResponse("blocked", issues, bundle, cleanupOutput, resolvedOutputDir);
    }
    bundle.pdftoppmExecuted = true;
    bundle.pdfProofWritten = true;
    bundle.pdfProofExists = proof.pdfInfo.exists;
    bundle.pdfProofSizeBytes = proof.pdfInfo.sizeBytes;
    bundle.pdfProofFileSizeNonzero = proof.pdfInfo.sizeNonzero;
    bundle.pdfProofSha256 = proof.pdfInfo.sha256;
    bundle.pngProofsWritten = proof.pngBasenames.length > 0;
    bundle.pngProofCount = proof.pngBasenames.length;
    bundle.pngProofBasenames = proof.pngBasenames;
    bundle.pngProofSizeBytes = proof.pngSizeBytes;
    bundle.pngProofSha256 = proof.pngSha256;

    const proofPayload = baseResponse("ready", [], {
      ...bundle,
      proofBundleWritten: true,
      proofBundleExists: true,
      proofBundleProduced: true,
      proofBundleVerified: true,
      proofBundleDeterministic: true,
    });
    const proofInfo = await writeJson(path.join(resolvedOutputDir, PROOF_BUNDLE_BASENAME), proofPayload);
    bundle.proofBundleWritten = proofInfo.exists;
    bundle.proofBundleExists = proofInfo.exists;
    bundle.proofBundleSizeBytes = proofInfo.sizeBytes;
    bundle.proofBundleFileSizeNonzero = proofInfo.sizeNonzero;
    bundle.proofBundleProduced = bundle.pdfProofExists && bundle.pdfProofFileSizeNonzero && bundle.pngProofsWritten && bundle.pngProofCount > 0 && bundle.proofBundleWritten;
    bundle.proofBundleVerified = bundle.proofBundleProduced && bundle.pngProofSizeBytes.every((size) => Number.isInteger(size) && size > 0);
    bundle.proofBundleDeterministic = bundle.proofBundleVerified && proofPayload.schema_version === SCHEMA_VERSION;
    if (!bundle.proofBundleVerified) {
      issues.push(issue("proof_bundle_not_verified", "PDF, PNG, and proof bundle JSON must all exist with non-zero sizes.", PROOF_BUNDLE_BASENAME));
    }
    return await finalizeProofBundleResponse(issues.length === 0 ? "ready" : "blocked", issues, bundle, cleanupOutput, resolvedOutputDir);
  } catch (error) {
    issues.push(issue("proof_bundle_smoke_failed", `Could not complete KR-7H.11 proof bundle smoke: ${error.message}`, null));
    return await finalizeProofBundleResponse("blocked", issues, bundle, cleanupOutput, resolvedOutputDir);
  }
}

function parseArgs(argv) {
  const args = { json: false, help: false, stdin: false, fixture: false, outputDir: null, cleanupOutput: false, sofficeBin: null, pdftoppmBin: null };
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
    } else if (arg === "--soffice-bin") {
      index += 1;
      if (index >= argv.length) {
        throw new Error("--soffice-bin requires a path argument");
      }
      args.sofficeBin = argv[index];
    } else if (arg === "--pdftoppm-bin") {
      index += 1;
      if (index >= argv.length) {
        throw new Error("--pdftoppm-bin requires a path argument");
      }
      args.pdftoppmBin = argv[index];
    } else if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  if (args.stdin && args.fixture) {
    throw new Error("Use only one input mode: --stdin or --fixture");
  }
  return args;
}

function printHelp() {
  console.log("Usage: node renderer_worker/kw_renderer_worker_libreoffice_proof_bundle_smoke.mjs --json [--fixture|--stdin] --output-dir <dir> [--cleanup-output] [--soffice-bin <path>] [--pdftoppm-bin <path>]\n\nRuns the KR-7H.11 controlled LibreOffice + pdftoppm proof bundle smoke on top of the KR-7H.10 persistent PPTX artifact bundle. The smoke fails closed if LibreOffice, pdftoppm, PDF proof, or PNG proofs are unavailable; it never uses fake or fallback proof renderers as success evidence.");
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
    console.log(JSON.stringify(baseResponse("blocked", [issue("output_dir_required", "KR-7H.11 requires an explicit controlled --output-dir.", "--output-dir")]), null, 2));
    process.exitCode = 1;
    return;
  }

  let payload = null;
  if (args.stdin) {
    const input = await readStdin();
    try {
      payload = JSON.parse(input);
    } catch (error) {
      console.log(JSON.stringify(baseResponse("blocked", [issue("invalid_json_input", `Could not parse stdin JSON: ${error.message}`, null)]), null, 2));
      process.exitCode = 1;
      return;
    }
  } else if (args.fixture) {
    payload = null;
  } else {
    payload = minimalRendererInputFixture();
  }

  const workerRoot = path.dirname(fileURLToPath(import.meta.url));
  const effectivePayload = payload === null ? null : payload;
  const result = await runProofBundle({
    workerRoot,
    payload: effectivePayload,
    outputDir: args.outputDir,
    cleanupOutput: args.cleanupOutput,
    sofficeBin: args.sofficeBin,
    pdftoppmBin: args.pdftoppmBin,
  });
  console.log(JSON.stringify(result, null, 2));
  if (result.status !== "ready") {
    process.exitCode = 1;
  }
}

await main();
