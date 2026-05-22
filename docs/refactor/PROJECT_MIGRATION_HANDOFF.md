# KW Studio Project Migration Handoff

**Purpose:** this is the durable handoff document for moving Knowledge_Work_Studio / KW Studio into another chat, another assistant account, or a fresh local development context.

**Update rule:** this document is part of the project, not a side note. Every future patch must review and update this file when the patch changes project status, rules, workflows, validation commands, operating profiles, architecture direction, accepted checkpoints, or the agreed plan for the next phase. It must be updated especially after the user and assistant agree on a new phase plan. A patch that changes project direction but does not update this handoff document is incomplete.

**Audience:** a senior engineer assistant that has no memory of previous conversations but needs to continue the project safely.

---

## 1. Current project identity

KW Studio is not a slide generator and not a simple chat wrapper around an LLM.

KW Studio is an **offline/intranet, artifact-first, provenance-first, operator-gated knowledge-work studio** for producing verifiable downloadable work products from source files, data, browser evidence, Python analysis, and local/intranet LLM assistance.

The core product direction is:

```text
source files + user intent
-> workflow plan
-> controlled deterministic tools
-> generated artifacts
-> validation / render / QA
-> provenance / citations / evidence
-> downloadable outputs
-> task history / artifact history / restore / audit
```

The mandatory first-class workflow pillars are:

```text
DOCX workflow
PDF workflow
XLSX / Excel workflow
Slides workflow
Python analysis workflow
Browser-assisted evidence workflow
```

XLSX / Excel is mandatory, not optional. Slides are high priority, but slides are one pillar of the product, not the whole product.

---

## 2. Current accepted continuation status

Current active branch:

```text
9_Product_Release_Hardening
```

Current accepted remote baseline at the time this document was introduced:

```text
accepted checkpoint: KR-4A
accepted commit short id: 3eaa9f8
accepted subject: KR-4A add workflow contract core
```

Current phase being prepared after this handoff update:

```text
phase: KR-5A
subject: XLSX inspect workflow
intent: add first concrete XLSX / CSV inspect runtime with workbook metadata, formulas, table previews, manifests, provenance, and quality report artifacts
```

Do not rely on this status blindly in future chats. Always verify the current remote state before creating a patch:

```bash
git fetch origin 9_Product_Release_Hardening
git status --short --branch
git rev-parse --short HEAD
git rev-parse --short origin/9_Product_Release_Hardening
git log --oneline -5
```

When direct Git access is unavailable in the assistant environment, verify the public GitHub commit page through web access and state the limitation honestly.

Accepted high-level KR history after the project reset work resumed:

```text
KR-3D: documented current continuation checkpoint and added project-resident validation runners
KR roadmap/render-stack: documented product reset scope and declared required LibreOffice/poppler render stack
KR-3E: removed first active gate references to legacy baseline-pinned stage scripts
KR-3F: archived inactive root historical prompt packs in a controlled batch
KR-4A: added workflow contract core
```

Next planned product direction after KR-4A:

```text
KR-5A: XLSX inspect workflow — in progress for this patch
KR-5B: XLSX validation and artifact bundle
KR-6A: source-grounded Slides continuation
```

Before starting the next feature phase, check whether any emergency hotfix or user-agreed plan superseded this sequence.

---

## 3. Development profiles and local-only paths

The project is developed across three user profiles. These paths are **local-only operator details** and must not be hardcoded into portable product code, tests, or active product documentation except in explicitly local runner scripts or migration instructions.

### Profile 1 local-only paths

```text
machine: Ubuntu 24.04.4 on Huawei laptop
repo: /home/su4ka/workplace/Knowledge_Work_Studio
downloads: /home/su4ka/Загрузки
logs: /home/su4ka/workplace/Knowledge_Work_Studio/logs
```

### Profile 2 local-only paths

```text
machine: Ubuntu 24.04.2 on VMware / Windows 10
repo: /home/editor/workplace/Knowledge_Work_Studio
downloads: /home/editor/Загрузки
logs: /home/editor/workplace/Knowledge_Work_Studio/logs
```


### Profile 3 local-only paths

```text
machine: Ubuntu 26.04 LTS on VMware Workstation 17 Pro / Windows 10 host
repo: /home/su4ka/workplace/Knowledge_Work_Studio
downloads: /home/su4ka/Загрузки
logs: /home/su4ka/workplace/Knowledge_Work_Studio/logs
setup scripts: scripts/bootstrap/profile3_ubuntu2604_project_bootstrap.sh, scripts/bootstrap/profile3_ubuntu2604_terminal_theme.sh
rules: same paths and logging rules as Profile 1
```

Both profiles may have proxy environment variables configured. Runner scripts must inherit, not erase:

```text
http_proxy
https_proxy
HTTP_PROXY
HTTPS_PROXY
NO_PROXY
no_proxy
```


### Profile-neutral operation rule

Profile 1 and Profile 3 are parallel working profiles. The project must not depend on a single main profile.

The assistant may continue development from Profile 1 or Profile 3 depending on where the user is working. Profile-specific absolute paths are allowed in local bootstrap/apply runner scripts and in this migration handoff document, but product code, Dockerfiles, reusable tests, product documentation, and production readiness gates must remain profile-neutral and portable.

When switching profiles, always verify the current remote HEAD, local HEAD, branch, working tree state, logs directory, and active Python virtual environment before preparing or applying the next patch.

---

## 4. Non-negotiable project rules

### 4.1 Always check actual repository state

Before creating a patch:

```text
verify current remote HEAD;
verify local branch;
verify working tree clean/dirty state;
if dirty, identify whether it is intended partial patch state;
do not assume a patch applies to a clean base if the user already applied part of it;
build and test against the actual expected state.
```

### 4.2 Do not delete blindly

The cleanup sequence is:

```text
audit
policy map
replacement coverage
active gate retirement
controlled archive/delete batch
full runner
Docker smoke
```

`docs/codex` is deprecated development history but must not be physically moved or deleted until direct checker/test dependencies are retired.

### 4.3 No unsupported claims

Do not claim any of these without evidence artifacts and logs:

```text
Kimi-level quality
selected parity
full offline workflow parity
Server 3 local_intranet proof
human approval
```

The default production/offline LLM direction is direct local GigaChat on Server 3. LiteLLM is optional gateway infrastructure, not a replacement for GigaChat. Ollama/local models are fallback/dev/experimental unless separately accepted.

### 4.4 No uncontrolled dependency fixes

Never run:

```text
npm audit fix --force
```

unless the user explicitly asks for a controlled dependency/security patch and the risk is reviewed.

### 4.5 Full and Docker smoke runners are project-resident

Full runner and Docker smoke runner entrypoints must live inside the repository and be committed:

```text
scripts/kw_product_full_runner_logged.sh
scripts/kw_product_docker_smoke_logged.sh
```

External scripts from a downloads directory are allowed only as bootstrap helpers, recovery helpers, or patch-application wrappers. They are not the final validation contract.

### 4.6 Logs are mandatory artifacts

Every patch/recovery/test runner must:

```text
write a log under the profile's project logs directory;
duplicate output to the terminal;
archive the raw log as .log.tar.gz;
remove the raw .log after archiving;
print the archive path;
keep generated report directories in the archive when applicable.
```

After the user uploads log archives, the assistant must analyze them before deciding ACCEPT/FAIL/hotfix.

---

## 5. How patches must be produced

Every patch response should explain, in simple language:

```text
what problem this solves;
why it is needed now;
what it changes;
what it intentionally does not change;
what the acceptance criteria are;
what was tested locally;
what remains out of scope.
```

Preferred output format:

```text
downloadable .patch file;
downloadable profile runner .sh file;
short command block in chat showing exactly how to run the script;
follow-up commands for project-resident full runner and Docker smoke.
```

Do not bury commands only inside attachments. The user should always see the exact command in chat.

Patch quality expectations before giving files to the user:

```text
inspect actual repo state when possible;
run git apply --check locally when feasible;
run git diff --check;
run py_compile for changed Python files;
run targeted checker scripts;
run targeted pytest when tests are added/changed;
run bash -n for shell scripts;
state clearly what was not tested locally.
```

If a patch fails, do not chain blind hotfixes. Read the logs, identify root cause, reproduce the expected state if possible, then produce a checked hotfix patch.

---

## 6. Acceptance process

A phase or patch is not ACCEPT until all of these are true:

```text
targeted checks pass;
commit exists;
push succeeds;
remote is verified;
full runner passes on committed HEAD;
Docker smoke passes on the same committed HEAD;
logs are reviewed for errors and obvious secret exposure;
working tree is clean or generated files are explicitly restored/acknowledged.
```

Use these labels consistently:

```text
TARGETED PASS: patch applied and targeted checks passed locally.
LOCAL ACCEPT: targeted checks, full runner, and Docker smoke passed on committed local HEAD.
REMOTE ACCEPT / CLOSED: commit has been pushed and verified on remote.
FAIL: logs show a real project or environment failure.
RUNNER BUG: failure is in the helper script, not the project; fix the runner and rerun.
```

Do not push before targeted checks. Do not declare remote closure before checking GitHub/remote state.

---

## 7. Local assistant workflow

When the assistant can maintain a local project copy, it should:

```text
restore or clone the project locally;
checkout the active branch;
verify remote HEAD through Git or web;
apply accepted patch history if the local bundle is stale;
create patches against the current accepted base;
run git apply --check before giving the patch;
run targeted validations before giving the patch;
be honest if direct Git fetch is unavailable.
```

In this environment, direct `git fetch` from GitHub may fail because of DNS/network restrictions. When that happens, the assistant should use the latest uploaded bundle plus accepted patch files, and verify public GitHub commits through web browsing. State this limitation clearly.

---

## 8. Current product architecture direction

### 8.1 Workflow contract core

KR-4A introduced the product-facing contract vocabulary:

```text
WorkflowInput
WorkflowPlan
WorkflowRun
WorkflowArtifact
WorkflowManifest
WorkflowQualityReport
WorkflowProvenance
WorkflowContractCore
```

Core files:

```text
backend/app/workflows/core_contracts.py
docs/architecture/WORKFLOW_CONTRACT_CORE.md
scripts/kw_workflow_contract_core_check.py
```

Future workflows should converge on this vocabulary rather than inventing isolated manifests.

### 8.2 Render stack is a system dependency

LibreOffice/render stack is not optional for the product. It is required for Slides render QA.

Project files:

```text
infra/system-packages/ubuntu-render-stack.txt
scripts/dev/install_system_dependencies_ubuntu.sh
scripts/kw_system_dependencies_check.py
Dockerfile.backend
```

The required render path is functional, not just binary presence:

```text
PPTX -> LibreOffice PDF -> poppler/pdftoppm PNG -> non-empty rendered output
```

### 8.3 Production readiness gate direction

The production gate should increasingly validate product/reset contracts instead of historical stage-specific proofs.

Already moved forward:

```text
KR-3E removed the first active gate references to retired baseline-pinned legacy stage scripts.
KR-3F introduced controlled archive/delete readiness.
KR-4A introduced workflow contract core guardrails.
```

More legacy stage-named checks remain. Future cleanup should continue in small batches with replacement coverage and full/Docker closure.

---

## 9. Documentation map

Active product documentation should live under:

```text
docs/product/
docs/architecture/
docs/workflows/
docs/quality/
docs/operators/
docs/refactor/
```

Important anchors:

```text
docs/refactor/KR_PRODUCT_RESET_ROADMAP.md
docs/refactor/PROJECT_MIGRATION_HANDOFF.md
docs/architecture/WORKFLOW_CONTRACT_CORE.md
docs/refactor/CONTROLLED_ARCHIVE_DELETE_READINESS.md
docs/refactor/ACTIVE_GATE_LEGACY_RETIREMENT.md
docs/refactor/PATH_PORTABILITY_CLEANUP_PLAN.md
```

`docs/codex` is deprecated development history. It remains in place until direct dependencies are cleared.

---

## 10. Current next-phase plan template

Every time the user and assistant agree on a new phase, update this section.

Current next intended phase after this handoff document:

```text
phase: KR-5A
name: XLSX inspect workflow
purpose: implement the first concrete XLSX inspect workflow on top of KR-4A contract core
expected outputs: workbook manifest, xlsx analysis report, formula inventory, table previews, source evidence manifest, artifact manifest, quality report
non-goals: do not build destructive workbook editing yet; do not skip provenance/quality contracts; do not treat XLSX as optional
closure: targeted checks, commit, push, full runner, Docker smoke, log review
```

If the user changes the plan, revise this section before or inside the next patch.

---

## 11. Minimal migration prompt for a new assistant

A new assistant should be told:

```text
You are continuing Knowledge_Work_Studio / KW Studio.
Answer in Russian by default unless the user requests an English artifact.
Act as senior engineer and teacher.
Explain every patch simply before commands.
Check GitHub/remote HEAD before every patch.
Use the current user profile paths only in local runner scripts, not product code.
Keep logs under the active profile's project logs directory.
Archive logs as .log.tar.gz and remove raw .log files.
Use project-resident full and Docker smoke runners.
Do not move docs/codex until dependencies are retired.
Do not make Kimi/offline/GigaChat parity claims without evidence.
Keep DOCX, PDF, XLSX/Excel, Slides, Python analysis, and Browser evidence as mandatory pillars.
After every agreed new phase plan, update docs/refactor/PROJECT_MIGRATION_HANDOFF.md.
Do not declare ACCEPT without targeted checks, commit, push, full runner, Docker smoke, and log review.
```

The assistant should first read this document, then inspect:

```text
docs/refactor/KR_PRODUCT_RESET_ROADMAP.md
docs/architecture/WORKFLOW_CONTRACT_CORE.md
scripts/kw_production_readiness_gate.py
scripts/kw_product_full_runner_logged.sh
scripts/kw_product_docker_smoke_logged.sh
```

---

## 12. Handoff maintenance checklist for future patches

Before sending a patch, ask:

```text
Does this patch change accepted status, current phase, next phase, project rules, workflow contracts, validation commands, profiles, dependencies, or operator procedure?
```

If yes, update this handoff document in the same patch.

A future patch should usually include a short entry here:

```text
YYYY-MM-DD / phase / commit short id after accept / what changed / what remains next
```

Initial entry:

```text
2026-05-20 / KR handoff anchor / pending commit / created durable migration handoff document and guardrail / next: KR-5A XLSX inspect workflow
```


## 15. KR-5A XLSX inspect workflow handoff update

KR-5A starts the first concrete spreadsheet runtime after the KR-4A workflow contract core. The work must remain inspect-only and non-destructive. It should not claim complete Excel feature coverage. The required implementation surface is:

```text
backend/app/services/xlsx_service/
scripts/kw_xlsx_inspect_workflow_check.py
backend/tests/workflows/test_xlsx_inspect_workflow.py
backend/tests/quality/test_xlsx_inspect_artifact_bundle.py
backend/tests/smoke/test_xlsx_inspect_workflow_smoke.py
```

The expected bundle contract is:

```text
workbook.xlsx or workbook.csv
workbook_manifest.json
xlsx_analysis_report.json
formula_inventory.json
table_previews/*.csv
source_evidence_manifest.json
artifact_manifest.json
quality_report.json
```

Before KR-5A can be accepted, `scripts/kw_xlsx_inspect_workflow_check.py --require-ready`, targeted pytest, project-resident full runner, project-resident Docker smoke, log review, clean working tree, commit, push, and remote verification must all pass.


## 16. Profile 3 Ubuntu 26.04 LTS bootstrap handoff update

Profile 3 is a new local development profile:

```text
machine: Ubuntu 26.04 LTS on VMware Workstation 17 Pro / Windows 10 host
repo: /home/su4ka/workplace/Knowledge_Work_Studio
downloads: /home/su4ka/Загрузки
logs: /home/su4ka/workplace/Knowledge_Work_Studio/logs
path/log rules: same as Profile 1
```

The project now carries two versioned bootstrap scripts for Profile 3:

```text
scripts/bootstrap/profile3_ubuntu2604_project_bootstrap.sh
scripts/bootstrap/profile3_ubuntu2604_terminal_theme.sh
```

The project bootstrap script updates Ubuntu packages, installs required developer/system/render/Docker packages, prepares GitHub SSH access, clones or updates the repository over SSH, creates `.venv`, installs Python/frontend dependencies, creates runtime storage directories, runs project system dependency checks, and archives its log.

The terminal theme script configures terminal syntax-highlighting tooling and GNOME Terminal dark colors with 50 percent transparency where supported by the GNOME/Wayland compositor.

Future setup changes for Profile 3 must update this handoff section and the versioned bootstrap scripts together.


## Profile 3 bootstrap scripts

Profile 3 setup scripts are versioned inside the repository for repeatable setup and audit:

```text
scripts/bootstrap/profile3_ubuntu2604_project_bootstrap.sh
scripts/bootstrap/profile3_ubuntu2604_terminal_theme.sh
```

These scripts are operator bootstrap helpers. They are allowed to contain Profile 3 local paths because they are explicitly local setup entrypoints. They must preserve proxy environment variables and write/archive logs under the active project logs directory or the bootstrap fallback logs directory if clone has not completed yet.


## Profile-neutral SQLite repository directory hotfix

Profile 1 and Profile 3 are parallel working profiles. Runtime and test infrastructure must not depend on one profile having pre-created storage or SQLite directories that another fresh clone does not have.

The SQLite repository layer must create the database parent directory immediately before connecting, and the project-resident full runner must create local runtime storage directories before tests. This keeps fresh Profile 3 clones and existing Profile 1 worktrees behaviorally equivalent.

Acceptance for this hotfix remains the normal project rule: targeted repository/API tests, full runner, Docker smoke, clean tree, commit, push, and remote verification.


## Profile-neutral runner resource limits

Fresh Ubuntu VM profiles may have low default open-file limits. The project-resident full runner must raise the process-local nofile limit before running large pytest suites. This is profile-neutral infrastructure hardening, not a Profile 1 or Profile 3 special case.

The contract is:

```text
scripts/kw_full_tests_with_proxy_runner.sh uses KWS_NOFILE_LIMIT;
default requested nofile limit is 65535;
the runner prints nofile_limit in logs;
manual shell ulimit changes must not be required for normal project validation.
```

If a future profile still fails with `Too many open files`, first inspect the runner log for `nofile_limit`, then raise `KWS_NOFILE_LIMIT` for that run only before changing product code.


## Profile-neutral Playwright browser bootstrap

Fresh cloned VM profiles may have npm packages installed but no Playwright browser binary in the user cache. The project-resident full runner must install the Chromium browser required by frontend E2E smoke before running Playwright tests. This is profile-neutral infrastructure hardening, not a Profile 3 special case.

The contract is:

```text
scripts/kw_full_tests_with_proxy_runner.sh runs npx playwright install chromium after npm ci;
frontend E2E chooses test:e2e, e2e, or npx playwright test based on package.json scripts;
the runner must not blindly call a missing npm e2e script after test:e2e fails;
manual npx playwright install must not be required for normal project validation.
```

If a future profile fails with `Executable doesn't exist` under `.cache/ms-playwright`, inspect the full runner log for the `20b-frontend-playwright-browser-install` step before changing product code.

## KR-5B XLSX validation and artifact bundle hardening handoff update

KR-5B builds on KR-5A. It does not add destructive workbook editing and does not claim complete Excel feature coverage.
It adds profile-neutral validation for the XLSX inspect artifact bundle.

The implementation surface is:

```text
backend/app/services/xlsx_service/validator.py
scripts/kw_xlsx_validation_bundle_check.py
backend/tests/quality/test_xlsx_validation_bundle_hardening.py
backend/tests/smoke/test_xlsx_validation_bundle_check.py
```

The key product rule is bundle validation, not only workbook parsing:

```text
required artifacts must exist;
artifact_manifest.json must list them;
size and sha256 metadata must match actual artifacts;
artifact_manifest.json must use explicit self_reference semantics;
formula inventory must be traceable;
table previews must be traceable from source_evidence_manifest.json;
quality_report.json must fail closed;
inspect workflow remains non-destructive.
```

Future XLSX work should build on this validation layer before adding edit, repair, chart, pivot, or cross-workflow export features.


## 16. KR-5B wording hotfix handoff update

KR-5B introduced XLSX bundle validation hardening. A follow-up hotfix removed a forbidden product-claim phrase from XLSX documentation because the legacy KR-2F scanner treats that phrase as unsupported even when it appears in a negative sentence. Future documentation should avoid using blocked positive-claim tokens verbatim; use wording such as `complete Excel feature coverage` when explaining non-goals.

## 17. KR-6A source-grounded Slides continuation handoff update

KR-6A starts the source-grounded Slides continuation after KR-5B. It does not try to solve every presentation rendering problem at once. The phase adds a deterministic Slides grounding bundle that validates slide-level citations, source evidence mapping, artifact manifest completeness, and fail-closed quality reporting.

Implementation surface:

```text
backend/app/services/slides_service/source_grounded_continuation.py
scripts/kw_slides_source_grounded_continuation_check.py
backend/tests/workflows/test_slides_source_grounded_continuation.py
backend/tests/quality/test_slides_source_grounding_quality.py
backend/tests/smoke/test_slides_source_grounded_continuation_smoke.py
```

Expected artifacts:

```text
slide_plan.json
citation_manifest.json
source_evidence_manifest.json
quality_report.json
artifact_manifest.json
```

Non-goals: KR-6A does not claim OCR, arbitrary figure extraction, unsupported table extraction, visual QA completion, or complete presentation feature coverage. It prepares the evidence/citation layer that later Slides render and visual QA work must consume.

## KR-6B Slides render/visual QA bundle handoff update

KR-6B follows KR-6A by hardening the Slides bundle contract with render artifacts, independent render artifacts, geometry metadata, visual QA report, and manifest validation.

Implementation surface:

```text
backend/app/services/slides_service/render_visual_qa_bundle.py
scripts/kw_slides_render_visual_qa_bundle_check.py
backend/tests/workflows/test_slides_render_visual_qa_bundle.py
backend/tests/quality/test_slides_render_visual_qa_quality.py
backend/tests/smoke/test_slides_render_visual_qa_bundle_smoke.py
```

Expected KR-6B artifacts:

```text
slide_plan.json
citation_manifest.json
source_evidence_manifest.json
render_manifest.json
geometry_report.json
visual_qa_report.json
quality_report.json
artifact_manifest.json
rendered_slides/*.png
independent_rendered_slides/*.png
```

KR-6B remains a checked bundle-hardening step. It must not be described as broad presentation feature coverage or as a replacement for later real PPTX render integration.

KR-6B repair note: artifact_manifest.json is self-referential, so its own hash and size must be represented by explicit self_reference metadata rather than a fake manifest entry. Render, geometry, citation, source evidence, visual QA, and quality artifacts must still have real size and sha256 records.

## KR-6B hygiene follow-up: Slides service export formatting

After KR-6B was accepted, `backend/app/services/slides_service/__init__.py` remained functional but visually dense because the render/visual QA exports were added in a compressed import/export form. The hygiene follow-up reformats this file into readable multiline imports and adds a smoke regression that prevents the import block from collapsing back into one long line.

This change is intentionally logic-neutral: it must not change the Slides render/visual QA bundle contract, source-grounded Slides contract, production gate semantics, or any runtime behavior. Acceptance still requires targeted checks, full runner, Docker smoke, log review, push, and remote verification.

## 18. Full-runner log isolation hygiene

After the KR-6B formatting hygiene patch, Profile 3 exposed a full-runner logging robustness issue: smoke tests can interfere with repository-local transient log directories. The project-resident full runner now writes step logs to a private temporary work directory and archives the final `full-tests-*.zip` under the repository `logs` directory. This keeps the external artifact contract unchanged while preventing tests from deleting the runner's active per-step logs.

## 16. Profile-neutral S2 lineage diagnostics hardening

The old S2 outline-first frontend workflow checker still references a historical S1 baseline commit. That historical lineage check must not behave like a modern profile-specific or shallow-clone blocker on the product-reset branch.

Current policy:

```text
S2 legacy lineage check is advisory on the product-reset branch when the old baseline object is unavailable or no longer a direct ancestor.
S2 must still validate current product files, plan-first replacement checks, safe task events, render modes, and offline/frontend workflow contracts.
S2 must emit machine-readable JSON diagnostics on every failure path.
```

This rule prevents old stage-history Git assumptions from hiding real product failures during Profile 1 / Profile 3 switching.

## Profile 3 real-user deploy test: Postgres task creation SQL alignment

During Profile 3 local deploy testing with GigaChat credentials, the operator could create a session through the running Postgres-backed deployment, but `POST /tasks` returned HTTP 500 before any slide generation could start. The root cause was a Postgres task repository SQL placeholder alignment bug: the `status` value was accidentally bound to the `result_json` JSONB placeholder in `PostgresTaskRepository.create`.

The hotfix contract is:

```text
POST /tasks must work in the real Postgres-backed deploy profile, not only in sqlite/unit tests;
task status and result_json placeholders must remain separate;
regression coverage must validate the SQL binding order without requiring a live Postgres instance;
real-user testing should resume from session/task creation after this repair is locally accepted.
```

This is a real product/runtime bug found by user-side testing, not an operator mistake.

## Dependency audit CLI help wording hotfix

Profile 3 full-runner validation on the Postgres task SQL hotfix exposed a small CLI/help regression: `backend/tests/smoke/test_r8_dependency_audit.py::test_r8_dependency_audit_help_mentions_no_network_baseline` requires `scripts/kw_dependency_audit.py --help` to explicitly state that the baseline audit runs without network access. The hotfix restores that operator-facing wording without changing dependency policy, package baselines, runtime logic, or npm audit behavior.

Acceptance for this hotfix follows the normal rule: targeted dependency-audit smoke tests, handoff check, full runner, Docker smoke, clean tree, push, and remote verification.


## Real-user Slides prompt quality failure and KR-6C direction

Profile 3 real-user testing after the GigaChat Authorization Key deployment proved that the runtime, Postgres task creation, artifact download, and GigaChat probe can pass while the user-facing Slides output is still unacceptable. The uploaded evidence showed a prompt-only deck request for six slides producing five slides, prompt echo, `Additional insight` placeholders, and the internal deterministic image source label in the PPTX.

KR-6C starts the real-user Slides generation MVP hardening path. The immediate contract is deliberately bounded:

```text
user-requested slide count must be respected when present;
public PPTX text must not contain prompt echo, placeholder fallback text, or internal deterministic source labels;
GigaChat/LLM planning may be used when runtime credentials are configured, but its JSON plan must be validated before use;
invalid or unavailable LLM plans must fall back to a cleaner deterministic user-prompt plan with explicit planning metadata, not to placeholder leakage;
full presentation feature coverage, arbitrary template understanding, and broad visual design quality remain future work.
```

Acceptance for KR-6C-style work still follows the normal project rule: targeted API/workflow tests, handoff check, full runner, Docker smoke, clean tree, push, and remote verification before closure.

## KR-6C media baseline smoke repair

The first KR-6C real-user Slides prompt planning patch correctly removed prompt echo, placeholder leakage, and the internal deterministic image source label from public PPTX text, but it accidentally removed generated media image specs from the new user-prompt plan path. Legacy RF2.1 inventory smoke still requires at least one generated media asset to prove the baseline local PPTX runtime surface remains present.

The repair keeps KR-6C user-facing quality guardrails while restoring local deterministic image specs with no public internal source label. Future Slides prompt-quality work must preserve both contracts: no placeholder/internal-label leakage in the PPTX, and no accidental retirement of the baseline media generation surface unless the RF2 legacy gate is formally retired with replacement coverage.

## Senior engineering patch-discipline correction

2026-05-21 / process hardening / user correction after KR-6C repair churn / mandatory future-assistant rule.

The user explicitly corrected the engineering process after a sequence of too-narrow and brittle KR-6C repair attempts. This correction is part of the migration handoff and must be treated as a mandatory operating rule for all future patches.

Before proposing or applying any future patch, the assistant must work at senior-engineer level and must not rely on shallow targeted edits. The required process is:

```text
1. Analyze the actual failing logs, artifacts, API responses, and repository state before deciding on a fix.
2. Audit all directly related files, call sites, compatibility tests, smoke tests, readiness gates, product documentation, and historical workflow contracts affected by the problem.
3. Map compatibility risks before changing shared services. For example, a Slides planner change must be checked against real-user prompt generation, source-aware generation, RF2/RF2.1 media baseline, render/visual QA, artifact manifests, and API schema tests.
4. Prefer small but complete repairs over brittle hotfixes. Do not use fragile text-anchor patchers for non-trivial code changes unless the patcher first proves the exact expected pre-state and exits before modifying anything on mismatch.
5. Check syntax and importability of changed code locally before giving the patch to the user. Python changes need py_compile/import checks; shell changes need bash -n; frontend changes need the relevant npm/type/build checks.
6. Run the relevant targeted tests/checkers on the locally checked-out project version before delivering the patch. Do not claim a patch is ready merely because it is conceptually plausible.
7. Do not introduce temporary workarounds, hidden behavior changes, or unreliable route guards that bypass product contracts. If a compatibility path is needed, document the routing rule and cover both old and new behavior with tests.
8. If a runner fails after partially modifying the tree, the next action must first cleanly classify and repair that partial state before applying another change.
9. A patch that fixes a user-visible quality defect must include explicit regression checks for the user-visible failure mode, not only backend internals.
10. Full runner and Docker smoke remain mandatory before LOCAL ACCEPT; push and remote verification remain mandatory before REMOTE ACCEPT / CLOSED.
```

This correction raises the quality bar. It is not a waiver for faster patching and must not be bypassed when the user asks for speed.

## KR-6C source-mode Slides routing repair

KR-6C real-user prompt planning must not globally replace legacy/source-aware Slides planning. The accepted routing contract is source-mode-aware:

```text
prompt_only + explicit real-user presentation/deck generation intent -> KR-6C user prompt planner
prompt_only + short/source-like outline text -> legacy outline-first planner
uploaded_source / stored_source -> legacy source-preserving outline-first planner
direct internal calls with source_refs or non-default templates -> legacy baseline planner
```

This keeps the real-user quality guardrails from KR-6C while preserving K2 source-aware API behavior, RF2/RF2.1 media baseline smoke, source grounding metadata, and artifact manifest/render QA contracts. Future Slides repairs must audit all of these contracts together before changing routing.

## Global deploy Postgres volume credential-drift guardrail

This rule is global, cross-platform, and profile-neutral. It was first reproduced on Profile 3, but future assistants must not document or implement it as a Profile 3-only workaround.

Failure mode:

```text
A deploy env file is regenerated with a new POSTGRES_PASSWORD.
Only Docker containers are removed or recreated.
The existing Postgres metadata volume is kept.
Postgres still stores the old database password inside the existing volume.
The backend reads the new password from the regenerated env file.
The backend cannot authenticate and becomes unhealthy.
```

Global rule:

```text
When a deploy env file is regenerated, runners and operator instructions must not recommend container-only cleanup as sufficient for Postgres-backed deploys.
They must either preserve the previous POSTGRES_PASSWORD or perform an explicit operator-confirmed Postgres metadata volume reset/migration.
Storage/artifact volumes must not be deleted as a side effect of fixing metadata password drift.
```

Project-resident helper:

```text
scripts/deploy/kw_postgres_volume_guardrail.py
```

The helper is intentionally cross-platform: it uses Python subprocess calls and Docker Compose labels instead of shell pipelines, xargs, Linux-only assumptions, or profile-specific paths. It requires `--confirm-reset-postgres-volume` before removing the Postgres metadata volume and must never print `.env.deploy`, Authorization Key, access tokens, GigaChat secrets, or `POSTGRES_PASSWORD`.

Future deploy/start/restart runners that regenerate deploy credentials must call this rule out explicitly. A future hardening patch should prefer preserving the previous `POSTGRES_PASSWORD` when safely available, and use volume reset only when the operator intentionally accepts metadata reset for a test/local deploy.

## Global local-state-aware patch planning rule

This rule is global, cross-platform, and profile-neutral. It applies before pull, before dependency checks, before deploy/start instructions, and before every patch runner.

Before changing files or choosing tests, the assistant must audit and record the actual local profile state, not an assumed clean clone. The minimum local-state audit is:

```text
current branch and local HEAD before fetch or pull
working tree status and dirty scope
generated files that may be modified by builds
presence or absence of expected project files
presence or absence of local-only env/deploy files
active containers, compose projects, volumes, ports, and runtime health when deploy behavior is relevant
recent logs or user-provided command output that proves what has actually been run
local Python, Node, Docker, render-stack, and Playwright state when dependencies or tests are relevant
```

Patch selection, test selection, and repair strategy must be based on that audited state. Future runners must not assume that a profile has the same files, env files, containers, volumes, caches, virtual environment, `node_modules`, or generated artifacts as another profile.

Before producing or applying a patch, the assistant must audit the related implementation surface and contracts for the specific problem. This includes directly related source files, entrypoints, repositories, services, tests, smoke checks, production gates, documentation, and previously uploaded logs or artifacts. Patches must be checked against the current file contents and must not rely on brittle text anchors when a safer structural update is possible.

Every patch must be reviewed for correctness, contract fit, syntax, importability, and wording quality before it is handed to the user. Documentation, comments, CLI help, operator messages, and user-facing text must be checked for spelling mistakes, accidental profile-specific wording, stale claims, and terminology drift. Incorrect spellings of key terms must not be introduced into project files; use `offline` and `senior engineer`.

If the actual local state does not match the expected base, the assistant must stop, explain the mismatch, and either prepare a state-repair runner or ask for the missing evidence. Do not continue by assuming the filesystem, runtime, or dependency state.

## Global LLM runtime endpoint-scope guardrail

Runtime endpoint privacy checks must be scoped to the active LLM transport selected by `LLM_PROVIDER` and `LLM_TRANSPORT_MODE`.

For `direct_gigachat`, the active runtime endpoints are `GIGACHAT_API_BASE_URL` and `GIGACHAT_AUTH_URL`.
For `litellm_gateway`, the active runtime endpoint is `LITELLM_GATEWAY_URL`; inactive direct GigaChat defaults must not block the explicit internal LiteLLM gateway transport.
For fallback or experimental transports, validation must remain fail-closed for production/offline use and must not silently route to public internet services.

This rule is global and profile-neutral. It was captured after Profile 1 full-runner smoke tests showed that `build_llm_provider()` rejected the optional internal LiteLLM gateway path because inactive direct GigaChat public defaults were checked as if they were active runtime endpoints.

The separate public internet GigaChat Authorization Key test mode is still required and must be implemented explicitly later. Do not hide public internet tests behind manual `APP_ENV=development` edits or claim offline/intranet proof from public endpoint probes.

## Global API test runtime isolation rule

API route tests must not inherit production runtime defaults from an operator shell, CI host, or local profile. The API test suite is a test-mode contract surface: it uses SQLite repositories, local temporary storage, and fake LLM wiring unless a specific test explicitly overrides those defaults.

Required API test defaults are:

```text
APP_ENV=test
METADATA_BACKEND=sqlite
SQLITE_RUNTIME_ALLOWED=true
STORAGE_BACKEND=local
LLM_PROVIDER=fake
```

This rule protects production/offline guardrails from being weakened while keeping test suites deterministic. Production runtime must still reject SQLite metadata truth and unsupported fake/noop LLM providers when `APP_ENV=production`. Future patches that add API tests must use the shared API test isolation fixture instead of copying partial environment setup into each test file.

When a full runner fails because test code inherited `APP_ENV=production`, fix the test isolation boundary, not production guardrails.

## Global API test environment non-leakage rule

API test isolation must not pollute the wider backend pytest process. API tests may need test-mode environment variables before importing the FastAPI app, but those import-time variables must be restored immediately after import. Function-scoped API fixtures may then use pytest monkeypatch for each API test.

This prevents API test defaults such as `APP_ENV=test`, `METADATA_BACKEND=sqlite`, and `LLM_PROVIDER=fake` from leaking into integration, smoke, CLI, diagnostics, or full-suite subprocess tests. CLI tests that pass an explicit `--env-file` must not be overridden by leftover parent-process test variables.

Future patches that modify API test isolation must prove both directions:

```text
API tests still run in test mode with SQLite and fake LLM wiring.
Non-API tests and CLI subprocess checks do not inherit API test defaults.
Production/offline guardrails remain strict.
```

Unit or integration tests that instantiate `Settings()` directly must not accidentally inherit operator production/offline defaults when they are testing development/test factory behavior. Such tests must pass an explicit `app_env="test"` or explicit production-safe private/internal endpoints, depending on the contract being tested. This keeps production guardrails strict while preventing local operator environment from changing unit-test intent.

## Global explicit app environment rule for direct Settings tests

Direct unit, integration, smoke, and API tests that instantiate `Settings(...)` must set `app_env` explicitly when they validate a non-production contract. This rule is global and profile-neutral. Tests must not inherit the operator shell environment implicitly, because full-runner execution may contain production/offline defaults even when the test is validating SQLite, fake LLM, or development/test behavior.

Required policy:

```text
SQLite success-path tests must pass app_env="test" or app_env="development" explicitly.
Fake/noop LLM factory tests must pass app_env="test" explicitly.
Production/offline guardrail tests must pass app_env="production" and production-safe endpoints explicitly.
Do not weaken production guardrails to satisfy test setup.
Do not rely on ambient APP_ENV inherited from the shell, CI, local profile, or previous test module.
When a full-runner failure shows Settings(app_env="production", metadata_backend="sqlite"), audit direct Settings constructors before changing product code.
```

This rule complements the API test-environment isolation rule: API fixtures may set scoped test defaults, but tests outside that fixture layer must still make their intended runtime mode explicit.


## Global public internet GigaChat test mode rule

Public internet tests against the external GigaChat API must use an explicit, profile-neutral runtime mode rather than ad-hoc `APP_ENV=development` overrides.

The supported operator test mode is:

```text
GIGACHAT_RUNTIME_MODE=public_internet_test
```

This mode is only for temporary operator internet tests with public GigaChat endpoints and a real Authorization Key-derived credential pair. It is not production readiness evidence, not offline/intranet deployment proof, and not a substitute for the later strict offline endpoint policy.

The normal production/offline profile remains:

```text
DEPLOYMENT_MODE=offline_intranet
GIGACHAT_RUNTIME_MODE=offline_intranet
LLM_PROVIDER=gigachat
LLM_TRANSPORT_MODE=direct_gigachat
```

Patch and deploy runners must not ask operators to bypass runtime guardrails by manually editing `APP_ENV=development`. Instead, they must set or validate the explicit public internet test mode and keep secret values redacted. When the deploy env file is regenerated, the global Postgres metadata volume guardrail still applies: preserve the existing `POSTGRES_PASSWORD` or explicitly reset/migrate the Postgres metadata volume with operator confirmation.

Strict rejection of public endpoints in the offline/intranet runtime mode must be preserved and can be tightened when the project reaches `kimi_level true` and the offline deployment preparation phase.


## Global public internet GigaChat test mode and local env isolation rule

The explicit public GigaChat test mode must also be respected by diagnostic and topology checkers that inspect deploy env files. `GIGACHAT_RUNTIME_MODE=public_internet_test` is allowed only for operator internet tests with direct GigaChat transport and must be reported as not being offline/intranet proof.

Tests or checkers whose contract refers to `.env.deploy.example` must pass that file explicitly and must not accidentally read an operator-local `.env.deploy` containing real secrets or temporary public endpoint settings. Local secret env files are runtime evidence, not deterministic test fixtures.

This rule is global and profile-neutral. It was discovered on Profile 3 because a real `.env.deploy` and running `kw-studio` stack were present during patch validation, but future runners on every profile must account for local env files, containers, volumes, and ports before choosing tests or checkers.


## KR-6D typed LLM slide planning contract (in progress)

KR-6D introduces a versioned planning schema for real-user prompt slide planning:
- `schema_version=slides_plan.v1` required;
- required `slides` array with exact requested slide count;
- each slide requires unique `slide_number` matching `1..N`, title, and 2..5 bullets.

Validation is typed and sanitised (no raw LLM response, no full prompt logging). Error codes include parse, schema, structure, numbering, label leakage, prompt echo, and low-information content failures.

Repair behavior: exactly one repair retry after first invalid attempt. Repair prompt includes schema version, exact schema, requested slide count, topic/style, sanitised validation errors (`code/path/expected/observed`), and forbidden public labels.

Fallback semantics: deterministic fallback is allowed only after attempts are exhausted, with `degraded=true`, `llm_planning_used=false`, and specific final error code preserved in both `llm_final_error_code` and compatibility alias `llm_planning_error_code`.

Planning metadata semantics:
- `planning_mode`, `llm_planning_used`, `llm_attempt_count`;
- `llm_final_error_code`, `llm_planning_error_code`, `llm_validation_errors`;
- `requested_slide_count`, `actual_slide_count`, `schema_version`;
- `prompt_echo_blocked`, `placeholder_leakage_blocked`, `template_label_leakage_blocked`;
- `degraded`, `raw_llm_response_logged=false`.

PPTX public text quality gate (workflow regression): output must keep requested slide count and reject template labels/public leakage (`Additional insight`, `Local deterministic slide image generation`, `Key points`, `Option A`, `Current path`, `Step 1`) and prompt echo in user-visible slide text.

Compatibility requirements remain protected:
- KR-6C source-mode routing behavior unchanged;
- K2 source-aware API behavior unchanged;
- RF2/RF2.1 media baseline preserved;
- public internet test mode and render/visual QA bundle contracts unchanged.
