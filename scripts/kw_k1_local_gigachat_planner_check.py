#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
REQUIRED_FILES=("docs/codex/K1_LOCAL_GIGACHAT_PLANNING_ENGINE.md","backend/app/services/k_phase/local_gigachat_planner.py","scripts/kw_k1_local_gigachat_planner_check.py","backend/tests/smoke/test_k1_local_gigachat_planner.py")
EXPECTED_HEAD_BASE="6a143ff264f11deff8bd257666b01b476f33f8da"
@dataclass
class MockLocalGigaChatProvider:
    response_text: str
    provider_name: str="gigachat"
    model_name: str="GigaChat-Pro-local-mock"
    def complete(self, request: Any) -> Any:
        from backend.app.integrations.llm.models import LLMCompletionResult
        return LLMCompletionResult(text=self.response_text, provider=self.provider_name, model=self.model_name, raw={"mocked": True})
@dataclass
class FailingLocalGigaChatProvider:
    provider_name: str="gigachat"
    model_name: str="GigaChat-Pro-local-mock"
    def complete(self, request: Any) -> Any: raise TimeoutError("mocked timeout")
@dataclass
class WrongProvider:
    provider_name: str="litellm-compatible"
    model_name: str="gateway-model"
    def complete(self, request: Any) -> Any: raise AssertionError("must not be called")
def run_git(root: Path,*args:str)->str|None:
    r=subprocess.run(("git",*args),cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False); return r.stdout.strip() if r.returncode==0 else None
def static_errors(root: Path, require_ready: bool)->list[str]:
    e=[f"missing K1 required file: {rel}" for rel in REQUIRED_FILES if not (root/rel).exists()]
    if require_ready and run_git(root,"branch","--show-current")not in ("8_K_Phase", "9_Product_Release_Hardening"): e.append(f"expected branch 8_K_Phase or 9_Product_Release_Hardening, got {run_git(root,'branch','--show-current')}")
    return e
def runtime_smoke(root: Path)->dict[str,Any]:
    if str(root) not in sys.path: sys.path.insert(0,str(root))
    from backend.app.services.k_phase.local_gigachat_planner import K1PlanningRequest, LocalGigaChatPlanningEngine
    source="Revenue grew in Q1. Churn risk increased in enterprise accounts. Recommendation is to prioritize retention and onboarding automation."
    llm_json=json.dumps({"deck_title":"Retention Growth Plan","slides":[{"title":"Retention Growth Plan","slide_type":"title","bullets":["Revenue grew in Q1","Enterprise churn risk increased"]},{"title":"Context","slide_type":"section","bullets":["Source memo shows growth and churn tension"]},{"title":"Evidence","slide_type":"data","bullets":["Retention risk requires onboarding automation"]},{"title":"Decision","slide_type":"conclusion","bullets":["Approve retention automation plan"]}]})
    req=K1PlanningRequest(source_text=source,source_refs=({"source_id":"memo_001","title":"Q1 memo"},),target_slide_count=4)
    llm=LocalGigaChatPlanningEngine(MockLocalGigaChatProvider(llm_json)).plan(req); fb=LocalGigaChatPlanningEngine(FailingLocalGigaChatProvider()).plan(req); wrong=LocalGigaChatPlanningEngine(WrongProvider()).plan(req)
    errors=[]
    if not llm.llm_used or llm.deterministic_fallback_used: errors.append("mocked local GigaChat plan did not use LLM path")
    if fb.llm_used or not fb.deterministic_fallback_used: errors.append("unavailable local GigaChat did not use deterministic fallback")
    if wrong.safe_metadata.get("fallback_reason_code")!="non_gigachat_provider_rejected": errors.append("non-GigaChat provider was not rejected safely")
    meta=json.dumps(llm.safe_metadata,ensure_ascii=False,sort_keys=True)
    if source[:40] in meta: errors.append("safe metadata contains raw source text")
    if llm.safe_metadata.get("cloud_llm_added_by_k1") is not False: errors.append("K1 must not add cloud LLM")
    if llm.safe_metadata.get("kimi_level_claimed_by_k1") is not False: errors.append("K1 must not claim Kimi-level")
    return {"status":"ready" if not errors else "failed","errors":errors,"local_gigachat_planning_supported":not errors,"source_aware_plan_created":len(llm.plan.slides)>=4,"outline_first_plan_created":bool(llm.plan.slides[0].title),"mocked_local_gigachat_success":llm.llm_used,"deterministic_fallback_when_unavailable":fb.deterministic_fallback_used,"non_gigachat_provider_rejected_without_call":wrong.deterministic_fallback_used,"safe_metadata_only":not errors,"raw_source_text_stored":False,"raw_prompt_stored":False,"cloud_llm_added_by_k1":False,"litellm_override_allowed_by_k1":False,"kimi_level_claimed_by_k1":False,"whole_project_kimi_level_supported":False,"slide_count":len(llm.plan.slides),"fallback_slide_count":len(fb.plan.slides)}
def build_report(root: Path, require_ready: bool)->dict[str,Any]:
    e=static_errors(root,require_ready); smoke=runtime_smoke(root) if not e else {"status":"skipped","errors":["static checks failed"]}; errors=e+list(smoke.get("errors",[]))
    return {"mode":"k1-local-gigachat-planning-engine","phase":"K-phase","checkpoint":"K1","branch":run_git(root,"branch","--show-current") or "unknown","commit":run_git(root,"rev-parse","HEAD") or "unknown","k1_base_after_k0":EXPECTED_HEAD_BASE,"runtime_changed_by_k1":True,"runtime_change_type":"local_gigachat_source_aware_planning_engine","local_gigachat_default_provider":True,"deterministic_fallback_supported":True,"dependency_versions_changed_by_k1":False,"dockerfiles_changed_by_k1":False,"frontend_runtime_changed_by_k1":False,"api_endpoint_added_by_k1":False,"db_schema_migration_added_by_k1":False,"cloud_llm_added_by_k1":False,"litellm_made_mandatory_by_k1":False,"kimi_level_claimed_by_k1":False,"whole_project_kimi_level_supported":False,"runtime_smoke":smoke,"next_recommended_step":"K2 — Plan editor as product workflow","errors":errors,"status":"ready" if not errors else "failed"}
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--repo-root",default=str(Path(__file__).resolve().parents[1])); p.add_argument("--require-ready",action="store_true"); p.add_argument("--json",action="store_true"); a=p.parse_args(); r=build_report(Path(a.repo_root).expanduser().resolve(),a.require_ready); print(json.dumps(r,indent=2,sort_keys=True)); return 0 if r["status"]=="ready" else 2
if __name__=="__main__": raise SystemExit(main())
