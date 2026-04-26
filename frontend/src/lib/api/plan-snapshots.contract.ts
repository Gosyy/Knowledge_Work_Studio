import {
  formatDateTime,
  type PresentationPlanDiff,
  type PresentationPlanSnapshot,
} from "./presentations";

const sampleSnapshot: PresentationPlanSnapshot = {
  snapshot_id: "plansnap_frontend_contract",
  presentation_id: "pres_frontend_contract",
  presentation_version_id: "presver_frontend_contract",
  created_from_task_id: "task_frontend_contract",
  change_summary: "Frontend snapshot contract",
  created_at: "2026-04-25T12:10:00Z",
  plan: {
    schema_version: 1,
    deck_title: "Frontend Snapshot Deck",
    target_slide_count: 1,
    slides: [
      {
        slide_id: "slide_001",
        slide_type: "title",
        story_arc_stage: "opening",
        title: "Frontend Snapshot Deck",
        bullets: ["Contract-safe outline"],
      },
    ],
  },
};

const sampleDiff: PresentationPlanDiff = {
  presentation_id: "pres_frontend_contract",
  base_version_id: "presver_base",
  compared_version_id: "presver_compared",
  base_snapshot_id: "plansnap_base",
  compared_snapshot_id: "plansnap_compared",
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
      bullets_added: ["New bullet"],
      bullets_removed: [],
      speaker_notes_changed: true,
    },
  ],
};

if (sampleSnapshot.plan.slides?.[0]?.slide_id !== "slide_001") {
  throw new Error("Plan snapshot frontend contract failed.");
}

if (sampleDiff.slide_deltas[0]?.change_type !== "modified") {
  throw new Error("Plan diff frontend contract failed.");
}

if (formatDateTime(sampleSnapshot.created_at).length === 0) {
  throw new Error("Plan snapshot date formatting contract failed.");
}

export { sampleDiff, sampleSnapshot };
