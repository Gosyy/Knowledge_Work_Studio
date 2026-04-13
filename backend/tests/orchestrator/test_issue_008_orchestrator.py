import pytest

from backend.app.domain import TaskType
from backend.app.orchestrator.classifier import TaskClassifier
from backend.app.orchestrator.coordinator import OrchestrationCoordinator
from backend.app.orchestrator.planner import TaskPlanner
from backend.app.orchestrator.result_composer import ResultComposer
from backend.app.orchestrator.tool_router import ToolRouter


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("Please edit this DOCX", TaskType.DOCX_EDIT),
        ("Summarize this PDF", TaskType.PDF_SUMMARY),
        ("Create slides from notes", TaskType.SLIDES_GENERATE),
        ("Analyze this CSV data", TaskType.DATA_ANALYSIS),
    ],
)
def test_classifier_supports_initial_task_types(prompt: str, expected: TaskType) -> None:
    classifier = TaskClassifier()
    assert classifier.classify(prompt) is expected


def test_coordinator_prepare_and_compose_is_testable() -> None:
    coordinator = OrchestrationCoordinator(
        classifier=TaskClassifier(),
        planner=TaskPlanner(),
        tool_router=ToolRouter(),
        result_composer=ResultComposer(),
    )

    bundle = coordinator.prepare("Generate slides deck from talking points")
    assert bundle.task_type is TaskType.SLIDES_GENERATE
    assert bundle.plan.task_type is TaskType.SLIDES_GENERATE
    assert bundle.tool_keys == ("slides_builder",)

    result = coordinator.compose_result(task_type=bundle.task_type, artifact_ids=["art_1", "art_2"])
    assert result.task_type is TaskType.SLIDES_GENERATE
    assert result.artifact_ids == ("art_1", "art_2")
    assert "2 artifact(s)" in result.summary
