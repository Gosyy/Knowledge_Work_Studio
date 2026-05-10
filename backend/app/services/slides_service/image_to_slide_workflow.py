from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any
S6_WORKFLOW_ID="slides.image_to_slide_workflow"
IMAGE_INPUT_TYPES=("screenshot_png","screenshot_jpeg","image_png","image_jpeg","scanned_page_image")
LOCAL_HEAVY_MODULES=("local_ocr","local_layout_detection","local_region_segmentation","local_table_structure_detection")
SUPPORTED_REGION_TYPES=("title_text","body_text","table_region","chart_region","diagram_region","screenshot_region","source_caption")
EDITABLE_RECONSTRUCTION_TARGETS=("pptx_text_box","pptx_table","pptx_chart_or_data_summary","pptx_shape_diagram","annotated_image_crop_with_region_provenance")
SAFE_TASK_EVENTS=("slides.image_input.received","slides.image_regions.detected","slides.image_ocr.completed","slides.image_to_slide.plan.created","slides.image_to_slide.reconstruction.selected","slides.image_to_slide.generation.started","artifact.registered","plan.snapshot.registered","slides.image_to_slide.generation.completed")
@dataclass(frozen=True)
class ImageRegionProvenancePolicy:
    region_id_required: bool=True
    source_image_id_required: bool=True
    bbox_required: bool=True
    page_or_frame_required: bool=True
    extracted_text_digest_required: bool=True
    reconstruction_element_id_required: bool=True
    confidence_required: bool=True
    def as_dict(self)->dict[str,Any]: return asdict(self)
@dataclass(frozen=True)
class ImageToSlideWorkflowContract:
    workflow_id:str=S6_WORKFLOW_ID
    accepted_input_types:tuple[str,...]=IMAGE_INPUT_TYPES
    local_heavy_modules:tuple[str,...]=LOCAL_HEAVY_MODULES
    supported_region_types:tuple[str,...]=SUPPORTED_REGION_TYPES
    editable_reconstruction_targets:tuple[str,...]=EDITABLE_RECONSTRUCTION_TARGETS
    safe_task_events:tuple[str,...]=SAFE_TASK_EVENTS
    provenance_policy:ImageRegionProvenancePolicy=ImageRegionProvenancePolicy()
    source_to_region_provenance_required:bool=True
    region_to_slide_element_provenance_required:bool=True
    editable_pptx_reconstruction_preferred:bool=True
    raster_fallback_primary_path_allowed:bool=False
    raster_fallback_requires_reason:bool=True
    local_heavy_node_ready:bool=True
    cloud_vision_allowed:bool=False
    public_internet_required:bool=False
    api_endpoint_added_by_s6:bool=False
    db_schema_migration_added_by_s6:bool=False
    frontend_runtime_changed_by_s6:bool=False
    dependency_versions_changed_by_s6:bool=False
    dockerfiles_changed_by_s6:bool=False
    kimi_level_claimed_by_s6:bool=False
    server3_local_intranet_route_verified_by_s6:bool=False
    def as_dict(self)->dict[str,Any]:
        payload=asdict(self)
        for key in ("accepted_input_types","local_heavy_modules","supported_region_types","editable_reconstruction_targets","safe_task_events"):
            payload[key]=list(payload[key])
        payload["provenance_policy"]=self.provenance_policy.as_dict()
        return payload
CONTRACT=ImageToSlideWorkflowContract()
def validate_image_to_slide_workflow_contract(contract:ImageToSlideWorkflowContract=CONTRACT)->list[str]:
    errors=[]
    for item in ("screenshot_png","image_png","scanned_page_image"):
        if item not in contract.accepted_input_types: errors.append(f"missing accepted input type: {item}")
    for item in LOCAL_HEAVY_MODULES:
        if item not in contract.local_heavy_modules: errors.append(f"missing local heavy module: {item}")
    for item in ("table_region","chart_region","diagram_region","screenshot_region"):
        if item not in contract.supported_region_types: errors.append(f"missing region type: {item}")
    for item in ("pptx_text_box","pptx_table","pptx_shape_diagram"):
        if item not in contract.editable_reconstruction_targets: errors.append(f"missing reconstruction target: {item}")
    for field,value in contract.provenance_policy.as_dict().items():
        if value is not True: errors.append(f"provenance policy requires {field}=true")
    expected={"source_to_region_provenance_required":True,"region_to_slide_element_provenance_required":True,"editable_pptx_reconstruction_preferred":True,"raster_fallback_primary_path_allowed":False,"raster_fallback_requires_reason":True,"local_heavy_node_ready":True,"cloud_vision_allowed":False,"public_internet_required":False,"api_endpoint_added_by_s6":False,"db_schema_migration_added_by_s6":False,"frontend_runtime_changed_by_s6":False,"dependency_versions_changed_by_s6":False,"dockerfiles_changed_by_s6":False,"kimi_level_claimed_by_s6":False,"server3_local_intranet_route_verified_by_s6":False}
    for key,val in expected.items():
        if getattr(contract,key) is not val: errors.append(f"{key} must be {val}")
    return errors
def image_to_slide_workflow_report()->dict[str,Any]:
    errors=validate_image_to_slide_workflow_contract(CONTRACT)
    return {"status":"ready" if not errors else "not_ready","workflow_id":S6_WORKFLOW_ID,"s_phase":"S6","image_screenshot_to_slide_workflow_completed_by_s6":not errors,"accepted_input_type_count":len(CONTRACT.accepted_input_types),"accepted_input_types":list(CONTRACT.accepted_input_types),"local_heavy_module_count":len(CONTRACT.local_heavy_modules),"local_heavy_modules":list(CONTRACT.local_heavy_modules),"supported_region_type_count":len(CONTRACT.supported_region_types),"supported_region_types":list(CONTRACT.supported_region_types),"editable_reconstruction_target_count":len(CONTRACT.editable_reconstruction_targets),"editable_reconstruction_targets":list(CONTRACT.editable_reconstruction_targets),"ocr_vision_ready_metadata_required_by_s6":True,"crop_region_provenance_required_by_s6":CONTRACT.source_to_region_provenance_required,"region_to_slide_element_provenance_required_by_s6":CONTRACT.region_to_slide_element_provenance_required,"editable_pptx_reconstruction_preferred_by_s6":CONTRACT.editable_pptx_reconstruction_preferred,"raster_fallback_primary_path_allowed_by_s6":CONTRACT.raster_fallback_primary_path_allowed,"raster_fallback_requires_reason_by_s6":CONTRACT.raster_fallback_requires_reason,"local_heavy_node_ready_by_s6":CONTRACT.local_heavy_node_ready,"cloud_vision_allowed_by_s6":CONTRACT.cloud_vision_allowed,"public_internet_required_by_s6":CONTRACT.public_internet_required,"api_endpoint_added_by_s6":CONTRACT.api_endpoint_added_by_s6,"db_schema_migration_added_by_s6":CONTRACT.db_schema_migration_added_by_s6,"frontend_runtime_changed_by_s6":CONTRACT.frontend_runtime_changed_by_s6,"dependency_versions_changed_by_s6":CONTRACT.dependency_versions_changed_by_s6,"dockerfiles_changed_by_s6":CONTRACT.dockerfiles_changed_by_s6,"kimi_level_claimed_by_s6":CONTRACT.kimi_level_claimed_by_s6,"whole_project_kimi_level_supported":False,"server3_local_intranet_route_verified_by_s6":CONTRACT.server3_local_intranet_route_verified_by_s6,"next_recommended_step":"S7 - offline/intranet research citations with source-grounded slide evidence.","contract":CONTRACT.as_dict(),"errors":errors}
