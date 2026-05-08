from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parents[3]
def run_p10_6(*args:str)->dict:
    r=subprocess.run([sys.executable,"scripts/kw_p10_6_human_review_packet_export.py","--repo-root",str(REPO_ROOT),"--require-ready","--json",*args],cwd=REPO_ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    assert r.returncode==0, r.stderr or r.stdout
    return json.loads(r.stdout)
def test_p10_6_static_export_report_is_conservative()->None:
    report=run_p10_6(); assert report["status"]=="ready"; assert report["human_re_review_packet_exported_by_p10_6"] is True; assert report["review_worksheet_count"]==5; assert report["all_review_decisions_pending"] is True; assert report["release_decision_remains"]=="defer_pending_human_re_review"; assert report["release_approval_granted_by_p10_6"] is False; assert report["approval_state_changed_by_p10_6"] is False; assert report["golden_decks_auto_approved_by_p10_6"] is False; assert report["kimi_level_claimed_by_p10_6"] is False; assert report["p10_5a_public_api_dev_evidence_is_not_server3_offline_proof"] is True; assert report["server3_offline_intranet_route_verified_by_p10_6"] is False
def test_p10_6_persistent_export_zip(tmp_path:Path)->None:
    artifacts_dir=tmp_path/"packet"; export_zip=tmp_path/"packet.zip"; report=run_p10_6("--artifacts-dir",str(artifacts_dir),"--export-zip",str(export_zip)); assert report["status"]=="ready"; assert export_zip.exists(); assert report["export_zip_summary"]["export_zip_size_bytes"]>0; assert report["export_zip_summary"]["exported_pptx_count"]>=5; assert report["export_zip_summary"]["exported_json_count"]>=5
