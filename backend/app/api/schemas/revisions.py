from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.services.slides_service.outline import PlannedSlide, PresentationPlan, SlideType, StoryArcStage


class PlannedSlidePayloadSchema(BaseModel):
    slide_id: str
    slide_type: str
    story_arc_stage: str
    title: str
    bullets: list[str] = Field(default_factory=list)
    speaker_notes: str | None = None
    layout_hint: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "slide_id": "slide_003",
                "slide_type": "content",
                "story_arc_stage": "analysis",
                "title": "Analysis: key finding",
                "bullets": ["Evidence one", "Evidence two"],
                "speaker_notes": "Explain the key finding.",
                "layout_hint": "content_with_visual",
            }
        }
    )

    def to_domain(self) -> PlannedSlide:
        return PlannedSlide(
            slide_id=self.slide_id,
            slide_type=SlideType(self.slide_type),
            story_arc_stage=StoryArcStage(self.story_arc_stage),
            title=self.title,
            bullets=tuple(self.bullets),
            speaker_notes=self.speaker_notes,
            layout_hint=self.layout_hint,
        )


class PresentationPlanPayloadSchema(BaseModel):
    deck_title: str
    deck_goal: str
    audience: str
    tone: str
    target_slide_count: int
    story_arc: list[str]
    slides: list[PlannedSlidePayloadSchema]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deck_title": "Quarterly Review",
                "deck_goal": "Communicate a concise slide story.",
                "audience": "general_business",
                "tone": "clear_professional",
                "target_slide_count": 5,
                "story_arc": ["opening", "context", "analysis", "recommendation", "close"],
                "slides": [
                    {
                        "slide_id": "slide_001",
                        "slide_type": "title",
                        "story_arc_stage": "opening",
                        "title": "Quarterly Review",
                        "bullets": ["Executive summary"],
                    }
                ],
            }
        }
    )

    def to_domain(self) -> PresentationPlan:
        return PresentationPlan(
            deck_title=self.deck_title,
            deck_goal=self.deck_goal,
            audience=self.audience,
            tone=self.tone,
            target_slide_count=self.target_slide_count,
            story_arc=tuple(StoryArcStage(stage) for stage in self.story_arc),
            slides=tuple(slide.to_domain() for slide in self.slides),
        )


class DeckRevisionSlideRequestSchema(BaseModel):
    instruction: str
    plan: PresentationPlanPayloadSchema
    target_slide_id: str | None = None
    target_slide_index: int | None = None
    template_id: str = "default_light"
    task_id: str | None = None
    change_summary: str | None = None


class DeckRevisionSectionRequestSchema(BaseModel):
    instruction: str
    plan: PresentationPlanPayloadSchema
    target_stage: str
    template_id: str = "default_light"
    task_id: str | None = None
    change_summary: str | None = None


class DeckRevisionResponseSchema(BaseModel):
    presentation_id: str
    version_id: str
    version_number: int
    parent_version_id: str | None
    stored_file_id: str
    revised_slide_ids: list[str]
    scope: str
    change_summary: str | None
    created_at: datetime
    current_file_id: str
    previous_file_id: str | None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "presentation_id": "pres_123",
                "version_id": "presver_456",
                "version_number": 2,
                "parent_version_id": "presver_123",
                "stored_file_id": "sf_presrev_456",
                "revised_slide_ids": ["slide_003"],
                "scope": "slide",
                "change_summary": "Refresh analysis slide",
                "created_at": "2026-04-24T12:00:00Z",
                "current_file_id": "sf_presrev_456",
                "previous_file_id": "sf_initial",
            }
        }
    )


class PresentationRevisionLineageItemSchema(BaseModel):
    id: str
    version_number: int
    file_id: str
    parent_version_id: str | None
    change_summary: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
