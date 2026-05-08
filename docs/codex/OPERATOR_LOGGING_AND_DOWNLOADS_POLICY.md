# Operator logging and Downloads policy

- status: `controlled_operator_tooling_policy`
- branch: `9_Product_Release_Hardening`
- baseline before patch: `048443a073b807026a2de725e1d069f60a7e6a18`
- applies to profiles: `profile1`, `profile2`
- Kimi-level claimed: `False`

## Purpose

This policy removes the accidental dependency on the operator Downloads directory as a durable storage location for KW Studio patch runners, full-runner wrappers, and logs.

The project repository is the source of truth for reusable operator tooling. The Downloads directory is allowed only as an input/output handoff area: downloaded scripts, uploaded archives, and temporary files may appear there, but reusable scripts must be moved into the repository before they become part of the workflow.

## files.zip inventory decision

The inspected `files.zip` contained these file categories:

| Archive item | Decision | Reason |
| --- | --- | --- |
| `patch_full_tests_summary_branch_profile2_v3.py` | Refactor and commit as `scripts/kw_patch_full_tests_summary.py` | Useful reusable summary metadata repair helper, but must not be profile-2-only. |
| `run_kws_full_tests_with_proxy.sh.orig-summary-branch-20260506_120614` | Refactor and commit as `scripts/kw_full_tests_with_proxy_runner.sh` | This is the real full-runner logic; the stale default branch must be removed and logs must be zipped under repo `logs/`. |
| `run_kws_full_tests_with_proxy.sh` | Do not commit raw | It is a local profile-2 wrapper around backups. Replaced by project-owned portable runner. |
| `kws_runner_backups/*` | Do not commit | Local backup chain; not a source-of-truth project artifact. |
| `run_p10_2_post_p9_artifact_pack_targeted_profile2.sh` | Do not commit | One-off patch runner for a specific commit. Future one-off runners may be regenerated, but reusable log behavior belongs in project tooling. |

## Log location rule

New patch runners, targeted runners, and full-runner helpers must write logs under the repository:

```text
<repo-root>/logs/<run-id>/
<repo-root>/logs/<run-id>.zip
```

After the `.zip` archive is created successfully, the source log directory must be removed automatically. The remaining uploadable artifact should be the `.zip` file.

The Downloads directory must not be used as the default log root.

## Profile portability rule

Committed operator scripts must not hardcode profile-specific paths such as:

```text
/home/editor/workplace/Knowledge_Work_Studio
/home/editor/Загрузки
/home/su4ka/workplace/Knowledge_Work_Studio
/home/su4ka/Загрузки
```

Instead, committed scripts must infer `repo_root` from their location or accept `--repo-root` / `KWS_REPO_ROOT`.

Profile 2 may still run:

```bash
/home/editor/workplace/Knowledge_Work_Studio/scripts/kw_full_tests_with_proxy_runner.sh
```

Profile 1 may run the same committed script from its own checkout:

```bash
/home/su4ka/workplace/Knowledge_Work_Studio/scripts/kw_full_tests_with_proxy_runner.sh
```

The script must write logs to the corresponding checkout's `logs/` directory.

## Summary metadata rule

- summary.log must report the real repository branch and HEAD.

Full-runner `summary.log` must report the real repository branch and HEAD. It must not rely on a stale default such as `8_K_Phase` after the project has moved to `9_Product_Release_Hardening`.

At minimum, summary metadata should include:

```text
repo=<repo-root>
branch=<actual branch>
head=<actual HEAD>
origin_head=<actual origin/9_Product_Release_Hardening HEAD if available>
started_at=<timestamp>
finished_at=<timestamp>
```

## Scope guard

This operator tooling policy does not add product APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, public-internet runtime requirements, or Kimi-level claims.

It does not run `npm audit fix --force` and does not remediate dependency/security warnings. Those remain a separate controlled track.
