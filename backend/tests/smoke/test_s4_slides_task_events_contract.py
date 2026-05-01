from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.app.services.slides_service.task_event_contract import (  # noqa: E402
    SLIDES_RETRY_EVENT_SEQUENCE,
    SLIDES_TASK_EVENT_STREAM_CONTRACT,
    slides_task_event_stream_report,
    validate_slides_task_event_stream_contract,
)


def run_s4_check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/kw_slides_task_events_check.py", "--repo-root", str(REPO_ROOT), *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_s4_contract_validates_without_errors() -> None:
    assert validate_slides_task_event_stream_contract() == []


def test_s4_contract_is_offline_append_only_and_provenance_first() -> None:
    contract = SLIDES_TASK_EVENT_STREAM_CONTRACT
    assert contract.workflow_id == "slides"
    assert contract.append_only_stream is True
    assert contract.offline_ready is True
    assert contract.provenance_required is True
    assert contract.browser_policy == "none"


def test_s4_retry_requires_saved_plan_and_new_artifact() -> None:
    contract = SLIDES_TASK_EVENT_STREAM_CONTRACT
    assert contract.retry_requires_saved_plan_snapshot is True
    assert contract.retry_requires_explicit_operator_instruction is True
    assert contract.retry_requires_render_mode_confirmation is True
    assert contract.retry_links_parent_plan_snapshot is True
    assert contract.retry_must_register_new_artifact is True


def test_s4_retry_event_sequence_is_ordered() -> None:
    sequence = SLIDES_RETRY_EVENT_SEQUENCE
    assert sequence.index("slides.retry.from_saved_plan.requested") < sequence.index(
        "slides.retry.saved_plan_snapshot.loaded"
    )
    assert sequence.index("slides.retry.saved_plan_snapshot.loaded") < sequence.index(
        "slides.retry.plan.validated"
    )
    assert sequence.index("slides.retry.render_mode.confirmed") < sequence.index(
        "slides.retry.generation.started"
    )
    assert sequence.index("artifact.registered") < sequence.index("slides.retry.generation.completed")


def test_s4_report_retry_slice_is_ready() -> None:
    report = slides_task_event_stream_report(mode="retry")
    assert report["status"] == "ready"
    assert report["selected_mode"] == "retry"
    assert report["controls"]["retry_requires_saved_plan_snapshot"] is True
    assert "slides.retry.saved_plan_snapshot.loaded" in report["selected_events"]


def test_s4_cli_outputs_json_for_retry_mode() -> None:
    result = run_s4_check("--mode", "retry", "--json", "--require-ready")
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["selected_mode"] == "retry"
    assert payload["controls"]["retry_must_register_new_artifact"] is True


def test_s4_cli_outputs_json_for_stream_mode() -> None:
    result = run_s4_check("--mode", "stream", "--json", "--require-ready")
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["selected_mode"] == "stream"
    assert "slides.plan.approved" in payload["selected_events"]


def test_s4_cli_rejects_unknown_mode() -> None:
    result = run_s4_check("--mode", "browser", "--require-ready")
    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_s4_contract_declares_redaction_policy() -> None:
    keys = set(SLIDES_TASK_EVENT_STREAM_CONTRACT.redacted_payload_keys)
    assert {"secret", "token", "api_key", "client_secret", "database_url"}.issubset(keys)
