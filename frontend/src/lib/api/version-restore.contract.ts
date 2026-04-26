import {
  type PresentationRestoreRequest,
  type PresentationRestoreResponse,
} from "./presentations";

const restoreRequest: PresentationRestoreRequest = {
  confirmation: "RESTORE",
  change_summary: "Restore previous accepted version",
  task_id: "task_restore_contract",
};

const restoreResponse: PresentationRestoreResponse = {
  presentation_id: "pres_contract",
  restored_version_id: "presver_contract_v3",
  restored_version_number: 3,
  target_version_id: "presver_contract_v1",
  target_version_number: 1,
  parent_version_id: "presver_contract_v2",
  current_file_id: "sf_contract_v1",
  previous_file_id: "sf_contract_v2",
  change_summary: "Restore previous accepted version",
  created_at: "2026-04-25T12:20:00Z",
};

if (restoreRequest.confirmation !== "RESTORE") {
  throw new Error("Restore request frontend contract failed.");
}

if (restoreResponse.current_file_id !== "sf_contract_v1") {
  throw new Error("Restore response frontend contract failed.");
}

export { restoreRequest, restoreResponse };
