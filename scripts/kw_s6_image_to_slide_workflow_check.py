#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path: sys.path.insert(0,str(REPO_ROOT))
from backend.app.services.slides_service.image_to_slide_workflow import image_to_slide_workflow_report
EXPECTED_BASE_AFTER_S5="0ce33b74473e8ffdbf6e47f4096da86b66b898eb"
REQUIRED_FILES=("docs/codex/S_PHASE_KIMI_SLIDES_CLASS_ROADMAP.md","docs/codex/S5_TEMPLATE_MASTER_INGESTION.md","docs/codex/S6_IMAGE_SCREENSHOT_TO_SLIDE_WORKFLOW.md","backend/app/services/slides_service/adaptive_deck_modes.py","backend/app/services/slides_service/native_visuals.py","backend/app/services/slides_service/template_master_ingestion.py","backend/app/services/slides_service/image_to_slide_workflow.py","scripts/kw_s5_template_master_ingestion_check.py","scripts/kw_s6_image_to_slide_workflow_check.py","backend/tests/smoke/test_s6_image_to_slide_workflow.py")
def run_git(repo_root:Path,*args:str)->str|None:
    result=subprocess.run(("git",*args),cwd=repo_root,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False)
    return result.stdout.strip() if result.returncode==0 else None
def is_ancestor(repo_root:Path,ancestor:str,descendant:str)->bool|None:
    result=subprocess.run(("git","merge-base","--is-ancestor",ancestor,descendant),cwd=repo_root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
    if result.returncode==0: return True
    if result.returncode==1: return False
    return None
def static_errors(repo_root:Path,require_ready:bool)->list[str]:
    errors=[f"missing S6 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root/rel).exists()]
    if require_ready:
        branch=run_git(repo_root,"branch","--show-current")
        if branch not in ("9_Product_Release_Hardening","8_K_Phase"): errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head=run_git(repo_root,"rev-parse","HEAD")
        if head and head!=EXPECTED_BASE_AFTER_S5:
            ancestry=is_ancestor(repo_root,EXPECTED_BASE_AFTER_S5,head)
            if ancestry is False: errors.append(f"expected S5 baseline {EXPECTED_BASE_AFTER_S5} to be an ancestor of HEAD {head}")
            elif ancestry is None: errors.append(f"could not verify S5 ancestry for {EXPECTED_BASE_AFTER_S5}..{head}")
    return errors
def main()->int:
    parser=argparse.ArgumentParser(description="Validate KW Studio S6 image/screenshot-to-slide workflow contract.")
    parser.add_argument("--repo-root",type=Path,default=Path.cwd())
    parser.add_argument("--json",action="store_true")
    parser.add_argument("--require-ready",action="store_true")
    args=parser.parse_args()
    repo_root=args.repo_root.resolve()
    report=image_to_slide_workflow_report()
    errors=static_errors(repo_root,args.require_ready)
    if errors:
        report["errors"].extend(errors); report["status"]="not_ready"
    report["repo_root"]=str(repo_root); report["branch"]=run_git(repo_root,"branch","--show-current") or "unknown"; report["commit"]=run_git(repo_root,"rev-parse","HEAD") or "unknown"; report["expected_base_after_s5"]=EXPECTED_BASE_AFTER_S5; report["required_files"]={rel:(repo_root/rel).exists() for rel in REQUIRED_FILES}
    if args.json: print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))
    else:
        print(f"S6 image/screenshot-to-slide workflow: {report['status']}")
        print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))
        for error in report.get("errors",[]): print(f"[FAIL] {error}")
    return 0 if report["status"]=="ready" else 1
if __name__=="__main__": raise SystemExit(main())
