"""Official orchestrator package surface for the current runtime path.

After G1-G3, the supported public execution flow is centered on
`OrchestratorExecutionCoordinator` plus the API task execution route.
Older planning/preview surfaces remain available through their direct modules
for focused tests, but are intentionally not re-exported here.
"""

from backend.app.orchestrator.execution import OrchestratorExecutionCoordinator, ServiceExecutionResult
from backend.app.orchestrator.router import RoutedTask, TaskRouter

__all__ = [
    "OrchestratorExecutionCoordinator",
    "RoutedTask",
    "ServiceExecutionResult",
    "TaskRouter",
]
