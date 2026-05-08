#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile, zipfile
from hashlib import sha256
from pathlib import Path
from typing import Any
CHECKPOINT="P10-6"
SCHEMA_VERSION="p10.6.human_review_packet_export.v1"
EXPECTED_BASE_AFTER_P10_5="6ab666e845898731d27e0b109b722c2eace70787"
GOLDEN_CASE_IDS=("k0_exec_memo_to_board_deck","k0_arch_doc_to_architecture_deck","k0_project_log_to_status_deck","k0_comparison_table_to_decision_deck","k0_long_docx_pdf_to_structured_presentation")
REQUIRED_FILES=("docs/codex/P10_POST_P9_GOLDEN_REVIEW_PHASE_PLAN.md","docs/codex/P10_4_POST_P9_HUMAN_RE_REVIEW_CAPTURE.md","docs/codex/P10_5_RELEASE_DECISION_DOSSIER.md","docs/codex/P10_6_HUMAN_REVIEW_PACKET_EXPORT.md","scripts/kw_p10_4_post_p9_human_re_review.py","scripts/kw_p10_5_release_decision_dossier.py","scripts/kw_p10_6_human_review_packet_export.py","backend/tests/smoke/test_p10_6_human_review_packet_export.py")
def run_git(repo_root:Path,*args:str)->str|None:
    r=subprocess.run(("git",*args),cwd=repo_root,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False); return r.stdout.strip() if r.returncode==0 else None
def is_ancestor(repo_root:Path,ancestor:str,descendant:str)->bool|None:
    r=subprocess.run(("git","merge-base","--is-ancestor",ancestor,descendant),cwd=repo_root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False); return True if r.returncode==0 else False if r.returncode==1 else None
def digest_payload(payload:Any)->str:
    return "sha256:"+sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()
def collect_static_errors(repo_root:Path, require_ready:bool)->list[str]:
    errors=[f"missing P10-6 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root/rel).exists()]
    if require_ready:
        branch=run_git(repo_root,"branch","--show-current")
        if branch not in ("9_Product_Release_Hardening","8_K_Phase"): errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head=run_git(repo_root,"rev-parse","HEAD")
        if head and head != EXPECTED_BASE_AFTER_P10_5:
            anc=is_ancestor(repo_root,EXPECTED_BASE_AFTER_P10_5,head)
            if anc is False: errors.append(f"expected P10-5 baseline {EXPECTED_BASE_AFTER_P10_5} to be ancestor of HEAD {head}")
            elif anc is None: errors.append(f"could not verify P10-5 ancestry for {EXPECTED_BASE_AFTER_P10_5}..{head}")
    return errors
def run_p10_4_packet(repo_root:Path, artifacts_root:Path):
    cmd=(sys.executable,"scripts/kw_p10_4_post_p9_human_re_review.py","--repo-root",str(repo_root),"--artifacts-dir",str(artifacts_root),"--require-ready","--json")
    r=subprocess.run(cmd,cwd=repo_root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False); payload=None
    if r.stdout.strip():
        try: payload=json.loads(r.stdout)
        except json.JSONDecodeError: payload=None
    return payload,r.stdout,r.stderr,r.returncode
def collect_files(root:Path)->list[Path]:
    return sorted([p for pat in ("*.json","*.pptx") for p in root.rglob(pat) if p.is_file()])
def make_zip(root:Path, export_zip:Path, metadata:dict[str,Any])->dict[str,Any]:
    export_zip.parent.mkdir(parents=True,exist_ok=True); manifest=root/"p10_6_human_review_packet_export_manifest.json"
    manifest.write_text(json.dumps(metadata,ensure_ascii=False,indent=2,sort_keys=True,default=str),encoding="utf-8")
    files=collect_files(root); files.append(manifest) if manifest not in files else None
    with zipfile.ZipFile(export_zip,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(set(files)): z.write(p,p.relative_to(root).as_posix())
    return {"export_zip_file":str(export_zip),"export_zip_size_bytes":export_zip.stat().st_size,"export_zip_sha256":"sha256:"+sha256(export_zip.read_bytes()).hexdigest(),"exported_file_count":len(files),"exported_pptx_count":sum(1 for p in files if p.suffix==".pptx"),"exported_json_count":sum(1 for p in files if p.suffix==".json"),"exported_file_digest":digest_payload([p.relative_to(root).as_posix() for p in sorted(set(files))])}
def build_report_with_artifacts(repo_root:Path, root:Path, export_zip:Path, persisted:bool, require_ready:bool)->dict[str,Any]:
    errors=collect_static_errors(repo_root,require_ready); worksheets=[]; zip_summary={}; payload=None
    if not errors:
        root.mkdir(parents=True,exist_ok=True); payload,out,err,code=run_p10_4_packet(repo_root,root)
        if code!=0: errors.append(f"P10-4 packet generation failed during P10-6 export with exit code {code}: {err.strip() or out.strip()[:500]}")
        if payload is None: errors.append("P10-6 could not parse P10-4 packet JSON output")
        elif payload.get("status")!="ready": errors.append(f"P10-4 packet status is not ready during P10-6 export: {payload.get('status')!r}")
        if payload:
            worksheets=payload.get("review_worksheets",[]) if isinstance(payload.get("review_worksheets"),list) else []
            if len(worksheets)!=len(GOLDEN_CASE_IDS): errors.append(f"expected {len(GOLDEN_CASE_IDS)} review worksheets, got {len(worksheets)}")
            if payload.get("human_re_review_completed_by_p10_4") is not False: errors.append("P10-4 worksheets must remain pending")
            if payload.get("approval_state_changed_by_p10_4") is not False: errors.append("P10-4 changed approval state")
        metadata={"schema_version":SCHEMA_VERSION,"checkpoint":CHECKPOINT,"source_checkpoint":"P10-4","branch":run_git(repo_root,"branch","--show-current") or "unknown","commit":run_git(repo_root,"rev-parse","HEAD") or "unknown","worksheet_count":len(worksheets),"expected_worksheet_count":len(GOLDEN_CASE_IDS),"review_decision_state":"pending_human_review","release_decision_remains":"defer_pending_human_re_review","human_re_review_packet_exported_by_p10_6":True,"human_re_review_completed_by_p10_6":False,"approval_state_changed_by_p10_6":False,"golden_decks_auto_approved_by_p10_6":False,"kimi_level_claimed_by_p10_6":False,"public_api_dev_evidence_is_not_server3_offline_proof":True}
        if not errors: zip_summary=make_zip(root,export_zip,metadata)
    ready=not errors and bool(zip_summary) and len(worksheets)==len(GOLDEN_CASE_IDS)
    return {"mode":"p10-6-human-review-packet-export","phase":"P10 Post-P9 Golden Benchmark Regeneration and Human Re-review","checkpoint":CHECKPOINT,"schema_version":SCHEMA_VERSION,"branch":run_git(repo_root,"branch","--show-current") or "unknown","commit":run_git(repo_root,"rev-parse","HEAD") or "unknown","expected_base_after_p10_5":EXPECTED_BASE_AFTER_P10_5,"status":"ready" if ready else "failed","errors":errors,"artifacts_root":str(root),"artifact_pack_persisted":persisted,"human_re_review_packet_exported_by_p10_6":bool(ready),"human_re_review_completed_by_p10_6":False,"review_worksheet_count":len(worksheets),"expected_review_worksheet_count":len(GOLDEN_CASE_IDS),"all_review_decisions_pending":bool(worksheets) and all(w.get("decision") is None for w in worksheets),"release_decision_remains":"defer_pending_human_re_review","release_approval_granted_by_p10_6":False,"approval_state_changed_by_p10_6":False,"golden_decks_auto_approved_by_p10_6":False,"known_non_blocking_warnings_inherited_from_p9":True,"p10_5a_public_api_dev_evidence_available":True,"p10_5a_public_api_dev_evidence_is_not_server3_offline_proof":True,"server3_offline_intranet_route_verified_by_p10_6":False,"full_runner_acceptance_mode":"pass_with_known_non_blocking_warnings","npm_audit_fix_force_run_by_p10_6":False,"api_endpoint_added_by_p10_6":False,"db_schema_migration_added_by_p10_6":False,"frontend_runtime_changed_by_p10_6":False,"dependency_versions_changed_by_p10_6":False,"dockerfiles_changed_by_p10_6":False,"cloud_llm_added_by_p10_6":False,"cloud_vision_added_by_p10_6":False,"kimi_level_claimed_by_p10_6":False,"whole_project_kimi_level_supported":False,"network_required_for_p10_6":False,"export_zip_summary":zip_summary,"next_recommended_step":"P10-7 - ingest completed human review results from this packet; do not approve release until worksheets are completed."}
def build_report(repo_root:Path, artifacts_dir:Path|None, export_zip:Path|None, require_ready:bool)->dict[str,Any]:
    if artifacts_dir is not None:
        root=artifacts_dir.resolve(); target=export_zip.resolve() if export_zip else root.parent/f"{root.name}.zip"; return build_report_with_artifacts(repo_root,root,target,True,require_ready)
    with tempfile.TemporaryDirectory(prefix="kw_p10_6_review_packet_") as tmp:
        root=Path(tmp); target=root.parent/f"{root.name}.zip"
        try: return build_report_with_artifacts(repo_root,root,target,False,require_ready)
        finally: target.unlink(missing_ok=True)
def main()->int:
    p=argparse.ArgumentParser(description="KW Studio P10-6 human review packet export."); p.add_argument("--repo-root",type=Path,default=Path.cwd()); p.add_argument("--artifacts-dir",type=Path,default=None); p.add_argument("--export-zip",type=Path,default=None); p.add_argument("--json",action="store_true"); p.add_argument("--require-ready",action="store_true")
    a=p.parse_args(); report=build_report(a.repo_root.resolve(),a.artifacts_dir,a.export_zip,a.require_ready)
    if a.json: print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True,default=str))
    else:
        print(f"P10-6 human review packet export: {report['status']}"); print(f"review worksheets: {report['review_worksheet_count']}/{report['expected_review_worksheet_count']}")
        if report.get("export_zip_summary"): print(f"export zip: {report['export_zip_summary'].get('export_zip_file')}")
        for e in report.get("errors",[]): print(f"- {e}")
    return 0 if report["status"]=="ready" else 1
if __name__=="__main__": raise SystemExit(main())\n