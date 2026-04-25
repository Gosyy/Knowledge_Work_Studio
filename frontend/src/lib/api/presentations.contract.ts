import { formatBytes, formatDateTime, type PresentationSummary } from "./presentations";

const samplePresentation: PresentationSummary = {
  id: "pres_frontend_contract",
  session_id: "ses_frontend_contract",
  current_file_id: "sf_current",
  presentation_type: "generated_deck",
  title: "Frontend Contract Deck",
  status: "active",
  created_at: "2026-04-25T12:00:00Z",
  updated_at: "2026-04-25T12:05:00Z",
  current_file: {
    id: "sf_current",
    kind: "presentation_deck",
    file_type: "pptx",
    mime_type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    title: "Frontend Contract Deck",
    original_filename: "frontend_contract.pptx",
    checksum_sha256: "abc123",
    size_bytes: 2048,
    created_at: "2026-04-25T12:00:00Z",
    updated_at: "2026-04-25T12:00:00Z",
  },
  latest_version: {
    id: "presver_current",
    version_number: 1,
    file_id: "sf_current",
    parent_version_id: null,
    change_summary: "Initial version",
    created_at: "2026-04-25T12:00:00Z",
  },
};

if (formatBytes(samplePresentation.current_file?.size_bytes ?? null) !== "2.0 KB") {
  throw new Error("Presentation registry byte formatter contract failed.");
}

if (formatDateTime(samplePresentation.updated_at).length === 0) {
  throw new Error("Presentation registry date formatter contract failed.");
}

export { samplePresentation };
