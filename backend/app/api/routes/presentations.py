from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_current_user_id, get_presentation_catalog_service
from backend.app.api.schemas import PresentationSchema
from backend.app.services import PresentationCatalogService

router = APIRouter(tags=["presentations"])


@router.get("/sessions/{session_id}/presentations", response_model=list[PresentationSchema])
def list_session_presentations(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: PresentationCatalogService = Depends(get_presentation_catalog_service),
) -> list[PresentationSchema]:
    presentations = service.list_session_presentations_for_user(
        session_id=session_id,
        owner_user_id=current_user_id,
    )
    return [PresentationSchema(**presentation.__dict__) for presentation in presentations]


@router.get("/presentations/{presentation_id}", response_model=PresentationSchema)
def get_presentation(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: PresentationCatalogService = Depends(get_presentation_catalog_service),
) -> PresentationSchema:
    presentation = service.get_presentation_for_user(
        presentation_id=presentation_id,
        owner_user_id=current_user_id,
    )
    return PresentationSchema(**presentation.__dict__)
