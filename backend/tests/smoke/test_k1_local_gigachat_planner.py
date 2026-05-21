from __future__ import annotations
import json, subprocess, sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from backend.app.integrations.llm.models import LLMCompletionResult
from backend.app.services.k_phase.local_gigachat_planner import K1PlanningRequest, LocalGigaChatPlanningEngine
@dataclass
class MockLocalGigaChatProvider:
    response_text: str
    provider_name: str="gigachat"
    model_name: str="GigaChat-Pro-local-mock"
    def complete(self, request: Any)->LLMCompletionResult:
        assert "source_text" in request.prompt
        return LLMCompletionResult(text=self.response_text,provider=self.provider_name,model=self.model_name,raw={"mocked":True})
@dataclass
class FailingLocalGigaChatProvider:
    provider_name: str="gigachat"; model_name: str="GigaChat-Pro-local-mock"
    def complete(self, request: Any)->LLMCompletionResult: raise TimeoutError("mocked timeout")
def repo_root()->Path: return Path(__file__).resolve().parents[3]
def run_check(*args:str)->subprocess.CompletedProcess[str]:
    root=repo_root(); return subprocess.run([sys.executable,"scripts/kw_k1_local_gigachat_planner_check.py","--repo-root",str(root),*args],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
def test_k1_checker_reports_ready_without_kimi_overclaim()->None:
    result=run_check("--require-ready","--json"); assert result.returncode==0,result.stdout+result.stderr; payload=json.loads(result.stdout); assert payload["checkpoint"]=="K1"; assert payload["status"]=="ready"; assert payload["cloud_llm_added_by_k1"] is False; assert payload["kimi_level_claimed_by_k1"] is False; assert payload["whole_project_kimi_level_supported"] is False
def test_k1_uses_mocked_local_gigachat_json_plan()->None:
    response=json.dumps({"deck_title":"Local Plan","slides":[{"title":"Open","slide_type":"title","bullets":["Source-backed opening"]},{"title":"Context","slide_type":"section","bullets":["Source-backed context"]},{"title":"Evidence","slide_type":"data","bullets":["Source-backed evidence"]},{"title":"Close","slide_type":"conclusion","bullets":["Source-backed decision"]}]})
    result=LocalGigaChatPlanningEngine(MockLocalGigaChatProvider(response)).plan(K1PlanningRequest(source_text="A. B. C. D.",target_slide_count=4)); assert result.llm_used is True; assert result.deterministic_fallback_used is False; assert result.plan.deck_title=="Local Plan"; assert len(result.plan.slides)==4; assert result.safe_metadata["provider"]=="gigachat"; assert result.safe_metadata["raw_source_text_stored"] is False
def test_k1_falls_back_deterministically_when_local_gigachat_unavailable()->None:
    result=LocalGigaChatPlanningEngine(FailingLocalGigaChatProvider()).plan(K1PlanningRequest(source_text="One. Two. Three. Four. Five.",target_slide_count=5)); assert result.llm_used is False; assert result.deterministic_fallback_used is True; assert result.fallback_reason_code=="local_gigachat_unavailable"; assert len(result.plan.slides)==5
def test_k1_rejects_missing_source_and_fallback_disabled_provider()->None:
    try: LocalGigaChatPlanningEngine(None).plan(K1PlanningRequest(source_text="",target_slide_count=5))
    except ValueError: pass
    else: raise AssertionError("empty source_text must be rejected")
    try: LocalGigaChatPlanningEngine(None).plan(K1PlanningRequest(source_text="Valid",allow_deterministic_fallback=False))
    except Exception as exc: assert "provider is required" in str(exc)
    else: raise AssertionError("fallback disabled without provider must fail")
