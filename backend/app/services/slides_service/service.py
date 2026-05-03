from __future__ import annotations

from dataclasses import dataclass, field, replace

from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderRequest, ApprovedPlanRenderResult, render_approved_plan_to_pptx
from backend.app.services.slides_service.approved_plan_lifecycle import ApprovedPlanLifecycleRequest, ApprovedPlanLifecycleResult, render_approved_plan_with_lifecycle
from backend.app.services.slides_service.saved_plan_retry import SavedPlanRetryRequest, SavedPlanRetryResult, retry_saved_plan_with_lifecycle
from backend.app.services.slides_service.generator import generate_pptx_from_plan
from backend.app.services.slides_service.image_pipeline import DeterministicPatternImageProvider, SlideImageProvider, SlideImageRegistry
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideOutlineItem, build_presentation_plan, plan_to_outline
from backend.app.services.slides_service.source_grounding import build_source_grounded_plan


@dataclass(frozen=True)
class SlidesTransformOutput:
    slide_count: int
    summary_text: str
    artifact_content: bytes
    outline: tuple[SlideOutlineItem, ...]
    plan: PresentationPlan
    template_id: str
    generated_media_file_ids: tuple[str, ...] = ()
    source_grounding_metadata: dict[str, object] | None = None


@dataclass
class SlidesService:
    """Planning-first, layout-aware, image-capable slides MVP generator."""

    image_provider: SlideImageProvider = field(default_factory=DeterministicPatternImageProvider)
    image_registry: SlideImageRegistry | None = None
    plan_snapshot_service: object | None = None
    artifact_service: object | None = None

    def generate_deck(
        self,
        source_text: str,
        *,
        template_id: str = "default_light",
        session_id: str | None = None,
        task_id: str | None = None,
        owner_user_id: str = "user_local_default",
        source_refs: tuple[dict[str, str], ...] = (),
    ) -> SlidesTransformOutput:
        plan = build_presentation_plan(source_text, min_slides=5, max_slides=10)
        grounding = build_source_grounded_plan(
            plan,
            source_text=source_text,
            source_refs=source_refs,
        )
        enriched_plan, stored_file_ids = self._attach_generated_visuals(
            grounding.plan,
            session_id=session_id,
            task_id=task_id,
            owner_user_id=owner_user_id,
        )
        outline = plan_to_outline(enriched_plan)
        slide_count = len(outline)
        artifact_content = generate_pptx_from_plan(enriched_plan, template_id=template_id)
        summary_text = (
            f"Generated {slide_count} slide(s)."
            if template_id == "default_light"
            else f"Generated {slide_count} slide(s) with template '{template_id}'."
        )
        return SlidesTransformOutput(
            slide_count=slide_count,
            summary_text=summary_text,
            artifact_content=artifact_content,
            outline=outline,
            plan=enriched_plan,
            template_id=template_id,
            generated_media_file_ids=stored_file_ids,
            source_grounding_metadata=grounding.as_metadata(),
        )


    def generate_deck_from_approved_plan(
        self,
        plan: PresentationPlan,
        *,
        plan_snapshot_id: str,
        approval_status: str = "approved",
        render_mode: str = "adaptive",
        template_id: str = "business_clean",
        session_id: str | None = None,
        task_id: str | None = None,
        presentation_id: str | None = None,
        artifact_filename: str = "approved-plan-deck.pptx",
        operator_user_id: str = "user_local_default",
    ) -> ApprovedPlanRenderResult:
        """Render an already-approved plan into deterministic PPTX bytes.

        This additive RF2.2 path intentionally does not persist artifacts,
        emit provenance manifests, call an LLM, or change the supplied plan.
        """
        return render_approved_plan_to_pptx(
            ApprovedPlanRenderRequest(
                plan=plan,
                plan_snapshot_id=plan_snapshot_id,
                approval_status=approval_status,
                render_mode=render_mode,  # type: ignore[arg-type]
                template_id=template_id,
                session_id=session_id,
                task_id=task_id,
                presentation_id=presentation_id,
                artifact_filename=artifact_filename,
                operator_user_id=operator_user_id,
            )
        )


    def generate_deck_from_approved_plan_with_lifecycle(
        self,
        plan: PresentationPlan,
        *,
        session_id: str,
        task_id: str,
        presentation_id: str,
        approval_status: str = "approved",
        render_mode: str = "adaptive",
        template_id: str = "business_clean",
        presentation_version_id: str | None = None,
        plan_snapshot_id: str | None = None,
        change_summary: str = "Approved plan rendered to deterministic PPTX.",
        artifact_filename: str = "approved-plan-deck.pptx",
        operator_user_id: str = "user_local_default",
    ) -> ApprovedPlanLifecycleResult:
        """Render an approved plan and wire snapshot/artifact/event lifecycle.

        RF2.3 intentionally does not add a public API endpoint, migration,
        retry runtime, provenance artifact, or Kimi-level quality claim.
        """
        if self.plan_snapshot_service is None:
            raise ValueError("Slides approved-plan lifecycle requires plan_snapshot_service.")
        if self.artifact_service is None:
            raise ValueError("Slides approved-plan lifecycle requires artifact_service.")

        return render_approved_plan_with_lifecycle(
            ApprovedPlanLifecycleRequest(
                plan=plan,
                session_id=session_id,
                task_id=task_id,
                presentation_id=presentation_id,
                approval_status=approval_status,
                render_mode=render_mode,
                template_id=template_id,
                presentation_version_id=presentation_version_id,
                plan_snapshot_id=plan_snapshot_id,
                change_summary=change_summary,
                artifact_filename=artifact_filename,
                operator_user_id=operator_user_id,
            ),
            plan_snapshot_service=self.plan_snapshot_service,  # type: ignore[arg-type]
            artifact_service=self.artifact_service,  # type: ignore[arg-type]
        )


    def retry_deck_from_saved_plan(
        self,
        *,
        saved_plan_snapshot_id: str,
        session_id: str,
        retry_task_id: str,
        parent_task_id: str,
        presentation_id: str,
        operator_instruction: str,
        render_mode: str = "adaptive",
        template_id: str = "business_clean",
        new_plan_snapshot_id: str | None = None,
        new_presentation_version_id: str | None = None,
        artifact_filename: str = "retry-from-saved-plan.pptx",
        operator_user_id: str = "user_local_default",
    ) -> SavedPlanRetryResult:
        """Regenerate a deck from a saved plan snapshot.

        RF2.4 intentionally does not add a public API endpoint, migration,
        queue/event-store runtime, provenance artifact, visual QA runtime, or
        Kimi-level quality claim.
        """
        if self.plan_snapshot_service is None:
            raise ValueError("Slides saved-plan retry requires plan_snapshot_service.")
        if self.artifact_service is None:
            raise ValueError("Slides saved-plan retry requires artifact_service.")

        return retry_saved_plan_with_lifecycle(
            SavedPlanRetryRequest(
                saved_plan_snapshot_id=saved_plan_snapshot_id,
                session_id=session_id,
                retry_task_id=retry_task_id,
                parent_task_id=parent_task_id,
                presentation_id=presentation_id,
                operator_instruction=operator_instruction,
                render_mode=render_mode,  # type: ignore[arg-type]
                template_id=template_id,
                new_plan_snapshot_id=new_plan_snapshot_id,
                new_presentation_version_id=new_presentation_version_id,
                artifact_filename=artifact_filename,
                operator_user_id=operator_user_id,
            ),
            plan_snapshot_service=self.plan_snapshot_service,  # type: ignore[arg-type]
            artifact_service=self.artifact_service,  # type: ignore[arg-type]
        )

    def _attach_generated_visuals(
        self,
        plan: PresentationPlan,
        *,
        session_id: str | None,
        task_id: str | None,
        owner_user_id: str,
    ) -> tuple[PresentationPlan, tuple[str, ...]]:
        updated_slides: list[PlannedSlide] = []
        stored_file_ids: list[str] = []
        for slide in plan.slides:
            if not slide.image_specs:
                updated_slides.append(slide)
                continue

            assets = []
            for spec in slide.image_specs:
                asset = self.image_provider.generate(spec)
                if self.image_registry is not None and session_id is not None and task_id is not None:
                    registered = self.image_registry.register_generated_asset(
                        session_id=session_id,
                        task_id=task_id,
                        owner_user_id=owner_user_id,
                        spec=spec,
                        asset=asset,
                    )
                    asset = registered.asset
                    stored_file_ids.append(registered.stored_file.id)
                assets.append(asset)
            updated_slides.append(replace(slide, media_assets=tuple(assets)))

        return replace(plan, slides=tuple(updated_slides)), tuple(stored_file_ids)
