import {
  type DeckRevisionResponse,
  type DeckSectionRevisionRequest,
  type DeckSlideRevisionRequest,
} from "./presentations";

const slideRevisionRequest: DeckSlideRevisionRequest = {
  instruction: "Make slide 3 sharper.",
  target_slide_index: 2,
  change_summary: "Sharpen slide 3",
};

const sectionRevisionRequest: DeckSectionRevisionRequest = {
  instruction: "Refresh the analysis section.",
  target_stage: "analysis",
  change_summary: "Refresh analysis section",
};

const revisionResponse: DeckRevisionResponse = {
  presentation_id: "pres_frontend_contract",
  version_id: "presver_frontend_contract_v2",
  version_number: 2,
  parent_version_id: "presver_frontend_contract_v1",
  stored_file_id: "sf_frontend_contract_v2",
  revised_slide_ids: ["slide_003"],
  scope: "slide",
  change_summary: "Sharpen slide 3",
  created_at: "2026-04-25T12:20:00Z",
  current_file_id: "sf_frontend_contract_v2",
  previous_file_id: "sf_frontend_contract_v1",
};

if (!slideRevisionRequest.instruction || slideRevisionRequest.target_slide_index !== 2) {
  throw new Error("Slide revision frontend contract failed.");
}

if (sectionRevisionRequest.target_stage !== "analysis") {
  throw new Error("Section revision frontend contract failed.");
}

if (revisionResponse.scope !== "slide" || revisionResponse.version_number !== 2) {
  throw new Error("Revision response frontend contract failed.");
}

export { revisionResponse, sectionRevisionRequest, slideRevisionRequest };
