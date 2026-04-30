"use client";

import { useMemo, useState } from "react";
import {
  formatDateTime,
  getPresentationRevisionDiff,
  getPresentationVersionPlan,
  listPresentationVersions,
  restorePresentationVersion,
  type PresentationPlanDiff,
  type PresentationPlanSnapshot,
  type PresentationRestoreResponse,
  type PresentationSummary,
  type PresentationVersionSummary,
} from "@/lib/api/presentations";

const mutedTextStyle = { color: "#6b7280", fontSize: "0.875rem" };
const buttonStyle = {
  border: "1px solid #111827",
  borderRadius: "0.375rem",
  background: "#111827",
  color: "#ffffff",
  padding: "0.45rem 0.7rem",
  cursor: "pointer",
};
const secondaryButtonStyle = { ...buttonStyle, background: "#ffffff", color: "#111827" };
const dangerButtonStyle = { ...buttonStyle, background: "#991b1b", borderColor: "#991b1b" };
const inputStyle = {
  border: "1px solid #d1d5db",
  borderRadius: "0.375rem",
  padding: "0.45rem 0.7rem",
  width: "100%",
  boxSizing: "border-box" as const,
};
const sectionStyle = { borderTop: "1px solid #e5e7eb", marginTop: "1rem", paddingTop: "1rem" };

type TimelineState = {
  status: "idle" | "loading_versions" | "loading_plan" | "loading_diff" | "loaded" | "error";
  error: string | null;
  versions: PresentationVersionSummary[];
  selectedVersionId: string | null;
  selectedPlan: PresentationPlanSnapshot | null;
  selectedDiff: PresentationPlanDiff | null;
};

export function VersionTimelinePanel({
  presentation,
  onRestoreApplied,
}: {
  presentation: PresentationSummary;
  onRestoreApplied?: () => Promise<void> | void;
}) {
  const [restoreConfirmation, setRestoreConfirmation] = useState("");
  const [restoreTargetVersionId, setRestoreTargetVersionId] = useState("");
  const [restoreReason, setRestoreReason] = useState("");
  const [restoreResult, setRestoreResult] = useState<PresentationRestoreResponse | null>(null);
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
  const normalizedRestoreReason = restoreReason.trim();
  const canLoadSelectedPlan = Boolean(selectedVersion);
  const canLoadSelectedDiff = Boolean(selectedVersion?.parent_version_id);
  const canRestoreSelected = Boolean(
    selectedVersion &&
      restoreConfirmation.trim() === "RESTORE" &&
      restoreTargetVersionId.trim() === selectedVersion.id &&
      normalizedRestoreReason.length >= 8 &&
      state.status !== "loading_diff",
  );

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
    setRestoreResult(null);
    setRestoreConfirmation("");
    setRestoreTargetVersionId("");
    setRestoreReason("");
  }

  async function loadSelectedPlan() {
    if (!selectedVersion) return;
    setState((current) => ({ ...current, status: "loading_plan", error: null }));
    try {
      const selectedPlan = await getPresentationVersionPlan(presentation.id, selectedVersion.id);
      setState((current) => ({ ...current, status: "loaded", error: null, selectedPlan }));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        error: error instanceof Error ? error.message : "Unable to load selected version plan.",
      }));
    }
  }

  async function loadSelectedDiff() {
    if (!selectedVersion?.parent_version_id) return;
    setState((current) => ({ ...current, status: "loading_diff", error: null }));
    try {
      const selectedDiff = await getPresentationRevisionDiff(presentation.id, selectedVersion.id);
      setState((current) => ({ ...current, status: "loaded", error: null, selectedDiff }));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        error: error instanceof Error ? error.message : "Unable to load selected version diff.",
      }));
    }
  }

  async function restoreSelectedVersion() {
    if (!selectedVersion) return;
    if (restoreConfirmation.trim() !== "RESTORE") {
      setState((current) => ({ ...current, status: "error", error: "Type RESTORE to confirm version restore." }));
      return;
    }
    if (restoreTargetVersionId.trim() !== selectedVersion.id) {
      setState((current) => ({
        ...current,
        status: "error",
        error: "Type the selected version id to confirm the restore target.",
      }));
      return;
    }
    if (normalizedRestoreReason.length < 8) {
      setState((current) => ({
        ...current,
        status: "error",
        error: "Enter a restore reason of at least 8 characters.",
      }));
      return;
    }

    setState((current) => ({ ...current, status: "loading_diff", error: null }));
    try {
      const result = await restorePresentationVersion(presentation.id, selectedVersion.id, {
        confirmation: restoreConfirmation,
        confirmation_target_version_id: restoreTargetVersionId.trim(),
        restore_reason: normalizedRestoreReason,
        change_summary: `Restore to v${selectedVersion.version_number}: ${normalizedRestoreReason}`,
      });
      const versions = await listPresentationVersions(presentation.id);
      const latest = [...versions].sort((left, right) => right.version_number - left.version_number)[0] ?? null;
      setRestoreResult(result);
      setRestoreConfirmation("");
      setRestoreTargetVersionId("");
      setRestoreReason("");
      setState((current) => ({
        ...current,
        status: "loaded",
        error: null,
        versions,
        selectedVersionId: latest?.id ?? result.restored_version_id,
        selectedPlan: null,
        selectedDiff: null,
      }));
      await onRestoreApplied?.();
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        error: error instanceof Error ? error.message : "Unable to restore selected version.",
      }));
    }
  }

  return (
    <section style={sectionStyle} aria-labelledby={`timeline-${presentation.id}`}>
      <h4 id={`timeline-${presentation.id}`}>Version timeline</h4>
      <p style={mutedTextStyle}>
        Inspect saved presentation versions, select a historical version, compare it with its parent, and restore only
        with explicit audit metadata.
      </p>

      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <button type="button" style={secondaryButtonStyle} onClick={() => void loadVersions()} disabled={state.status === "loading_versions"}>
          {state.status === "loading_versions" ? "Loading versions..." : "Load version timeline"}
        </button>
        <button type="button" style={secondaryButtonStyle} onClick={() => void loadSelectedPlan()} disabled={!canLoadSelectedPlan || state.status === "loading_plan"}>
          {state.status === "loading_plan" ? "Loading selected plan..." : "Load selected version plan"}
        </button>
        <button type="button" style={secondaryButtonStyle} onClick={() => void loadSelectedDiff()} disabled={!canLoadSelectedDiff || state.status === "loading_diff"}>
          {state.status === "loading_diff" ? "Loading selected diff..." : "Load selected version diff"}
        </button>
      </div>

      {state.error ? <p role="alert" style={{ color: "#b91c1c" }}>{state.error}</p> : null}

      {sortedVersions.length > 0 ? (
        <ol>
          {sortedVersions.map((version) => {
            const selected = version.id === state.selectedVersionId;
            return (
              <li key={version.id} style={{ marginTop: "0.5rem" }}>
                <strong>v{version.version_number} · {version.id}</strong>{" "}
                <button type="button" style={selected ? buttonStyle : secondaryButtonStyle} onClick={() => selectVersion(version.id)}>
                  Select version v{version.version_number}
                </button>
                {selected ? <span style={mutedTextStyle}> Selected</span> : null}
                <div style={mutedTextStyle}>Parent: {version.parent_version_id ?? "none"} · File: {version.file_id}</div>
                <div style={mutedTextStyle}>{version.change_summary ?? "No change summary"} · {formatDateTime(version.created_at)}</div>
              </li>
            );
          })}
        </ol>
      ) : null}

      {state.status === "loaded" && sortedVersions.length === 0 ? (
        <p style={mutedTextStyle}>No presentation versions are available.</p>
      ) : null}

      <section style={sectionStyle} aria-labelledby={`restore-${presentation.id}`}>
        <h5 id={`restore-${presentation.id}`}>Restore selected version</h5>
        <p style={mutedTextStyle}>
          This creates a new restore version and does not delete historical versions. Type RESTORE, type the selected
          version id, and provide a restore reason to enable the action.
        </p>
        <p style={mutedTextStyle}>Selected target: {selectedVersion ? `v${selectedVersion.version_number} · ${selectedVersion.id}` : "none"}</p>

        <label style={{ display: "grid", gap: "0.25rem", marginTop: "0.5rem" }}>
          Restore confirmation
          <input value={restoreConfirmation} onChange={(event) => setRestoreConfirmation(event.target.value)} placeholder="Type RESTORE" style={inputStyle} />
        </label>

        <label style={{ display: "grid", gap: "0.25rem", marginTop: "0.5rem" }}>
          Restore target version id
          <input value={restoreTargetVersionId} onChange={(event) => setRestoreTargetVersionId(event.target.value)} placeholder={selectedVersion?.id ?? "Select a version first"} style={inputStyle} />
        </label>

        <label style={{ display: "grid", gap: "0.25rem", marginTop: "0.5rem" }}>
          Restore reason
          <textarea value={restoreReason} onChange={(event) => setRestoreReason(event.target.value)} placeholder="Explain why this restore is required." style={{ ...inputStyle, minHeight: "4rem" }} />
        </label>

        <button type="button" style={dangerButtonStyle} onClick={() => void restoreSelectedVersion()} disabled={!canRestoreSelected}>
          Restore selected version
        </button>

        {restoreResult ? (
          <div role="status" style={{ marginTop: "0.75rem" }}>
            <p>Restored v{restoreResult.target_version_number} as v{restoreResult.restored_version_number} · {restoreResult.restored_version_id}</p>
            {restoreResult.audit_summary ? <p>Restore audit: {restoreResult.audit_summary}</p> : null}
            {restoreResult.restore_reason ? <p>Restore reason: {restoreResult.restore_reason}</p> : null}
          </div>
        ) : null}
      </section>

      {selectedVersion && !selectedVersion.parent_version_id ? (
        <p style={mutedTextStyle}>Selected version has no parent, so selected diff is not available.</p>
      ) : null}

      {state.selectedPlan ? <SelectedVersionPlanCard snapshot={state.selectedPlan} /> : null}
      {state.selectedDiff ? <SelectedVersionDiffCard diff={state.selectedDiff} /> : null}
    </section>
  );
}

function SelectedVersionPlanCard({ snapshot }: { snapshot: PresentationPlanSnapshot }) {
  const slides = Array.isArray(snapshot.plan.slides) ? snapshot.plan.slides : [];

  return (
    <section style={sectionStyle}>
      <h5>Selected version plan snapshot</h5>
      <p style={mutedTextStyle}>{snapshot.snapshot_id} · {snapshot.presentation_version_id ?? "no version"} · {formatDateTime(snapshot.created_at)}</p>
      <p>{snapshot.plan.deck_title ?? "Untitled deck"}</p>
      <p style={mutedTextStyle}>Target slides: {snapshot.plan.target_slide_count ?? "unknown"} · Snapshot slides: {slides.length}</p>
      {slides.length > 0 ? (
        <ol>
          {slides.slice(0, 6).map((slide, index) => (
            <li key={slide.slide_id ?? index}>
              <span>{slide.title ?? slide.slide_id ?? `Slide ${index + 1}`}</span>
              <span style={mutedTextStyle}>
                {" "}· {slide.slide_type ?? "slide"} · {slide.story_arc_stage ?? "stage unknown"}
              </span>
            </li>
          ))}
        </ol>
      ) : (
        <p style={mutedTextStyle}>No slide outline is available in this snapshot.</p>
      )}
    </section>
  );
}

function SelectedVersionDiffCard({ diff }: { diff: PresentationPlanDiff }) {
  return (
    <section style={sectionStyle}>
      <h5>Selected version diff</h5>
      <p style={mutedTextStyle}>{diff.base_version_id} → {diff.compared_version_id} · {diff.changed_slide_count} changed slide(s)</p>
      {diff.slide_deltas.length > 0 ? (
        <ul>
          {diff.slide_deltas.map((delta) => (
            <li key={delta.slide_id}>
              <strong>{delta.slide_id} · {delta.change_type}</strong>
              <div>{delta.title_before ?? "Untitled"} → {delta.title_after ?? "Untitled"}</div>
              {delta.bullets_added.length > 0 ? <div>Added bullets: {delta.bullets_added.join("; ")}</div> : null}
              {delta.bullets_removed.length > 0 ? <div>Removed bullets: {delta.bullets_removed.join("; ")}</div> : null}
            </li>
          ))}
        </ul>
      ) : (
        <p style={mutedTextStyle}>No structural plan changes were detected for the selected version.</p>
      )}
    </section>
  );
}
