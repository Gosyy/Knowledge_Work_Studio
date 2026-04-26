import {
  type PresentationPlanDiff,
  type PresentationPlanSnapshot,
  type PresentationVersionSummary,
} from "./presentations";

const versionTimeline: PresentationVersionSummary[] = [
  {
    id: "presver_contract_v1",
    version_number: 1,
    file_id: "sf_contract_v1",
    parent_version_id: null,
    change_summary: "Initial version",
    created_at: "2026-04-25T12:00:00Z",
  },
  {
    id: "presver_contract_v2",
    version_number: 2,
    file_id: "sf_contract_v2",
    parent_version_id: "presver_contract_v1",
    change_summary: "Revision",
    created_at: "2026-04-25T12:10:00Z",
  },
];

const selectedVersionPlan: PresentationPlanSnapshot = {
  snapshot_id: "plansnap_contract_v2",
  presentation_id: "pres_contract",
  presentation_version_id: "presver_contract_v2",
  created_from_task_id: "task_contract",
  change_summary: "Revision",
  created_at: "2026-04-25T12:10:00Z",
  plan: {
    schema_version: 1,
    deck_title: "Contract timeline deck",
    target_slide_count: 1,
    slides: [{ slide_id: "slide_001", title: "Timeline slide", bullets: ["Stable"] }],
  },
};

const selectedVersionDiff: PresentationPlanDiff = {
  presentation_id: "pres_contract",
  base_version_id: "presver_contract_v1",
  compared_version_id: "presver_contract_v2",
  base_snapshot_id: "plansnap_contract_v1",
  compared_snapshot_id: "plansnap_contract_v2",
  changed_slide_count: 1,
  slide_deltas: [
    {
      slide_id: "slide_001",
      change_type: "modified",
      before_index: 0,
      after_index: 0,
      title_before: "Before",
      title_after: "After",
      story_arc_stage_before: "opening",
      story_arc_stage_after: "opening",
      layout_hint_before: null,
      layout_hint_after: null,
      bullets_added: ["Stable"],
      bullets_removed: [],
      speaker_notes_changed: false,
    },
  ],
};

if (versionTimeline[1]?.parent_version_id !== "presver_contract_v1") {
  throw new Error("Version timeline frontend contract failed.");
}

if (selectedVersionPlan.presentation_version_id !== "presver_contract_v2") {
  throw new Error("Selected version plan frontend contract failed.");
}

if (selectedVersionDiff.changed_slide_count !== 1) {
  throw new Error("Selected version diff frontend contract failed.");
}

export { selectedVersionDiff, selectedVersionPlan, versionTimeline };
