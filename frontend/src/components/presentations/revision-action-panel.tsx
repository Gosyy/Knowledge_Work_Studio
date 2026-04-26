"use client";

import { FormEvent, useState } from "react";
import {
  formatDateTime,
  revisePresentationSectionWithoutPlan,
  revisePresentationSlideWithoutPlan,
  type DeckRevisionResponse,
  type PresentationSummary,
} from "@/lib/api/presentations";

const mutedTextStyle = {
  color: "#6b7280",
  fontSize: "0.875rem",
};

const inputStyle = {
  border: "1px solid #d1d5db",
  borderRadius: "0.375rem",
  padding: "0.5rem 0.75rem",
  width: "100%",
};

const buttonStyle = {
  border: "1px solid #111827",
  borderRadius: "0.375rem",
  background: "#111827",
  color: "#ffffff",
  padding: "0.5rem 0.75rem",
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

type RevisionMode = "slide" | "section";

type RevisionActionPanelProps = {
  presentation: PresentationSummary;
  onRevisionApplied: (revision: DeckRevisionResponse) => Promise<void> | void;
};

type RevisionUiState = {
  mode: RevisionMode;
  instruction: string;
  changeSummary: string;
  targetSlideIndex: string;
  targetSlideId: string;
  targetStage: string;
  status: "idle" | "submitting" | "success" | "error";
  error: string | null;
  lastRevision: DeckRevisionResponse | null;
};

export function RevisionActionPanel({ presentation, onRevisionApplied }: RevisionActionPanelProps) {
  const [state, setState] = useState<RevisionUiState>({
    mode: "slide",
    instruction: "",
    changeSummary: "",
    targetSlideIndex: "0",
    targetSlideId: "",
    targetStage: "analysis",
    status: "idle",
    error: null,
    lastRevision: null,
  });

  const canSubmit = state.instruction.trim().length > 0 && state.status !== "submitting";

  async function submitRevision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      setState((current) => ({
        ...current,
        status: "error",
        error: "Instruction is required before creating a revision.",
      }));
      return;
    }

    setState((current) => ({ ...current, status: "submitting", error: null }));
    try {
      const common = {
        instruction: state.instruction.trim(),
        change_summary: state.changeSummary.trim() || null,
      };

      const revision =
        state.mode === "slide"
          ? await revisePresentationSlideWithoutPlan(presentation.id, {
              ...common,
              target_slide_id: state.targetSlideId.trim() || null,
              target_slide_index: parseSlideIndex(state.targetSlideIndex),
            })
          : await revisePresentationSectionWithoutPlan(presentation.id, {
              ...common,
              target_stage: state.targetStage,
            });

      await onRevisionApplied(revision);
      setState((current) => ({
        ...current,
        status: "success",
        error: null,
        lastRevision: revision,
        instruction: "",
        changeSummary: "",
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        error: error instanceof Error ? error.message : "Unable to create deck revision.",
      }));
    }
  }

  return (
    <section style={sectionStyle} aria-labelledby="revision-action-panel-title">
      <h4 id="revision-action-panel-title">Revise deck</h4>
      <p style={mutedTextStyle}>
        Create a new deck revision from the latest saved plan snapshot. No explicit plan payload is sent from the UI.
      </p>

      <form onSubmit={submitRevision} style={{ display: "grid", gap: "0.75rem", marginTop: "0.75rem" }}>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <button
            type="button"
            style={state.mode === "slide" ? buttonStyle : secondaryButtonStyle}
            onClick={() => setState((current) => ({ ...current, mode: "slide", error: null }))}
          >
            Slide revision
          </button>
          <button
            type="button"
            style={state.mode === "section" ? buttonStyle : secondaryButtonStyle}
            onClick={() => setState((current) => ({ ...current, mode: "section", error: null }))}
          >
            Section revision
          </button>
        </div>

        <label>
          <span style={{ display: "block", fontSize: "0.875rem", marginBottom: "0.25rem" }}>
            Instruction
          </span>
          <textarea
            value={state.instruction}
            onChange={(event) => setState((current) => ({ ...current, instruction: event.target.value }))}
            placeholder="Make the analysis slide sharper and more executive."
            rows={4}
            style={{ ...inputStyle, resize: "vertical" }}
            aria-label="Revision instruction"
          />
        </label>

        <label>
          <span style={{ display: "block", fontSize: "0.875rem", marginBottom: "0.25rem" }}>
            Change summary
          </span>
          <input
            value={state.changeSummary}
            onChange={(event) => setState((current) => ({ ...current, changeSummary: event.target.value }))}
            placeholder="Short revision summary"
            style={inputStyle}
            aria-label="Revision change summary"
          />
        </label>

        {state.mode === "slide" ? (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <label>
              <span style={{ display: "block", fontSize: "0.875rem", marginBottom: "0.25rem" }}>
                Slide index, zero-based
              </span>
              <input
                type="number"
                min={0}
                value={state.targetSlideIndex}
                onChange={(event) => setState((current) => ({ ...current, targetSlideIndex: event.target.value }))}
                style={inputStyle}
                aria-label="Target slide index"
              />
            </label>
            <label>
              <span style={{ display: "block", fontSize: "0.875rem", marginBottom: "0.25rem" }}>
                Slide id, optional
              </span>
              <input
                value={state.targetSlideId}
                onChange={(event) => setState((current) => ({ ...current, targetSlideId: event.target.value }))}
                placeholder="slide_003"
                style={inputStyle}
                aria-label="Target slide id"
              />
            </label>
          </div>
        ) : (
          <label>
            <span style={{ display: "block", fontSize: "0.875rem", marginBottom: "0.25rem" }}>
              Story arc stage
            </span>
            <select
              value={state.targetStage}
              onChange={(event) => setState((current) => ({ ...current, targetStage: event.target.value }))}
              style={inputStyle}
              aria-label="Target story arc stage"
            >
              <option value="opening">opening</option>
              <option value="context">context</option>
              <option value="analysis">analysis</option>
              <option value="recommendation">recommendation</option>
              <option value="close">close</option>
            </select>
          </label>
        )}

        <button type="submit" style={buttonStyle} disabled={!canSubmit}>
          {state.status === "submitting" ? "Creating revision..." : "Create revision"}
        </button>
      </form>

      {state.error ? (
        <div role="alert" style={{ marginTop: "0.75rem", color: "#991b1b", background: "#fef2f2", padding: "0.75rem", borderRadius: "0.375rem" }}>
          {state.error}
        </div>
      ) : null}

      {state.lastRevision ? (
        <div style={{ marginTop: "0.75rem", background: "#ecfdf5", color: "#065f46", padding: "0.75rem", borderRadius: "0.375rem" }}>
          Created revision v{state.lastRevision.version_number} ({state.lastRevision.scope}) at{" "}
          {formatDateTime(state.lastRevision.created_at)}. Revised slides:{" "}
          {state.lastRevision.revised_slide_ids.join(", ") || "none"}.
        </div>
      ) : null}
    </section>
  );
}

function parseSlideIndex(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const parsed = Number.parseInt(trimmed, 10);
  return Number.isFinite(parsed) ? parsed : null;
}
