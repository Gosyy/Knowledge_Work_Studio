#!/usr/bin/env node
/**
 * KR-7H.5 controlled PptxGenJS capability preflight.
 *
 * This script verifies that the isolated renderer_worker package can resolve
 * and import the pinned PptxGenJS dependency. It intentionally does not create
 * a presentation, add slides, write .pptx files, run LibreOffice, create
 * artifact/proof bundles, or claim production renderer readiness.
 */

import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const CAPABILITY_SCHEMA_VERSION = "presentation_renderer_worker_pptxgenjs_capability.v1";
const EXPECTED_PACKAGE_NAME = "pptxgenjs";
const EXPECTED_PACKAGE_VERSION = "4.0.1";

const BLOCKED_RUNTIME_ACTIONS = Object.freeze([
  "instantiate_presentation_for_output",
  "add_slide_content",
  "generate_editable_pptx",
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

function response(status, issues, capability = {}) {
  return {
    schema_version: CAPABILITY_SCHEMA_VERSION,
    phase: "KR-7H.5 controlled PptxGenJS capability preflight",
    status,
    dependency_name: EXPECTED_PACKAGE_NAME,
    expected_dependency_version: EXPECTED_PACKAGE_VERSION,
    dependency_available: status === "ready",
    dependency_version: capability.version || null,
    module_default_export_type: capability.defaultExportType || null,
    module_default_export_name: capability.defaultExportName || null,
    capability_preflight_implemented: true,
    renderer_runtime_implemented: false,
    production_pptx_output_implemented: false,
    pptx_generation_executed: false,
    artifact_bundle_produced: false,
    proof_bundle_produced: false,
    output_mode: "dependency_capability_preflight_only",
    blocked_runtime_actions: [...BLOCKED_RUNTIME_ACTIONS],
    non_goals: [
      "no_pptx_generation",
      "no_presentation_ir_mapping",
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

function findPackageJson(moduleEntryPoint) {
  let current = path.dirname(moduleEntryPoint);
  for (let index = 0; index < 8; index += 1) {
    const candidate = path.join(current, "package.json");
    if (fs.existsSync(candidate)) {
      return candidate;
    }
    const next = path.dirname(current);
    if (next === current) {
      break;
    }
    current = next;
  }
  return null;
}

async function checkCapability() {
  const issues = [];
  const require = createRequire(import.meta.url);

  let moduleEntryPoint;
  try {
    moduleEntryPoint = require.resolve(EXPECTED_PACKAGE_NAME);
  } catch (error) {
    return response("blocked", [issue("dependency_not_resolved", `Could not resolve ${EXPECTED_PACKAGE_NAME}: ${error.message}`, EXPECTED_PACKAGE_NAME)]);
  }

  const packageJsonPath = findPackageJson(moduleEntryPoint);
  if (!packageJsonPath) {
    issues.push(issue("dependency_package_json_not_found", "Could not locate dependency package.json after module resolution.", moduleEntryPoint));
  }

  let dependencyVersion = null;
  if (packageJsonPath) {
    try {
      const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));
      dependencyVersion = packageJson.version || null;
    } catch (error) {
      issues.push(issue("dependency_package_json_invalid", `Could not read dependency package.json: ${error.message}`, packageJsonPath));
    }
  }
  if (dependencyVersion !== EXPECTED_PACKAGE_VERSION) {
    issues.push(issue("dependency_version_mismatch", `Expected ${EXPECTED_PACKAGE_NAME}@${EXPECTED_PACKAGE_VERSION}, got ${dependencyVersion || "unknown"}.`, packageJsonPath));
  }

  let moduleNamespace;
  try {
    moduleNamespace = await import(EXPECTED_PACKAGE_NAME);
  } catch (error) {
    issues.push(issue("dependency_import_failed", `Could not import ${EXPECTED_PACKAGE_NAME}: ${error.message}`, EXPECTED_PACKAGE_NAME));
  }

  const defaultExport = moduleNamespace ? moduleNamespace.default : null;
  const capability = {
    version: dependencyVersion,
    defaultExportType: typeof defaultExport,
    defaultExportName: defaultExport && defaultExport.name ? String(defaultExport.name) : null,
  };
  if (typeof defaultExport !== "function") {
    issues.push(issue("dependency_default_export_unexpected", "PptxGenJS default export must be a function/class for future renderer work.", EXPECTED_PACKAGE_NAME));
  }

  return response(issues.length === 0 ? "ready" : "blocked", issues, capability);
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
  console.log("Usage: node renderer_worker/kw_renderer_worker_pptxgenjs_capability.mjs [--json]\n\nChecks PptxGenJS dependency availability only. Does not generate PPTX, run LibreOffice, or write artifacts.");
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

  const result = await checkCapability();
  console.log(JSON.stringify(result, null, 2));
  if (result.status !== "ready") {
    process.exitCode = 1;
  }
}

await main();
