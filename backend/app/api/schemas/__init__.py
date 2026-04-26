from backend.app.api.schemas.artifacts import ArtifactSchema
from backend.app.api.schemas.files import UploadedFileSchema
from backend.app.api.schemas.presentations import PresentationCurrentFileSchema, PresentationSchema, PresentationVersionSummarySchema
from backend.app.api.schemas.plan_snapshots import PresentationPlanDiffSchema, PresentationPlanSlideDeltaSchema, PresentationPlanSnapshotSchema
from backend.app.api.schemas.slides import (
    SlideCitationSchema,
    SlideOutlineItemSchema,
    SlidesGeneratedMediaRefSchema,
    SlidesSourceRefSchema,
    SlidesTaskResultDataSchema,
    SourceGroundingMetadataSchema,
    normalize_public_task_result_data,
)
from backend.app.api.schemas.revisions import (
    DeckRevisionResponseSchema,
    DeckRevisionSectionRequestSchema,
    DeckRevisionSlideRequestSchema,
    PlannedSlidePayloadSchema,
    PresentationPlanPayloadSchema,
    PresentationRevisionLineageItemSchema,
)
from backend.app.api.schemas.sessions import SessionCreateRequest, SessionDetailSchema, SessionSchema
from backend.app.api.schemas.tasks import TaskCreateRequest, TaskExecuteRequest, TaskExecutionJobSchema, TaskSemanticExecuteRequest, TaskSchema

__all__ = [
    "ArtifactSchema",
    "SlideCitationSchema",
    "SlideOutlineItemSchema",
    "SlidesGeneratedMediaRefSchema",
    "SlidesSourceRefSchema",
    "SlidesTaskResultDataSchema",
    "SourceGroundingMetadataSchema",
    "normalize_public_task_result_data",
    "DeckRevisionResponseSchema",
    "DeckRevisionSectionRequestSchema",
    "DeckRevisionSlideRequestSchema",
    "PlannedSlidePayloadSchema",
    "PresentationPlanPayloadSchema",
    "PresentationRevisionLineageItemSchema",
    "PresentationPlanDiffSchema",
    "PresentationPlanSlideDeltaSchema",
    "PresentationPlanSnapshotSchema",
    "PresentationCurrentFileSchema",
    "PresentationSchema",
    "PresentationVersionSummarySchema",
    "SessionCreateRequest",
    "SessionDetailSchema",
    "SessionSchema",
    "TaskCreateRequest",
    "TaskExecuteRequest",
    "TaskExecutionJobSchema",
    "TaskSemanticExecuteRequest",
    "TaskSchema",
    "UploadedFileSchema",
]
