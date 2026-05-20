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

KR-5A starts the first concrete spreadsheet runtime after the KR-4A workflow contract core. The work must remain inspect-only and non-destructive. It should not claim full Excel parity. The required implementation surface is:

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
