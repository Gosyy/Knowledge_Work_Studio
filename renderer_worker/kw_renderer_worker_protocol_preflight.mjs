#!/usr/bin/env node
/**
 * KR-7H.3 renderer worker protocol preflight scaffold.
 *
 * This is a deterministic Node-side protocol validator for the future
 * PptxGenJS renderer worker. It intentionally does not import PptxGenJS,
 * generate PPTX, run LibreOffice, write artifact bundles, or claim rendered
 * output quality. It only validates the KR-7H.2 dry-run report/invocation
 * manifest and returns a fail-closed JSON response.
 */

import fs from "node:fs";

const PROTOCOL_SCHEMA_VERSION = "presentation_renderer_worker_protocol_preflight.v1";
const RESPONSE_SCHEMA_VERSION = "presentation_renderer_worker_protocol_preflight_response.v1";
const DRY_RUN_SCHEMA_VERSION = "presentation_renderer_worker_dry_run.v1";
const INVOCATION_MANIFEST_SCHEMA_VERSION = "presentation_renderer_worker_invocation_manifest.v1";
const RENDERER_INPUT_SCHEMA_VERSION = "presentation_renderer_worker_input.v1";
const CONTRACT_SCHEMA_VERSION = "presentation_renderer_worker_contract.v1";

const BLOCKED_RUNTIME_ACTIONS = Object.freeze([
  "start_node_worker",
  "import_or_execute_pptxgenjs",
  "generate_editable_pptx",
  "run_libreoffice_pdf_export",
  "render_slide_png_proofs",
  "write_artifact_bundle",
  "write_proof_bundle",
  "claim_visual_quality_score",
]);

function capabilities() {
  return {
    schema_version: PROTOCOL_SCHEMA_VERSION,
    phase: "KR-7H.3 renderer worker protocol preflight scaffold",
    protocol_runtime_implemented: true,
    renderer_runtime_implemented: false,
    production_pptx_output_implemented: false,
    artifact_bundle_produced: false,
    proof_bundle_produced: false,
    accepted_input_schema_versions: {
      dry_run: DRY_RUN_SCHEMA_VERSION,
      invocation_manifest: INVOCATION_MANIFEST_SCHEMA_VERSION,
      renderer_input: RENDERER_INPUT_SCHEMA_VERSION,
      contract: CONTRACT_SCHEMA_VERSION,
    },
    protocol_chain: [
      "receive_renderer_worker_dry_run_json",
      "validate_invocation_manifest_schema",
      "validate_renderer_input_schema",
      "return_fail_closed_preflight_response",
      "block_runtime_and_artifact_generation",
    ],
    blocked_runtime_actions: [...BLOCKED_RUNTIME_ACTIONS],
    non_goals: [
      "no_pptxgenjs_dependency",
      "no_pptx_generation",
      "no_libreoffice_execution",
      "no_artifact_bundle_storage",
      "no_proof_bundle_generation",
      "no_visual_qa_scoring",
      "no_production_quality_output_claims",
    ],
  };
}

function response(status, issues, inputSummary = {}) {
  return {
    schema_version: RESPONSE_SCHEMA_VERSION,
    protocol_schema_version: PROTOCOL_SCHEMA_VERSION,
    status,
    renderer_runtime_implemented: false,
    production_pptx_output_implemented: false,
    artifact_bundle_produced: false,
    proof_bundle_produced: false,
    preflight_runtime_implemented: true,
    output_mode: "protocol_preflight_only",
    blocked_runtime_actions: [...BLOCKED_RUNTIME_ACTIONS],
    input_summary: inputSummary,
    issues,
  };
}

function issue(code, message, path = null) {
  return { code, message, path };
}

function isObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function validateDryRunPayload(payload) {
  const issues = [];
  if (!isObject(payload)) {
    return response("blocked", [issue("payload_must_be_object", "Renderer worker preflight input must be a JSON object.", null)]);
  }

  if (payload.schema_version !== DRY_RUN_SCHEMA_VERSION) {
    issues.push(issue("unsupported_dry_run_schema", "Dry-run payload schema_version is unsupported.", "schema_version"));
  }
  if (payload.status !== "ready") {
    issues.push(issue("dry_run_not_ready", "Renderer worker protocol preflight accepts only ready dry-run reports.", "status"));
  }
  if (payload.renderer_runtime_implemented === true) {
    issues.push(issue("runtime_claim_not_allowed", "Dry-run payload must not claim renderer runtime implementation.", "renderer_runtime_implemented"));
  }
  if (payload.artifact_bundle_produced === true) {
    issues.push(issue("artifact_bundle_claim_not_allowed", "Dry-run payload must not claim artifact bundle production.", "artifact_bundle_produced"));
  }
  if (payload.proof_bundle_produced === true) {
    issues.push(issue("proof_bundle_claim_not_allowed", "Dry-run payload must not claim proof bundle production.", "proof_bundle_produced"));
  }

  const rendererInput = payload.renderer_input;
  if (!isObject(rendererInput)) {
    issues.push(issue("missing_renderer_input", "Ready dry-run payload must include renderer_input object.", "renderer_input"));
  } else {
    validateRendererInput(rendererInput, issues, "renderer_input");
  }

  const invocationManifest = payload.invocation_manifest;
  if (!isObject(invocationManifest)) {
    issues.push(issue("missing_invocation_manifest", "Ready dry-run payload must include invocation_manifest object.", "invocation_manifest"));
  } else {
    validateInvocationManifest(invocationManifest, issues, "invocation_manifest");
  }

  const inputSummary = {
    request_id: String(payload.request_id || ""),
    dry_run_schema_version: payload.schema_version || null,
    renderer_input_schema_version: isObject(rendererInput) ? rendererInput.schema_version || null : null,
    invocation_manifest_schema_version: isObject(invocationManifest) ? invocationManifest.schema_version || null : null,
    slide_count: isObject(rendererInput) && isObject(rendererInput.presentation_ir) && Array.isArray(rendererInput.presentation_ir.slides)
      ? rendererInput.presentation_ir.slides.length
      : 0,
  };

  return response(issues.length === 0 ? "ready" : "blocked", issues, inputSummary);
}

function validateRendererInput(rendererInput, issues, path) {
  if (rendererInput.schema_version !== RENDERER_INPUT_SCHEMA_VERSION) {
    issues.push(issue("unsupported_renderer_input_schema", "Renderer input schema_version is unsupported.", `${path}.schema_version`));
  }
  if (rendererInput.contract_schema_version !== CONTRACT_SCHEMA_VERSION) {
    issues.push(issue("unsupported_contract_schema", "Renderer input contract_schema_version is unsupported.", `${path}.contract_schema_version`));
  }
  if (rendererInput.status !== "ready") {
    issues.push(issue("renderer_input_not_ready", "Renderer input must be ready for protocol preflight.", `${path}.status`));
  }
  if (rendererInput.renderer_runtime_implemented === true) {
    issues.push(issue("renderer_input_runtime_claim_not_allowed", "Renderer input must not claim renderer runtime implementation.", `${path}.renderer_runtime_implemented`));
  }
  if (rendererInput.artifact_bundle_produced === true || rendererInput.proof_bundle_produced === true) {
    issues.push(issue("renderer_input_bundle_claim_not_allowed", "Renderer input must not claim artifact/proof bundle production.", path));
  }
  if (!isObject(rendererInput.presentation_ir)) {
    issues.push(issue("missing_presentation_ir", "Renderer input must include presentation_ir object.", `${path}.presentation_ir`));
  }
}

function validateInvocationManifest(manifest, issues, path) {
  if (manifest.schema_version !== INVOCATION_MANIFEST_SCHEMA_VERSION) {
    issues.push(issue("unsupported_invocation_manifest_schema", "Invocation manifest schema_version is unsupported.", `${path}.schema_version`));
  }
  if (manifest.contract_schema_version !== CONTRACT_SCHEMA_VERSION) {
    issues.push(issue("unsupported_invocation_contract_schema", "Invocation manifest contract_schema_version is unsupported.", `${path}.contract_schema_version`));
  }
  if (manifest.renderer_input_schema_version !== RENDERER_INPUT_SCHEMA_VERSION) {
    issues.push(issue("unsupported_invocation_renderer_input_schema", "Invocation manifest renderer_input_schema_version is unsupported.", `${path}.renderer_input_schema_version`));
  }
  if (manifest.status !== "dry_run_ready") {
    issues.push(issue("invocation_manifest_not_dry_run_ready", "Invocation manifest must be dry_run_ready.", `${path}.status`));
  }
  if (manifest.renderer_runtime_implemented === true || manifest.production_pptx_output_implemented === true) {
    issues.push(issue("invocation_runtime_claim_not_allowed", "Invocation manifest must not claim runtime or production PPTX output.", path));
  }
  if (manifest.artifact_bundle_produced === true || manifest.proof_bundle_produced === true) {
    issues.push(issue("invocation_bundle_claim_not_allowed", "Invocation manifest must not claim artifact/proof bundle production.", path));
  }
  const blocked = Array.isArray(manifest.blocked_runtime_actions) ? manifest.blocked_runtime_actions : [];
  for (const action of BLOCKED_RUNTIME_ACTIONS) {
    if (!blocked.includes(action)) {
      issues.push(issue("missing_blocked_runtime_action", `Invocation manifest must explicitly block ${action}.`, `${path}.blocked_runtime_actions`));
    }
  }
}

async function readInput(inputPath) {
  if (inputPath) {
    return fs.readFileSync(inputPath, "utf8");
  }
  return await new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => {
      data += chunk;
    });
    process.stdin.on("end", () => resolve(data));
    process.stdin.on("error", reject);
  });
}

function parseArgs(argv) {
  const args = { capabilities: false, input: null, json: false };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--capabilities") {
      args.capabilities = true;
    } else if (value === "--input") {
      args.input = argv[index + 1] || null;
      index += 1;
    } else if (value === "--json") {
      args.json = true;
    } else if (value === "--help" || value === "-h") {
      args.help = true;
    } else {
      throw new Error(`Unknown argument: ${value}`);
    }
  }
  return args;
}

function printHelp() {
  console.log(`Usage: node renderer_worker/kw_renderer_worker_protocol_preflight.mjs [--capabilities] [--input file] [--json]\n\nReads a KR-7H.2 dry-run JSON payload from --input or stdin and returns a KR-7H.3 fail-closed protocol preflight response. This script does not generate PPTX, import PptxGenJS, run LibreOffice, write artifacts, or claim visual quality.`);
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
  if (args.capabilities) {
    console.log(JSON.stringify(capabilities(), null, 2));
    return;
  }

  let payload;
  try {
    const raw = await readInput(args.input);
    payload = JSON.parse(raw);
  } catch (error) {
    console.log(JSON.stringify(response("blocked", [issue("invalid_json_input", `Could not parse renderer worker preflight JSON: ${error.message}`, null)]), null, 2));
    process.exitCode = 1;
    return;
  }

  const result = validateDryRunPayload(payload);
  console.log(JSON.stringify(result, null, 2));
  if (result.status !== "ready") {
    process.exitCode = 1;
  }
}

await main();
