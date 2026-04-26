"use client";

import { useMemo, useState } from "react";
import {
  formatDateTime,
  getPresentationRevisionDiff,
  getPresentationVersionPlan,
  listPresentationVersions,
  type PresentationPlanDiff,
  type PresentationPlanSnapshot,
  type PresentationSummary,
  type PresentationVersionSummary,
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

type TimelineState = {
  status: "idle" | "loading_versions" | "loading_plan" | "loading_diff" | "loaded" | "error";
  error: string | null;
  versions: PresentationVersionSummary[];
  selectedVersionId: string | null;
  selectedPlan: PresentationPlanSnapshot | null;
  selectedDiff: PresentationPlanDiff | null;
};

export function VersionTimelinePanel({ presentation }: { presentation: PresentationSummary }) {
  const [state, setState] = useState<TimelineState>({
    status: "idle",
    error: null,
    versions: [],
    selectedVersionId: null,
    selectedPlan: null,
    selectedDiff: null,
  });

  const sortedVersions = useMemo(
    () => [...state.versions].sort((left, right) => right.version_number - left.version_number),
    [state.versions],
  );
  const selectedVersion = state.versions.find((version) => version.id === state.selectedVersionId) ?? null;
  const canLoadSelectedPlan = Boolean(selectedVersion);
  const canLoadSelectedDiff = Boolean(selectedVersion?.parent_version_id);

  async function loadVersions() {
    setState((current) => ({ ...current, status: "loading_versions", error: null }));
    try {
      const versions = await listPresentationVersions(presentation.id);
      const latest = [...versions].sort((left, right) => right.version_number - left.version_number)[0] ?? null;
      setState((current) => ({
        ...current,
        status: "loaded",
        error: null,
        versions,
        selectedVersionId: latest?.id ?? null,
        selectedPlan: null,
        selectedDiff: null,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        error: error instanceof Error ? error.message : "Unable to load version timeline.",
      }));
    }
  }

  function selectVersion(versionId: string) {
    setState((current) => ({
      ...current,
      selectedVersionId: versionId,
      selectedPlan: null,
      selectedDiff: null,
      error: null,
    }));
  }

  async function loadSelectedPlan() {
    if (!selectedVersion) {
      return;
    }
    setState((current) => ({ ...current, status: "loading_plan", error: null }));
    try {
      const selectedPlan = await getPresentationVersionPlan(presentation.id, selectedVersion.id);
      setState((current) => ({
        ...current,
        status: "loaded",
        error: null,
        selectedPlan,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        error: error instanceof Error ? error.message : "Unable to load selected version plan.",
      }));
    }
  }

  async function loadSelectedDiff() {
    if (!selectedVersion?.parent_version_id) {
      return;
    }
    setState((current) => ({ ...current, status: "loading_diff", error: null }));
    try {
      const selectedDiff = await getPresentationRevisionDiff(presentation.id, selectedVersion.id);
      setState((current) => ({
        ...current,
        status: "loaded",
        error: null,
        selectedDiff,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        error: error instanceof Error ? error.message : "Unable to load selected version diff.",
      }));
    }
  }

  return (
    <section style={sectionStyle} aria-labelledby="version-timeline-title">
      <h4 id="version-timeline-title">Version timeline</h4>
      <p style={mutedTextStyle}>
        Inspect saved presentation versions, select a historical version, and compare it with its parent.
      </p>

      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.75rem" }}>
        <button
          type="button"
          style={buttonStyle}
          onClick={() => void loadVersions()}
          disabled={state.status === "loading_versions"}
        >
          {state.status === "loading_versions" ? "Loading versions..." : "Load version timeline"}
        </button>
        <button
          type="button"
          style={secondaryButtonStyle}
          onClick={() => void loadSelectedPlan()}
          disabled={!canLoadSelectedPlan || state.status === "loading_plan"}
        >
          {state.status === "loading_plan" ? "Loading selected plan..." : "Load selected version plan"}
        </button>
        <button
          type="button"
          style={secondaryButtonStyle}
          onClick={() => void loadSelectedDiff()}
          disabled={!canLoadSelectedDiff || state.status === "loading_diff"}
        >
          {state.status === "loading_diff" ? "Loading selected diff..." : "Load selected version diff"}
        </button>
      </div>

      {state.error ? (
        <div role="alert" style={{ marginTop: "0.75rem", color: "#991b1b", background: "#fef2f2", padding: "0.75rem", borderRadius: "0.375rem" }}>
          {state.error}
        </div>
      ) : null}

      {sortedVersions.length > 0 ? (
        <ol style={{ paddingLeft: 0, listStyle: "none", marginTop: "0.75rem" }}>
          {sortedVersions.map((version) => {
            const selected = version.id === state.selectedVersionId;
            return (
              <li
                key={version.id}
                style={{
                  border: selected ? "2px solid #111827" : "1px solid #e5e7eb",
                  borderRadius: "0.5rem",
                  padding: "0.75rem",
                  marginBottom: "0.5rem",
                  background: "#ffffff",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: "0.75rem" }}>
                  <div>
                    <strong>v{version.version_number}</strong>
                    <span style={mutedTextStyle}> · {version.id}</span>
                  </div>
                  <button
                    type="button"
                    style={selected ? buttonStyle : secondaryButtonStyle}
                    aria-label={`Select version v${version.version_number}`}
                    onClick={() => selectVersion(version.id)}
                  >
                    {selected ? "Selected" : "Select"}
                  </button>
                </div>
                <div style={{ ...mutedTextStyle, marginTop: "0.35rem" }}>
                  Parent: {version.parent_version_id ?? "none"} · File: {version.file_id}
                </div>
                <div style={{ ...mutedTextStyle, marginTop: "0.35rem" }}>
                  {version.change_summary ?? "No change summary"} · {formatDateTime(version.created_at)}
                </div>
              </li>
            );
          })}
        </ol>
      ) : null}

      {state.status === "loaded" && sortedVersions.length === 0 ? (
        <p style={{ ...mutedTextStyle, marginTop: "0.75rem" }}>No presentation versions are available.</p>
      ) : null}

      {selectedVersion && !selectedVersion.parent_version_id ? (
        <p style={{ ...mutedTextStyle, marginTop: "0.75rem" }}>
          Selected version has no parent, so selected diff is not available.
        </p>
      ) : null}

      {state.selectedPlan ? <SelectedVersionPlanCard snapshot={state.selectedPlan} /> : null}
      {state.selectedDiff ? <SelectedVersionDiffCard diff={state.selectedDiff} /> : null}
    </section>
  );
}

function SelectedVersionPlanCard({ snapshot }: { snapshot: PresentationPlanSnapshot }) {
  const slides = Array.isArray(snapshot.plan.slides) ? snapshot.plan.slides : [];

  return (
    <article style={{ marginTop: "1rem", border: "1px solid #e5e7eb", borderRadius: "0.5rem", padding: "0.75rem", background: "#ffffff" }}>
      <h5 style={{ marginTop: 0 }}>Selected version plan snapshot</h5>
      <p style={mutedTextStyle}>
        {snapshot.snapshot_id} · {snapshot.presentation_version_id ?? "no version"} · {formatDateTime(snapshot.created_at)}
      </p>
      <p>
        <strong>{snapshot.plan.deck_title ?? "Untitled deck"}</strong>
      </p>
      <p style={mutedTextStyle}>
        Target slides: {snapshot.plan.target_slide_count ?? "unknown"} · Snapshot slides: {slides.length}
      </p>
      {slides.length > 0 ? (
        <ol style={{ paddingLeft: "1.25rem" }}>
          {slides.slice(0, 6).map((slide, index) => (
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
    </article>
  );
}

function SelectedVersionDiffCard({ diff }: { diff: PresentationPlanDiff }) {
  return (
    <article style={{ marginTop: "1rem", border: "1px solid #e5e7eb", borderRadius: "0.5rem", padding: "0.75rem", background: "#ffffff" }}>
      <h5 style={{ marginTop: 0 }}>Selected version diff</h5>
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
            </li>
          ))}
        </ul>
      ) : (
        <p style={mutedTextStyle}>No structural plan changes were detected for the selected version.</p>
      )}
    </article>
  );
}
