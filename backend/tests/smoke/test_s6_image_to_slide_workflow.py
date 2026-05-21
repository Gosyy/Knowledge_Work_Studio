from __future__ import annotations
from backend.app.services.slides_service.image_to_slide_workflow import image_to_slide_workflow_report
def test_s6_image_to_slide_workflow_ready()->None:
    report=image_to_slide_workflow_report(); assert report["status"]=="ready"; assert report["image_screenshot_to_slide_workflow_completed_by_s6"] is True
def test_s6_requires_local_heavy_modules_and_no_cloud_vision()->None:
    report=image_to_slide_workflow_report(); assert report["local_heavy_node_ready_by_s6"] is True; assert "local_ocr" in report["local_heavy_modules"]; assert "local_layout_detection" in report["local_heavy_modules"]; assert report["cloud_vision_allowed_by_s6"] is False; assert report["public_internet_required_by_s6"] is False
def test_s6_requires_region_provenance_and_editable_reconstruction()->None:
    report=image_to_slide_workflow_report(); assert report["crop_region_provenance_required_by_s6"] is True; assert report["region_to_slide_element_provenance_required_by_s6"] is True; assert report["editable_pptx_reconstruction_preferred_by_s6"] is True; assert report["raster_fallback_primary_path_allowed_by_s6"] is False; assert "pptx_table" in report["editable_reconstruction_targets"]; assert "pptx_shape_diagram" in report["editable_reconstruction_targets"]
def test_s6_preserves_release_boundaries()->None:
    report=image_to_slide_workflow_report(); assert report["api_endpoint_added_by_s6"] is False; assert report["db_schema_migration_added_by_s6"] is False; assert report["frontend_runtime_changed_by_s6"] is False; assert report["dependency_versions_changed_by_s6"] is False; assert report["dockerfiles_changed_by_s6"] is False; assert report["kimi_level_claimed_by_s6"] is False; assert report["server3_local_intranet_route_verified_by_s6"] is False; assert report["next_recommended_step"].startswith("S7")
