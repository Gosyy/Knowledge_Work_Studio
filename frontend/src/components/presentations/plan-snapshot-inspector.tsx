"use client";

import { useMemo, useState } from "react";
import {
  formatDateTime,
  getCurrentPresentationPlan,
  getPresentationRevisionDiff,
  getPresentationVersionPlan,
  type PresentationPlanDiff,
  type PresentationPlanSnapshot,
  type PresentationSummary,
} from "@/lib/api/presentations";

const mutedTextStyle = {
  color: "#6b7280",
  fontSize: "0.875rem",
};

const buttonStyle = {
  border: "1px solid #111827",
  borderRadius: "0.375rem",
  background: "#111827",
  color: "#ffffff",
  padding: "0.45rem 0.7rem",
  cursor: "pointer",
};

const secondaryButtonStyle = {
  ...buttonStyle,
  background: "#ffffff",
  color: "#111827",
};

const sectionStyle = {
  borderTop: "1px solid #e5e7eb",
  marginTop: "1rem",
  paddingTop: "1rem",
};

type InspectorState = {
  status: "idle" | "loading_plan" | "loading_version_plan" | "loading_diff" | "loaded" | "error";
  error: string | null;
  currentPlan: PresentationPlanSnapshot | null;
  versionPlan: PresentationPlanSnapshot | null;
  diff: PresentationPlanDiff | null;
};

export function PlanSnapshotInspector({ presentation }: { presentation: PresentationSummary }) {
  const [state, setState] = useState<InspectorState>({
    status: "idle",
    error: null,
    currentPlan: null,
    versionPlan: null,
    diff: null,
  });

  const latestVersion = presentation.latest_version;
  const canLoadVersionPlan = Boolean(latestVersion?.id);
  const canLoadDiff = Boolean(latestVersion?.id && latestVersion.parent_version_id);

  const slideCount = useMemo(() => {
    const slides = state.currentPlan?.plan.slides ?? state.versionPlan?.plan.slides;
    return Array.isArray(slides) ? slides.length : 0;
  }, [state.currentPlan, state.versionPlan]);

  async function loadCurrentPlan() {
    setState((current) => ({ ...current, status: "loading_plan", error: null }));
    try {
      const currentPlan = await getCurrentPresentationPlan(presentation.id);
      setState((current) => ({
        ...current,
        status: "loaded",
        error: null,
        currentPlan,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        error: error instanceof Error ? error.message : "Unable to load current plan snapshot.",
      }));
    }
  }

  async function loadLatestVersionPlan() {
    if (!latestVersion?.id) {
      return;
    }
    setState((current) => ({ ...current, status: "loading_version_plan", error: null }));
    try {
      const versionPlan = await getPresentationVersionPlan(presentation.id, latestVersion.id);
      setState((current) => ({
        ...current,
        status: "loaded",
        error: null,
        versionPlan,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        error: error instanceof Error ? error.message : "Unable to load latest version plan.",
      }));
    }
  }

  async function loadLatestDiff() {
    if (!latestVersion?.id || !latestVersion.parent_version_id) {
      return;
    }
    setState((current) => ({ ...current, status: "loading_diff", error: null }));
    try {
      const diff = await getPresentationRevisionDiff(presentation.id, latestVersion.id);
      setState((current) => ({
        ...current,
        status: "loaded",
        error: null,
        diff,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        error: error instanceof Error ? error.message : "Unable to load latest revision diff.",
      }));
    }
  }

  return (
    <section style={sectionStyle} aria-labelledby="plan-snapshot-inspector-title">
      <h4 id="plan-snapshot-inspector-title">Editable plan</h4>
      <p style={mutedTextStyle}>
        Inspect saved PresentationPlan snapshots and the latest revision diff without editing the deck.
      </p>

      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.75rem" }}>
        <button
          type="button"
          style={buttonStyle}
          onClick={() => void loadCurrentPlan()}
          disabled={state.status === "loading_plan"}
        >
          {state.status === "loading_plan" ? "Loading plan..." : "Load current plan"}
        </button>
        <button
          type="button"
          style={secondaryButtonStyle}
          onClick={() => void loadLatestVersionPlan()}
          disabled={!canLoadVersionPlan || state.status === "loading_version_plan"}
        >
          {state.status === "loading_version_plan" ? "Loading version..." : "Load latest version plan"}
        </button>
        <button
          type="button"
          style={secondaryButtonStyle}
          onClick={() => void loadLatestDiff()}
          disabled={!canLoadDiff || state.status === "loading_diff"}
        >
          {state.status === "loading_diff" ? "Loading diff..." : "Load latest diff"}
        </button>
      </div>

      {!canLoadDiff ? (
        <p style={{ ...mutedTextStyle, marginTop: "0.75rem" }}>
          Latest version has no parent version, so revision diff is not available yet.
        </p>
      ) : null}

      {state.error ? (
        <div role="alert" style={{ marginTop: "0.75rem", color: "#991b1b", background: "#fef2f2", padding: "0.75rem", borderRadius: "0.375rem" }}>
          {state.error}
        </div>
      ) : null}

      {state.currentPlan ? (
        <PlanSnapshotCard title="Current plan snapshot" snapshot={state.currentPlan} slideCount={slideCount} />
      ) : null}

      {state.versionPlan ? (
        <PlanSnapshotCard title="Latest version plan snapshot" snapshot={state.versionPlan} slideCount={slideCount} />
      ) : null}

      {state.diff ? <PlanDiffCard diff={state.diff} /> : null}
    </section>
  );
}

function PlanSnapshotCard({
  title,
  snapshot,
  slideCount,
}: {
  title: string;
  snapshot: PresentationPlanSnapshot;
  slideCount: number;
}) {
  const slides = Array.isArray(snapshot.plan.slides) ? snapshot.plan.slides : [];

  return (
    <article style={{ marginTop: "1rem", border: "1px solid #e5e7eb", borderRadius: "0.5rem", padding: "0.75rem", background: "#ffffff" }}>
      <h5 style={{ marginTop: 0 }}>{title}</h5>
      <p style={mutedTextStyle}>
        {snapshot.snapshot_id} · {snapshot.presentation_version_id ?? "no version"} · {formatDateTime(snapshot.created_at)}
      </p>
      <p>
        <strong>{snapshot.plan.deck_title ?? "Untitled deck"}</strong>
      </p>
      <p style={mutedTextStyle}>
        Target slides: {snapshot.plan.target_slide_count ?? "unknown"} · Snapshot slides: {slideCount}
      </p>
      {snapshot.change_summary ? <p style={mutedTextStyle}>Change: {snapshot.change_summary}</p> : null}

      {slides.length > 0 ? (
        <ol style={{ paddingLeft: "1.25rem" }}>
          {slides.slice(0, 8).map((slide, index) => (
            <li key={`${slide.slide_id ?? "slide"}-${index}`} style={{ marginBottom: "0.35rem" }}>
              <strong>{slide.title ?? slide.slide_id ?? `Slide ${index + 1}`}</strong>
              <span style={mutedTextStyle}>
                {" "}
                · {slide.slide_type ?? "slide"} · {slide.story_arc_stage ?? "stage unknown"}
              </span>
            </li>
          ))}
        </ol>
      ) : (
        <p style={mutedTextStyle}>No slide outline is available in this snapshot.</p>
      )}
      {slides.length > 8 ? <p style={mutedTextStyle}>Showing first 8 slides of {slides.length}.</p> : null}
    </article>
  );
}

function PlanDiffCard({ diff }: { diff: PresentationPlanDiff }) {
  return (
    <article style={{ marginTop: "1rem", border: "1px solid #e5e7eb", borderRadius: "0.5rem", padding: "0.75rem", background: "#ffffff" }}>
      <h5 style={{ marginTop: 0 }}>Latest revision diff</h5>
      <p style={mutedTextStyle}>
        {diff.base_version_id} → {diff.compared_version_id} · {diff.changed_slide_count} changed slide(s)
      </p>
      {diff.slide_deltas.length > 0 ? (
        <ul style={{ paddingLeft: "1.25rem" }}>
          {diff.slide_deltas.map((delta) => (
            <li key={delta.slide_id} style={{ marginBottom: "0.75rem" }}>
              <strong>{delta.slide_id}</strong>
              <span style={mutedTextStyle}> · {delta.change_type}</span>
              <div>{delta.title_before ?? "Untitled"} → {delta.title_after ?? "Untitled"}</div>
              {delta.bullets_added.length > 0 ? (
                <div style={mutedTextStyle}>Added bullets: {delta.bullets_added.join("; ")}</div>
              ) : null}
              {delta.bullets_removed.length > 0 ? (
                <div style={mutedTextStyle}>Removed bullets: {delta.bullets_removed.join("; ")}</div>
              ) : null}
              {delta.speaker_notes_changed ? (
                <div style={mutedTextStyle}>Speaker notes changed.</div>
              ) : null}
            </li>
          ))}
        </ul>
      ) : (
        <p style={mutedTextStyle}>No structural plan changes were detected.</p>
      )}
    </article>
  );
}
