#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

REQUIRED_P_PHASE_FILES = (
    "P_PHASE_ISSUE_PACK.md",
    "P_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md",
    ".github/workflows/postgres-integration.yml",
    ".github/workflows/frontend-e2e-smoke.yml",
    "scripts/kw_postgres_integration_gate.py",
    "scripts/kw_validate_deployment_package.py",
    "scripts/kw_schema_preflight.py",
    "scripts/kw_deployment_preflight.py",
    "scripts/kw_runtime_diagnostics.py",
    "scripts/kw_llm_topology_check.py",
    "scripts/kw_litellm_gateway_check.py",
    "scripts/kw_visual_qa_planning_check.py",
    "scripts/kw_offline_dependency_inventory_check.py", "docs/codex/OFFLINE_DEPENDENCY_REPRODUCIBILITY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_STRATEGY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_MANIFEST.md",
    "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_TOOLING.md",
    "docs/codex/OFFLINE_BOOTSTRAP_OPERATOR_RUNBOOK.md",
    "docs/codex/OFFLINE_BOOTSTRAP_INTEGRITY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_ARTIFACT_INVENTORY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_BUILD_READINESS.md",
    "docs/codex/OFFLINE_BOOTSTRAP_RF1_CLOSURE.md",
    "docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md",
    "docs/codex/SLIDES_RUNTIME_CAPABILITY_INVENTORY.md",
    "docs/codex/SLIDES_APPROVED_PLAN_RUNTIME.md",
    "docs/codex/SLIDES_APPROVED_PLAN_LIFECYCLE_RUNTIME.md",
    "docs/codex/SLIDES_SAVED_PLAN_RETRY_RUNTIME.md",
    "backend/app/services/slides_service/saved_plan_retry.py",
    "scripts/kw_slides_saved_plan_retry_check.py",
    "backend/tests/smoke/test_rf2_4_slides_saved_plan_retry.py",
    "docs/codex/SLIDES_RENDER_MODE_RUNTIME_HARDENING.md",
    "docs/codex/SLIDES_PROVENANCE_MANIFEST_RUNTIME.md",
    "docs/codex/SLIDES_RUNTIME_RF2_CLOSURE.md",
    "docs/codex/SLIDES_RUNTIME_RF2_FINAL_CLOSURE.md",
    "backend/app/services/slides_service/rf2_final_closure.py",
    "scripts/kw_slides_rf2_closure_check.py",
    "backend/tests/smoke/test_rf2_closure_slides_runtime.py",
    "docs/codex/DOCX_PDF_REAL_INGESTION_RUNTIME.md",
    "backend/app/services/docx_service/ingestion.py",
    "backend/app/services/pdf_service/ingestion.py",
    "scripts/kw_docx_pdf_real_ingestion_check.py",
    "backend/tests/smoke/test_rf3_docx_pdf_real_ingestion.py",
    "backend/app/services/slides_service/runtime_closure.py",
    "scripts/kw_slides_runtime_closure_check.py",
    "backend/tests/smoke/test_rf2_7_slides_runtime_closure.py",
    "backend/app/services/slides_service/provenance_manifest_runtime.py",
    "scripts/kw_slides_provenance_manifest_runtime_check.py",
    "backend/tests/smoke/test_rf2_6_slides_provenance_manifest_runtime.py",
    "backend/app/services/slides_service/render_mode_runtime.py",
    "scripts/kw_slides_render_mode_runtime_check.py",
    "backend/tests/smoke/test_rf2_5_slides_render_mode_runtime.py",
    "backend/app/services/slides_service/approved_plan_lifecycle.py",
    "scripts/kw_slides_approved_plan_lifecycle_check.py",
    "backend/tests/smoke/test_rf2_3_slides_approved_plan_lifecycle.py",
    "docs/codex/K_PHASE_PRODUCT_POWER_PLAN.md",
    "docs/codex/K0_KIMI_LEVEL_RUBRIC_AND_GOLDEN_BENCHMARK.md",
    "backend/app/services/k_phase/kimi_level_rubric.py",
    "backend/tests/smoke/test_k0_kimi_rubric.py",
    "docs/codex/K1_LOCAL_GIGACHAT_PLANNING_ENGINE.md",
    "backend/app/services/k_phase/local_gigachat_planner.py",
    "scripts/kw_k1_local_gigachat_planner_check.py",
    "backend/tests/smoke/test_k1_local_gigachat_planner.py",
    "docs/codex/K2_PLAN_EDITOR_PRODUCT_WORKFLOW.md",
    "backend/app/services/k_phase/plan_editor.py",
    "backend/tests/smoke/test_k2_plan_editor_workflow.py",
    "docs/codex/K3_RENDERER_QUALITY_RUNTIME.md",
    "backend/app/services/k_phase/renderer_quality.py",
    "backend/tests/smoke/test_k3_renderer_quality_runtime.py",
    "docs/codex/K4_VISUAL_QA_RUNTIME.md",
    "backend/app/services/k_phase/visual_qa.py",
    "backend/tests/smoke/test_k4_visual_qa_runtime.py",
    "docs/codex/K5_SOURCE_TO_SLIDE_PROVENANCE.md",
    "backend/app/services/k_phase/source_to_slide_provenance.py",
    "backend/tests/smoke/test_k5_source_to_slide_provenance.py",
    "docs/codex/K6_END_TO_END_KIMI_LIKE_WORKFLOW.md",
    "backend/app/services/k_phase/end_to_end_workflow.py",
    "backend/tests/smoke/test_k6_end_to_end_workflow.py",
    "docs/codex/K_PHASE_RELEASE_READINESS_CHECKPOINT.md",
    "backend/tests/smoke/test_k_phase_release_readiness_checkpoint.py",
    "docs/codex/RC1_GOLDEN_BENCHMARK_EXECUTION_HARNESS.md",
    "scripts/kw_rc1_golden_benchmark_harness.py",
    "backend/tests/smoke/test_rc1_golden_benchmark_harness.py",
    "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json",
    "docs/codex/RC2_GOLDEN_BENCHMARK_QUALITY_REVIEW_REPORT.md",
    "scripts/kw_rc2_golden_benchmark_quality_review.py",
    "backend/tests/smoke/test_rc2_golden_benchmark_quality_review.py",
    "docs/codex/RC3_LOCAL_GIGACHAT_GOLDEN_BENCHMARK_COMPARISON.md",
    "scripts/kw_rc3_local_gigachat_benchmark_comparison.py",
    "backend/tests/smoke/test_rc3_local_gigachat_benchmark_comparison.py",
    "docs/codex/RCH1_RENDERER_DENSITY_LAYOUT_FIXES.md",
    "scripts/kw_rch1_renderer_density_layout_check.py",
    "backend/tests/smoke/test_rch1_renderer_density_layout_fixes.py",
    "docs/codex/RCH2_PROVENANCE_FRAGMENT_QUALITY.md",
    "scripts/kw_rch2_provenance_fragment_quality_check.py",
    "backend/tests/smoke/test_rch2_provenance_fragment_quality.py",
    "docs/codex/RCH3_VISUAL_QA_HEURISTIC_CALIBRATION.md",
    "scripts/kw_rch3_visual_qa_calibration_check.py",
    "backend/tests/smoke/test_rch3_visual_qa_calibration.py",
    "docs/codex/RC4_RELEASE_CANDIDATE_ARTIFACT_PACK.md",
    "scripts/kw_rc4_release_candidate_artifact_pack.py",
    "backend/tests/smoke/test_rc4_release_candidate_artifact_pack.py",
    "docs/codex/RC5_FINAL_RELEASE_READINESS_DOSSIER.md",
    "scripts/kw_rc5_final_release_readiness_dossier.py",
    "backend/tests/smoke/test_rc5_final_release_readiness_dossier.py",
    "docs/codex/RCH4_GOLDEN_BENCHMARK_HUMAN_REVIEW_WORKFLOW.md",
    "scripts/kw_rch4_golden_benchmark_human_review.py",
    "backend/tests/smoke/test_rch4_golden_benchmark_human_review.py",
    "docs/codex/P9_PRODUCT_RELEASE_HARDENING_PLAN.md",
    "docs/codex/P9_1_GOLDEN_HUMAN_REVIEW_RESULTS.md",
    "backend/tests/fixtures/p9/p9_1_human_review_results.json",
    "backend/tests/smoke/test_p9_1_human_review_results.py",
    "docs/codex/P9_2_RENDERER_CONTENT_HARDENING.md",
    "scripts/kw_p9_2_renderer_content_hardening_check.py",
    "backend/tests/smoke/test_p9_2_renderer_content_hardening.py",
    "docs/codex/P9_3_RENDERER_LAYOUT_HARDENING.md",
    "scripts/kw_p9_3_renderer_layout_hardening_check.py",
    "backend/tests/smoke/test_p9_3_renderer_layout_hardening.py",
    "docs/codex/P9_4_VISUAL_QA_SEMANTIC_GUARD.md",
    "scripts/kw_p9_4_visual_qa_semantic_guard_check.py",
    "backend/tests/smoke/test_p9_4_visual_qa_semantic_guard.py",
    "docs/codex/P9_5_PROVENANCE_USEFULNESS.md",
    "scripts/kw_p9_5_provenance_usefulness_check.py",
    "backend/tests/smoke/test_p9_5_provenance_usefulness.py",
    "docs/codex/P9_6_SEMANTIC_SOURCE_COVERAGE.md",
    "scripts/kw_p9_6_semantic_source_coverage_check.py",
    "backend/tests/smoke/test_p9_6_semantic_source_coverage.py",
    "docs/codex/P9_7_GOLDEN_REVIEW_READINESS.md",
    "scripts/kw_p9_7_golden_review_readiness_check.py",
    "backend/tests/smoke/test_p9_7_golden_review_readiness.py",
    "docs/codex/P9_8_PRODUCT_RELEASE_HARDENING_CLOSURE.md",
    "scripts/kw_p9_8_product_release_hardening_closure_check.py",
    "backend/tests/smoke/test_p9_8_product_release_hardening_closure.py",
    "docs/codex/P10_POST_P9_GOLDEN_REVIEW_PHASE_PLAN.md",
    "backend/tests/smoke/test_p10_1_post_p9_regeneration_readiness.py",
    "docs/codex/P10_2_POST_P9_ARTIFACT_PACK.md",
    "backend/tests/smoke/test_p10_2_post_p9_artifact_pack.py",
    "docs/codex/P10_5A_GIGACHAT_API_GOLDEN_BENCHMARK.md",
    "scripts/kw_p10_5a_gigachat_api_golden_benchmark.py",
    "backend/tests/smoke/test_p10_5a_gigachat_api_golden_benchmark.py",
    "docs/codex/P10_5_RELEASE_DECISION_DOSSIER.md",
    "scripts/kw_p10_5_release_decision_dossier.py",
    "backend/tests/smoke/test_p10_5_release_decision_dossier.py",
    "docs/codex/OPERATOR_LOGGING_AND_DOWNLOADS_POLICY.md",
    "scripts/kw_operator_log_archive.py",
    "scripts/kw_patch_full_tests_summary.py",
    "scripts/kw_full_tests_with_proxy_runner.sh",
    "scripts/kw_operator_logging_policy_check.py",
    "backend/tests/smoke/test_operator_logging_downloads_policy.py",
    "docs/codex/KRC_FINAL_BRANCH_CLOSURE.md",
    "scripts/kw_krc_final_branch_closure_check.py",
    "backend/tests/smoke/test_krc_final_branch_closure.py",
    "docs/codex/RF_EXIT_TO_K_PHASE_CRITERIA.md",
    "scripts/kw_rf_to_k_transition_check.py",
    "backend/tests/smoke/test_rf2_2a_rf_to_k_transition.py",
    "backend/app/services/slides_service/approved_plan.py",
    "scripts/kw_slides_approved_plan_runtime_check.py",
    "backend/tests/smoke/test_rf2_2_slides_approved_plan_runtime.py",
    "scripts/kw_slides_runtime_inventory_check.py",
    "backend/tests/smoke/test_rf2_1_slides_runtime_inventory.py",
    "docs/codex/CONTROLLED_DEPENDENCY_SECURITY_ASSESSMENT.md",
    "scripts/kw_controlled_dependency_security_assessment.py",
    "backend/tests/smoke/test_rf1_10_controlled_dependency_security_assessment.py",
    "scripts/kw_slides_runtime_phase_check.py",
    "backend/tests/smoke/test_rf2_0_slides_runtime_phase.py",
    "backend/tests/smoke/test_rf1_9_offline_operator_command_groups.py",
    "backend/tests/smoke/test_rf1_8_offline_build_readiness.py",
    "backend/tests/smoke/test_rf1_7_offline_artifact_inventory.py",
    "backend/tests/smoke/test_rf1_6_offline_bundle_integrity.py",
    "backend/tests/smoke/test_rf1_5_offline_bundle_artifact_presence.py",
    "scripts/kw_offline_bootstrap_bundle_tool.py",
    "backend/tests/smoke/test_rf1_4_offline_bootstrap_bundle_tooling.py",
    "scripts/kw_offline_bootstrap_manifest_check.py",
    "backend/tests/smoke/test_rf1_3_offline_bootstrap_manifest.py",
    "scripts/kw_offline_bootstrap_bundle_check.py",
    "backend/tests/smoke/test_rf1_2_offline_bootstrap_bundle.py", "backend/tests/smoke/test_rf1_offline_dependency_inventory.py", "backend/app/integrations/llm/litellm_gateway_contract.py",
    "scripts/kw_workflow_contracts_check.py", "scripts/kw_workflow_contract_core_check.py", "docs/architecture/WORKFLOW_CONTRACT_CORE.md", "backend/app/workflows/core_contracts.py", "scripts/kw_slides_plan_first_check.py",
    "scripts/kw_slides_task_events_check.py",
    "scripts/kw_slides_plan_editor_check.py",
    "scripts/kw_browser_evidence_capture_check.py",
    "scripts/kw_operator_smoke.py",
    "frontend/playwright.config.ts",
    "frontend/tests/e2e/deck-revision-smoke.spec.ts",
    "frontend/tests/e2e/version-timeline-smoke.spec.ts",
    "frontend/tests/e2e/version-restore-smoke.spec.ts",
    "Dockerfile.backend",
    "frontend/Dockerfile",
    "docker-compose.deploy.yml",
    ".env.deploy.example",
    "docs/deployment-packaging.md",
    "docs/schema-lifecycle.md",
    "docs/observability-baseline.md",
    "docs/offline-llm-topology.md",
    "docs/llm-provider-contract.md",
    "docs/litellm-gateway-topology.md",
    "docs/visual-qa-planning.md",
    "docs/heavy-node-runtime.md",
    "docs/workflow-contracts.md", "docs/slides-plan-first-ux.md",
    "docs/slides-task-events-and-retry.md",
    "docs/slides-plan-editor-ui.md",
    "docs/browser-evidence-capture.md",
    "docs/artifact-delivery-hardening.md",
    "docs/revision-restore.md",
    "docs/version-timeline-ui.md",
    "docs/codex/GIGACHAT_RUNTIME_HARDENING.md",
    "backend/app/integrations/llm/gigachat_runtime.py",
    "scripts/kw_gigachat_runtime_hardening_check.py",
    "backend/tests/smoke/test_rf4_gigachat_runtime_hardening.py",
    "docs/codex/RUNTIME_FOUNDATION_FINAL_CLOSURE.md",
    "backend/app/services/runtime_foundation_closure.py",
    "scripts/kw_runtime_foundation_closure_check.py",
    "backend/tests/smoke/test_rf_closure_runtime_foundation.py",
    "backend/tests/smoke/test_s9_litellm_gateway_contract.py",
    "docs/codex/P10_6_HUMAN_REVIEW_PACKET_EXPORT.md",
    "scripts/kw_p10_6_human_review_packet_export.py",
    "backend/tests/smoke/test_p10_6_human_review_packet_export.py",
    "docs/codex/P10_7A_HUMAN_REVIEW_WORKSHEET_IMPORT_VALIDATOR.md",
    "scripts/kw_p10_7a_human_review_worksheet_import_validator.py",
    "backend/tests/smoke/test_p10_7a_human_review_worksheet_import_validator.py",
    "docs/codex/P10_7_HUMAN_REVIEW_RESULTS_INGEST.md",
    "backend/tests/fixtures/p10/p10_7_human_review_results.json",
    "scripts/kw_p10_7_human_review_results_ingest.py",
    "backend/tests/smoke/test_p10_7_human_review_results_ingest.py",
    "docs/codex/P10_8_FINAL_RELEASE_DECISION_DOSSIER.md",
    "scripts/kw_p10_8_final_release_decision_dossier.py",
    "backend/tests/smoke/test_p10_8_final_release_decision_dossier.py",
    "docs/codex/P10_9_TARGETED_ARCHITECTURE_REWORK.md",
    "scripts/kw_p10_9_targeted_architecture_rework.py",
    "backend/tests/smoke/test_p10_9_targeted_architecture_rework.py",
    "docs/codex/P10_10_FINAL_RELEASE_APPROVAL_DOSSIER.md",
    "backend/tests/smoke/test_p10_10_final_release_approval_dossier.py",
    "docs/codex/P10_11_FINAL_OPERATOR_RELEASE_CLOSURE.md",
    "backend/tests/smoke/test_p10_11_final_operator_release_closure.py",
    "docs/codex/S_PHASE_KIMI_SLIDES_CLASS_ROADMAP.md",
    "docs/codex/S1_KIMI_SLIDES_CLASS_GAP_DOSSIER.md",
    "scripts/kw_s1_kimi_slides_gap_check.py",
    "backend/tests/smoke/test_s1_kimi_slides_gap.py",
    "docs/codex/S2_OUTLINE_FIRST_FRONTEND_WORKFLOW.md",
    "scripts/kw_s2_outline_first_frontend_workflow_check.py",
    "backend/tests/smoke/test_s2_outline_first_frontend_workflow.py",
    "docs/codex/S3_ADAPTIVE_DECK_MODES.md",
    "backend/app/services/slides_service/adaptive_deck_modes.py",
    "scripts/kw_s3_adaptive_deck_modes_check.py",
    "backend/tests/smoke/test_s3_adaptive_deck_modes.py",
    "docs/codex/S4_NATIVE_TABLE_CHART_DIAGRAM_RENDERING.md",
    "backend/app/services/slides_service/native_visuals.py",
    "scripts/kw_s4_native_visual_rendering_check.py",
    "backend/tests/smoke/test_s4_native_visual_rendering.py",
    "docs/codex/S5_TEMPLATE_MASTER_INGESTION.md",
    "backend/app/services/slides_service/template_master_ingestion.py",
    "scripts/kw_s5_template_master_ingestion_check.py",
    "backend/tests/smoke/test_s5_template_master_ingestion.py",
    "docs/codex/S6_IMAGE_SCREENSHOT_TO_SLIDE_WORKFLOW.md",
    "backend/app/services/slides_service/image_to_slide_workflow.py",
    "scripts/kw_s6_image_to_slide_workflow_check.py",
    "backend/tests/smoke/test_s6_image_to_slide_workflow.py",
    "docs/codex/S7_OFFLINE_INTRANET_RESEARCH_CITATIONS.md",
    "backend/app/services/slides_service/offline_research_citations.py",
    "scripts/kw_s7_offline_research_citations_check.py",
    "backend/tests/smoke/test_s7_offline_research_citations.py",
    "docs/codex/S8_CONVERSATIONAL_EDIT_LOOP.md",
    "backend/app/services/slides_service/conversational_edit_loop.py",
    "scripts/kw_s8_conversational_edit_loop_check.py",
    "backend/tests/smoke/test_s8_conversational_edit_loop.py",
    "docs/codex/S9_RENDER_BASED_VISUAL_QA.md",
    "backend/app/services/slides_service/render_based_visual_qa.py",
    "scripts/kw_s9_render_based_visual_qa_check.py",
    "backend/tests/smoke/test_s9_render_based_visual_qa.py",
    "docs/codex/S10_EXPANDED_KIMI_STYLE_BENCHMARK.md",
    "backend/app/services/slides_service/kimi_style_benchmark.py",
    "scripts/kw_s10_kimi_style_benchmark_check.py",
    "backend/tests/smoke/test_s10_kimi_style_benchmark.py",
    "docs/codex/S11_S_PHASE_CLOSURE_DOSSIER.md",
    "backend/app/services/slides_service/s_phase_closure.py",
    "scripts/kw_s11_s_phase_closure_check.py",
    "backend/tests/smoke/test_s11_s_phase_closure.py",
    "docs/codex/S12_SELECTED_BENCHMARK_EXECUTION_PACKET.md",
    "backend/app/services/slides_service/selected_benchmark_execution_packet.py",
    "scripts/kw_s12_selected_benchmark_execution_packet_check.py",
    "backend/tests/smoke/test_s12_selected_benchmark_execution_packet.py",
    "docs/codex/S13A_SELECTED_BENCHMARK_REVIEW_PACKET.md",
    "backend/app/services/slides_service/selected_benchmark_review_packet.py",
    "scripts/kw_s13a_selected_benchmark_review_packet_check.py",
    "backend/tests/smoke/test_s13a_selected_benchmark_review_packet.py",
    "docs/codex/S13B_LIVE_PUBLIC_API_DEV_GIGACHAT_GENERATION.md",
    "backend/app/services/slides_service/live_gigachat_selected_benchmark.py",
    "scripts/kw_s13b_live_gigachat_selected_benchmark_check.py",
    "scripts/kw_s13b_live_gigachat_selected_benchmark_run.py",
    "backend/tests/smoke/test_s13b_live_gigachat_selected_benchmark.py",
    "docs/codex/S13C_LIVE_GIGACHAT_EVIDENCE_PACKET_EXPORT.md",
    "backend/app/services/slides_service/live_gigachat_evidence_packet.py",
    "scripts/kw_s13c_live_gigachat_evidence_packet_check.py",
    "scripts/kw_s13c_live_gigachat_evidence_packet_export.py",
    "backend/tests/smoke/test_s13c_live_gigachat_evidence_packet.py",
    "docs/codex/S13D_LIVE_BENCHMARK_PROMPT_SCHEMA_HARDENING.md",
    "backend/app/services/slides_service/live_benchmark_prompt_schema_hardening.py",
    "scripts/kw_s13d_live_benchmark_prompt_schema_hardening_check.py",
    "scripts/kw_s13d_live_gigachat_hardened_benchmark_run.py",
    "backend/tests/smoke/test_s13d_live_benchmark_prompt_schema_hardening.py",
    "docs/codex/S13E_HARDENED_OUTPUT_REPAIR.md",
    "backend/app/services/slides_service/hardened_output_repair.py",
    "scripts/kw_s13e_hardened_output_repair_check.py",
    "scripts/kw_s13e_hardened_output_repair_run.py",
    "backend/tests/smoke/test_s13e_hardened_output_repair.py",
    "docs/codex/S13F_STRICT_JSON_PER_SCENARIO_RERUN.md",
    "backend/app/services/slides_service/strict_json_per_scenario_rerun.py",
    "scripts/kw_s13f_strict_json_per_scenario_rerun_check.py",
    "scripts/kw_s13f_strict_json_per_scenario_rerun.py",
    "backend/tests/smoke/test_s13f_strict_json_per_scenario_rerun.py",
    "backend/tests/smoke/test_s13g_canonical_schema_adapter.py",
    "docs/codex/S13H_TARGETED_RETRY_FAILED_S13G.md",
    "backend/app/services/slides_service/targeted_s13g_retry.py",
    "scripts/kw_s13h_targeted_s13g_retry_check.py",
    "scripts/kw_s13h_targeted_s13g_retry.py",
    "backend/tests/smoke/test_s13h_targeted_s13g_retry.py",
    "docs/codex/S13I_SINGLE_SCENARIO_EXECUTIVE_MEMO_RETRY.md",
    "backend/app/services/slides_service/single_scenario_s13h_retry.py",
    "scripts/kw_s13i_single_scenario_retry_check.py",
    "scripts/kw_s13i_single_scenario_retry.py",
    "backend/tests/smoke/test_s13i_single_scenario_retry.py",
    "docs/codex/S13J_EXECUTIVE_MEMO_SALVAGE.md",
    "backend/app/services/slides_service/executive_memo_salvage.py",
    "scripts/kw_s13j_executive_memo_salvage_check.py",
    "scripts/kw_s13j_executive_memo_salvage.py",
    "backend/tests/smoke/test_s13j_executive_memo_salvage.py",
    "docs/codex/S13K_HUMAN_REVIEW_PACKET_FROM_S13J.md",
    "backend/app/services/slides_service/s13j_human_review_packet.py",
    "scripts/kw_s13k_human_review_packet_check.py",
    "scripts/kw_s13k_human_review_packet_export.py",
    "backend/tests/smoke/test_s13k_human_review_packet.py",
    "docs/codex/KQ_PHASE_QUALITY_ROADMAP.md",
    "docs/codex/KQ1A_DECK_ARTIFACT_QUALITY_HARNESS.md",
    "backend/app/services/slides_service/kq_deck_quality.py",
    "scripts/kw_kq1_exec_memo_deck_quality.py",
    "backend/tests/smoke/test_kq1_deck_quality.py",
    "docs/codex/KQ1B_EXEC_MEMO_ACTUAL_PPTX_GENERATION.md",
    "backend/app/services/slides_service/kq_exec_memo_deck_generation.py",
    "scripts/kw_kq1b_exec_memo_pptx_check.py",
    "scripts/kw_kq1b_exec_memo_pptx_generate.py",
    "backend/tests/smoke/test_kq1b_exec_memo_deck_generation.py",
    "scripts/kw_s13g_canonical_schema_adapter_rerun.py",
    "scripts/kw_s13g_canonical_schema_adapter_check.py",
    "backend/app/services/slides_service/canonical_schema_adapter.py",
    "docs/codex/S13G_CANONICAL_SCHEMA_ADAPTER.md",
)

SECRET_MARKERS = (
    "sk-proj-",
    "sk-live-",
    "xoxb-",
    "ghp_",
    "gho_",
    "ghu_",
    "github_pat_",
    "BEGIN PRIVATE KEY",
    "AWS_SECRET_ACCESS_KEY=",
    "OPENAI_API_KEY=sk-",
    "GIGACHAT_API_KEY=",
)

TEXT_SUFFIXES = {
    "",
    ".dockerignore",
    ".env",
    ".example",
    ".gitignore",
    ".ini",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yml",
    ".yaml",
}

SECRET_MARKER_ALLOWLIST_FILES = {
    # These files intentionally contain marker literals as scanner catalogs or scanner tests.
    "scripts/kw_production_readiness_gate.py",
    "scripts/kw_validate_deployment_package.py",
    "backend/tests/smoke/test_p6_deployment_packaging.py",
    "backend/tests/smoke/test_p7_production_readiness_gate.py",
    "scripts/kw_dependency_audit.py",
    "backend/tests/smoke/test_r8_dependency_audit.py",
}


@dataclass(frozen=True)
class GateStep:
    name: str
    command: tuple[str, ...]
    cwd: Path | None = None


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def run_step(step: GateStep) -> None:
    cwd = step.cwd or Path.cwd()
    printable = " ".join(step.command)
    print()
    print("=" * 96)
    print(f"[STEP] {step.name}")
    print(f"$ {printable}")
    print("=" * 96)
    started = perf_counter()
    result = subprocess.run(step.command, cwd=cwd, text=True, check=False)
    elapsed = perf_counter() - started
    if result.returncode != 0:
        raise SystemExit(f"[FAIL] {step.name} failed with exit code {result.returncode} after {elapsed:.1f}s")
    print(f"[PASS] {step.name} completed in {elapsed:.1f}s")


def require_files(repo_root: Path) -> list[str]:
    missing = [path for path in REQUIRED_P_PHASE_FILES if not (repo_root / path).exists()]
    return [f"missing expected P-phase file: {path}" for path in missing]


def is_text_candidate(path: Path) -> bool:
    if path.name in {"Makefile", "Dockerfile", "Dockerfile.backend"}:
        return True
    return path.suffix in TEXT_SUFFIXES or path.name.endswith(".env.deploy.example")


def iter_scannable_files(repo_root: Path) -> list[Path]:
    excluded_parts = {
        ".git",
        ".venv",
        "node_modules",
        ".next",
        ".pytest_cache",
        "__pycache__",
        "playwright-report",
        "test-results",
    }
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_root)
        if any(part in excluded_parts for part in rel.parts):
            continue
        if is_text_candidate(path):
            files.append(path)
    return files


def scan_for_secret_markers(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for path in iter_scannable_files(repo_root):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(repo_root)
        rel_posix = rel.as_posix()
        if rel_posix in SECRET_MARKER_ALLOWLIST_FILES:
            continue
        for marker in SECRET_MARKERS:
            if marker in content:
                errors.append(f"potential secret marker '{marker}' found in {rel}")
    return errors


def checks_only(repo_root: Path) -> None:
    print(f"[INFO] repo_root={repo_root}")
    errors = []
    errors.extend(require_files(repo_root))
    errors.extend(scan_for_secret_markers(repo_root))
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        raise SystemExit(2)
    print("[PASS] required P-phase files are present")
    print("[PASS] no forbidden secret markers found in tracked text candidates")


def build_steps(repo_root: Path, args: argparse.Namespace) -> list[GateStep]:
    python = sys.executable
    frontend_dir = repo_root / "frontend"
    steps: list[GateStep] = []

    steps.append(GateStep("Git whitespace check", ("git", "diff", "--check"), repo_root))

    if args.require_clean_git:
        steps.append(GateStep("Git working tree is clean", ("git", "diff", "--exit-code"), repo_root))
        steps.append(GateStep("Git index is clean", ("git", "diff", "--cached", "--exit-code"), repo_root))

    steps.append(
        GateStep(
            "Deployment package validation",
            (python, "scripts/kw_validate_deployment_package.py", "--repo-root", str(repo_root)),
            repo_root,
        )
    )

    if not args.skip_preflight:
        steps.append(
            GateStep(
                "Deployment preflight static checks",
                (
                    python,
                    "scripts/kw_deployment_preflight.py",
                    "--repo-root",
                    str(repo_root),
                    "--skip-readiness",
                    "--skip-tests",
                    "--skip-frontend",
                ),
                repo_root,
            )
        )

    steps.append(
        GateStep(
            "Postgres schema lifecycle preflight",
            (python, "scripts/kw_schema_preflight.py", "--repo-root", str(repo_root), "--explain"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Runtime diagnostics",
            (python, "scripts/kw_runtime_diagnostics.py", "--repo-root", str(repo_root)),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline LLM topology contract",
            (python, "scripts/kw_llm_topology_check.py", "--repo-root", str(repo_root), "--allow-placeholders", "--require-ready"),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "LiteLLM gateway optional transport contract",
            (
                python,
                "scripts/kw_litellm_gateway_check.py",
                "--repo-root",
                str(repo_root),
                "--allow-placeholders",
                "--require-ready",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Workflow contracts registry",
            (python, "scripts/kw_workflow_contracts_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Workflow contract core",
            (python, "scripts/kw_workflow_contract_core_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides plan-first UX contract",
            (python, "scripts/kw_slides_plan_first_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Slides task event retry contract",
            (python, "scripts/kw_slides_task_events_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Slides plan editor UI contract",
            (python, "scripts/kw_slides_plan_editor_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )

    steps.append(

        GateStep(

            "Slides adaptive/template render mode contract",

            (python, "scripts/kw_slides_render_modes_check.py", "--repo-root", str(repo_root), "--require-ready"),

            repo_root,

        )

    )


    steps.append(
        GateStep(
            "Slides provenance manifest contract",
            (
                python,
                "scripts/kw_slides_provenance_manifest_check.py",
                "--repo-root",
                str(repo_root),
                "--mode",
                "generation",
                "--require-ready",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Browser evidence capture contract",
            (
                python,
                "scripts/kw_browser_evidence_capture_check.py",
                "--repo-root",
                str(repo_root),
                "--mode",
                "capture",
                "--require-ready",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Browser evidence slides provenance link contract",
            (
                python,
                "scripts/kw_browser_evidence_capture_check.py",
                "--repo-root",
                str(repo_root),
                "--mode",
                "slides_link",
                "--require-ready",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Visual QA planning contract",
            (
                python,
                "scripts/kw_visual_qa_planning_check.py",
                "--repo-root",
                str(repo_root),
                "--mode",
                "slides",
                "--require-ready",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Visual QA artifact planning contract",
            (
                python,
                "scripts/kw_visual_qa_planning_check.py",
                "--repo-root",
                str(repo_root),
                "--mode",
                "artifact",
                "--require-ready",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Offline dependency inventory contract",
            (
                python,
                "scripts/kw_offline_dependency_inventory_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline bootstrap bundle strategy contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline bootstrap manifest validation contract",
            (
                python,
                "scripts/kw_offline_bootstrap_manifest_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline bootstrap bundle tooling contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_tool.py",
                "check-policy",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline bundle artifact presence policy contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_tool.py",
                "check-artifact-policy",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline bundle checksum integrity policy contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_tool.py",
                "check-integrity-policy",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline artifact inventory policy contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_tool.py",
                "check-inventory-policy",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline bundle readiness report policy contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_tool.py",
                "check-readiness-policy",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline operator command groups and RF1 closure policy contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_tool.py",
                "check-closure-policy",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides runtime phase checkpoint",
            (
                python,
                "scripts/kw_slides_runtime_phase_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Controlled dependency/security baseline assessment",
            (
                python,
                "scripts/kw_controlled_dependency_security_assessment.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides runtime capability inventory and baseline smoke",
            (
                python,
                "scripts/kw_slides_runtime_inventory_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides approved-plan deterministic PPTX runtime",
            (
                python,
                "scripts/kw_slides_approved_plan_runtime_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    product_checks_dir = repo_root / "logs" / "production_readiness_product_checks"

    steps.append(
        GateStep(
            "KR product reset roadmap guardrail",
            (
                python,
                "scripts/kw_kr_product_reset_roadmap_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "KR-3E active gate legacy retirement guardrail",
            (
                python,
                "scripts/kw_active_gate_legacy_retirement_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "KR-3F controlled archive/delete readiness guardrail",
            (
                python,
                "scripts/kw_controlled_archive_delete_readiness_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Product workflow and quality aliases",
            (
                python,
                "scripts/kw_product_test_aliases_check.py",
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(product_checks_dir / "product_test_aliases"),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Low-risk operator static replacement tests",
            (
                python,
                "scripts/kw_low_risk_operator_static_replacements_check.py",
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(product_checks_dir / "low_risk_operator_static_replacements"),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides product quality replacement tests",
            (
                python,
                "scripts/kw_slides_product_quality_replacements_check.py",
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(product_checks_dir / "slides_product_quality_replacements"),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "DOCX PDF XLSX product workflow tests",
            (
                python,
                "scripts/kw_docx_pdf_xlsx_product_workflows_check.py",
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(product_checks_dir / "docx_pdf_xlsx_product_workflows"),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Path portability policy",
            (
                python,
                "scripts/kw_path_portability_policy_check.py",
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(product_checks_dir / "path_portability_policy"),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Path portability cleanup plan",
            (
                python,
                "scripts/kw_path_portability_cleanup_plan.py",
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(product_checks_dir / "path_portability_cleanup_plan"),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Legacy stage baseline pin retirement manifest",
            (
                python,
                "scripts/kw_legacy_stage_baseline_pin_retirement.py",
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(product_checks_dir / "legacy_stage_baseline_pin_retirement"),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )











    steps.append(
        GateStep(
            "RC1 Golden benchmark execution harness",
            (python, "scripts/kw_rc1_golden_benchmark_harness.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "RC2 Golden benchmark quality review report",
            (python, "scripts/kw_rc2_golden_benchmark_quality_review.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "RC3 Local GigaChat golden benchmark comparison",
            (python, "scripts/kw_rc3_local_gigachat_benchmark_comparison.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )



    steps.append(
        GateStep(
            "RCH1 Renderer density/layout fixes",
            (python, "scripts/kw_rch1_renderer_density_layout_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "RCH2 Provenance fragment quality/diversity fixes",
            (python, "scripts/kw_rch2_provenance_fragment_quality_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "RCH3 Visual QA heuristic calibration",
            (python, "scripts/kw_rch3_visual_qa_calibration_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "RC4 Release candidate artifact pack",
            (python, "scripts/kw_rc4_release_candidate_artifact_pack.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "RC5 Final release readiness dossier",
            (python, "scripts/kw_rc5_final_release_readiness_dossier.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "RCH4 Golden benchmark human review workflow",
            (python, "scripts/kw_rch4_golden_benchmark_human_review.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "P9-2 Renderer/content hardening",
            (python, "scripts/kw_p9_2_renderer_content_hardening_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "P9-3 Renderer/layout hardening",
            (python, "scripts/kw_p9_3_renderer_layout_hardening_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "P9-4 Visual QA semantic guard",
            (python, "scripts/kw_p9_4_visual_qa_semantic_guard_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "P9-5 Provenance usefulness",
            (python, "scripts/kw_p9_5_provenance_usefulness_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "P9-6 Semantic source coverage",
            (python, "scripts/kw_p9_6_semantic_source_coverage_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "P9-7 Golden benchmark post-hardening review readiness",
            (python, "scripts/kw_p9_7_golden_review_readiness_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "K/RC final branch closure",
            (python, "scripts/kw_krc_final_branch_closure_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "K1 Local GigaChat planning engine",
            (python, "scripts/kw_k1_local_gigachat_planner_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "RF-to-K transition guard",
            (
                python,
                "scripts/kw_rf_to_k_transition_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "Slides approved-plan lifecycle runtime",
            (
                python,
                "scripts/kw_slides_approved_plan_lifecycle_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "Slides saved-plan retry runtime",
            (
                python,
                "scripts/kw_slides_saved_plan_retry_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides provenance manifest runtime",
            (
                python,
                "scripts/kw_slides_provenance_manifest_runtime_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides render mode runtime hardening",
            (
                python,
                "scripts/kw_slides_render_mode_runtime_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides RF2 runtime closure and readiness",
            (
                python,
                "scripts/kw_slides_runtime_closure_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides RF2 final closure checkpoint",
            (
                python,
                "scripts/kw_slides_rf2_closure_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "DOCX/PDF real ingestion runtime",
            (
                python,
                "scripts/kw_docx_pdf_real_ingestion_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "GigaChat runtime hardening",
            (
                python,
                "scripts/kw_gigachat_runtime_hardening_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Runtime Foundation final closure checkpoint",
            (
                python,
                "scripts/kw_runtime_foundation_closure_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    if args.postgres_mode == "safety":
        steps.append(
            GateStep(
                "Postgres gate safety checks",
                (python, "scripts/kw_postgres_integration_gate.py", "--safety-only"),
                repo_root,
            )
        )
    elif args.postgres_mode == "optional":
        steps.append(GateStep("Optional real Postgres gate", (python, "scripts/kw_postgres_integration_gate.py"), repo_root))
    elif args.postgres_mode == "required":
        steps.append(
            GateStep(
                "Required real Postgres gate",
                (python, "scripts/kw_postgres_integration_gate.py", "--require-dsn"),
                repo_root,
            )
        )

    if not args.skip_backend:
        steps.append(GateStep("Backend full pytest suite", (python, "-m", "pytest", "-q"), repo_root))
        steps.append(GateStep("Backend compileall", (python, "-m", "compileall", "backend"), repo_root))

    if not args.skip_frontend:
        steps.append(GateStep("Frontend production build", ("npm", "run", "build"), frontend_dir))
        if not args.skip_e2e:
            steps.append(GateStep("Frontend E2E smoke", ("npm", "run", "test:e2e:smoke"), frontend_dir))

    steps.append(
        GateStep(
            "P9-8 Product release hardening closure dossier",
            (python, "scripts/kw_p9_8_product_release_hardening_closure_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )





    steps.append(
        GateStep(
            "Operator logging and Downloads policy",
            (python, "scripts/kw_operator_logging_policy_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "P10-3 Post-P9 artifact comparison report",
            (
                python,
                "scripts/kw_p10_3_post_p9_artifact_comparison.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "P10-4 Post-P9 human re-review capture workflow",
            (python, "scripts/kw_p10_4_post_p9_human_re_review.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "P10-5a GigaChat API golden benchmark contract",
            (python, "scripts/kw_p10_5a_gigachat_api_golden_benchmark.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "P10-5 Release decision dossier",
            (
                python,
                "scripts/kw_p10_5_release_decision_dossier.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )


    steps.append(

        GateStep(

            "P10-6 Human review packet export",

            (python, "scripts/kw_p10_6_human_review_packet_export.py", "--repo-root", str(repo_root), "--require-ready", "--json"),

            repo_root,

        )

    )

    steps.append(
        GateStep(
            "P10-7a Human review worksheet import validator",
            (
                python,
                "scripts/kw_p10_7a_human_review_worksheet_import_validator.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "P10-7 Human review results ingest",
            (
                python,
                "scripts/kw_p10_7_human_review_results_ingest.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "P10-8 Final release decision dossier",
            (
                python,
                "scripts/kw_p10_8_final_release_decision_dossier.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "P10-9 Targeted architecture rework",
            (
                python,
                "scripts/kw_p10_9_targeted_architecture_rework.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )



    steps.append(
        GateStep(
            "S1 Kimi Slides-class gap dossier",
            (
                python,
                "scripts/kw_s1_kimi_slides_gap_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "S2 Outline-first frontend workflow",
            (
                python,
                "scripts/kw_s2_outline_first_frontend_workflow_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "S3 Adaptive deck modes",
            (
                python,
                "scripts/kw_s3_adaptive_deck_modes_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "S4 Native table/chart/diagram rendering",
            (python, "scripts/kw_s4_native_visual_rendering_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "S5 Template and slide-master ingestion",
            (python, "scripts/kw_s5_template_master_ingestion_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "S6 Image/screenshot-to-slide workflow",
            (python, "scripts/kw_s6_image_to_slide_workflow_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "S7 Offline/intranet research citations",
            (
                python,
                "scripts/kw_s7_offline_research_citations_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "S8 Conversational edit loop",
            (
                python,
                "scripts/kw_s8_conversational_edit_loop_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "S9 Render-based visual QA",
            (python, "scripts/kw_s9_render_based_visual_qa_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "S10 Expanded Kimi-style benchmark and human review",
            (python, "scripts/kw_s10_kimi_style_benchmark_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "S11 S-phase closure dossier",
            (python, "scripts/kw_s11_s_phase_closure_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "S12 Selected benchmark execution packet",
            (python, "scripts/kw_s12_selected_benchmark_execution_packet_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "S13a Selected benchmark review packet skeleton",
            (
                python,
                "scripts/kw_s13a_selected_benchmark_review_packet_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "S13b Live public_api_dev GigaChat generation workflow",
            (
                python,
                "scripts/kw_s13b_live_gigachat_selected_benchmark_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "S13c Live GigaChat evidence packet export",
            (python, "scripts/kw_s13c_live_gigachat_evidence_packet_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "S13d Live benchmark prompt/schema hardening",
            (
                python,
                "scripts/kw_s13d_live_benchmark_prompt_schema_hardening_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
            ),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "S13e Hardened output repair/parser",
            (python, "scripts/kw_s13e_hardened_output_repair_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "S13f Strict per-scenario JSON rerun",
            (python, "scripts/kw_s13f_strict_json_per_scenario_rerun_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "S13g Canonical schema adapter minimal rerun",
            (
                python,
                "scripts/kw_s13g_canonical_schema_adapter_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
            ),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "S13h Targeted retry failed S13g scenarios",
            (python, "scripts/kw_s13h_targeted_s13g_retry_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "S13i Single-scenario executive memo retry",
            (python, "scripts/kw_s13i_single_scenario_retry_check.py", "--require-ready"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "S13j Deterministic executive memo salvage",
            (python, "scripts/kw_s13j_executive_memo_salvage_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "S13k Human review packet export from S13j",
            (
                python,
                "scripts/kw_s13k_human_review_packet_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "S13l Completed S13k review results ingest",
            (
                python,
                "scripts/kw_s13l_review_results_ingest_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "KQ-1B Executive memo actual PPTX generation",
            (
                python,
                "scripts/kw_kq1b_exec_memo_pptx_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "KQ-1C Independent PPTX render visual QA",
            (
                python,
                "scripts/kw_kq1c_independent_render_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                    "--allow-missing-render-stack",
                "--json",
            ),
            repo_root,
        )
    )
    return steps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the KW Studio P-phase production readiness final gate.")
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--checks-only", action="store_true", help="Only run static P-phase file and secret-marker checks.")
    parser.add_argument("--skip-backend", action="store_true", help="Skip backend pytest and compileall.")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend build and E2E smoke.")
    parser.add_argument("--skip-e2e", action="store_true", help="Skip frontend Playwright smoke.")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip deployment preflight static checks.")
    parser.add_argument("--require-clean-git", action="store_true", help="Fail if tracked local changes are present.")
    parser.add_argument(
        "--postgres-mode",
        choices=("safety", "optional", "required"),
        default="safety",
        help="How to run the Postgres integration gate.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()

    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}")
        return 2

    os.environ.setdefault("NEXT_TELEMETRY_DISABLED", "1")
    checks_only(repo_root)

    if args.checks_only:
        return 0

    steps = build_steps(repo_root, args)
    started = perf_counter()
    for step in steps:
        run_step(step)

    elapsed = perf_counter() - started
    print()
    print("=" * 96)
    print("[PRODUCTION READINESS GATE: PASS]")
    print(f"[INFO] completed {len(steps)} executable step(s) in {elapsed:.1f}s")
    print("=" * 96)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
