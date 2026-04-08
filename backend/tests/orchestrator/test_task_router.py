from backend.app.domain import TaskType
from backend.app.orchestrator import TaskRouter


def test_task_router_maps_task_types_to_service_keys() -> None:
    router = TaskRouter()

    assert router.route(TaskType.DOCX_EDIT).service_key == "docx_service"
    assert router.route(TaskType.PDF_SUMMARY).service_key == "pdf_service"
    assert router.route(TaskType.SLIDES_GENERATE).service_key == "slides_service"
    assert router.route(TaskType.DATA_ANALYSIS).service_key == "data_analysis_service"
