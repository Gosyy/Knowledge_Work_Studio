from pathlib import Path

import backend.app.orchestrator as orchestrator
from backend.app.orchestrator import (
    OrchestratorExecutionCoordinator,
    RoutedTask,
    ServiceExecutionResult,
    TaskRouter,
)


def test_l2_official_orchestrator_package_surface_is_execution_only() -> None:
    assert OrchestratorExecutionCoordinator is not None
    assert ServiceExecutionResult is not None
    assert TaskRouter is not None
    assert RoutedTask is not None

    legacy_exports = {
        "OrchestrationCoordinator",
        "OrchestrationBundle",
        "OrchestratorIntegrationSurface",
        "TaskClassifier",
        "TaskPlanner",
        "ToolRouter",
        "ResultComposer",
        "ExecutionPlan",
        "OrchestrationResult",
    }

    for name in legacy_exports:
        assert not hasattr(orchestrator, name)


def test_l2_transitional_orchestration_modules_are_removed() -> None:
    orchestrator_dir = Path(__file__).resolve().parents[2] / "app" / "orchestrator"

    removed_modules = {
        "coordinator.py",
        "integration.py",
        "classifier.py",
        "planner.py",
        "tool_router.py",
        "result_composer.py",
    }

    for filename in removed_modules:
        assert not (orchestrator_dir / filename).exists()
